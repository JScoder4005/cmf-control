"""
BTSession: RFCOMM connection to CMF Buds Pro 2 via BlueZ D-Bus profile.

BlueZ profile flow (mirrors BudsLink):
  1. Register Profile1 D-Bus object
  2. Call org.bluez.ProfileManager1.RegisterProfile
  3. Call org.bluez.Device1.ConnectProfile(uuid)
  4. BlueZ calls NewConnection(device, fd, props) with RFCOMM fd
  5. Read/write fd directly

Requires system Python with dbus-python + PyGObject (gi).
Run with: /usr/bin/python3

UUID: aeac4a03-dff5-498f-843a-34487cf133eb
"""
import os
import select
import threading
import time
from concurrent.futures import Future

try:
    import dbus
    import dbus.service
    import dbus.mainloop.glib
    from gi.repository import GLib
    _DBUS_AVAILABLE = True
except ImportError:
    _DBUS_AVAILABLE = False

from cmf_control.protocol.codec import Message

Packet = Message  # backward-compat

NOTHING_UUID    = "aeac4a03-dff5-498f-843a-34487cf133eb"
CLASSIC_MAC     = "2C:BE:EE:F0:00:3C"
PROFILE_PATH    = "/org/cmfcontrol/profile0"
RECV_TIMEOUT    = 5.0
CONNECT_TIMEOUT = 20.0


def _make_profile_class():
    if not _DBUS_AVAILABLE:
        class _Stub:
            def __init__(self, bus, path, on_new_connection):
                self._on_new_connection = on_new_connection
        return _Stub

    class _Profile1(dbus.service.Object):
        def __init__(self, bus, path, on_new_connection):
            super().__init__(bus, path)
            self._on_new_connection = on_new_connection

        @dbus.service.method("org.bluez.Profile1", in_signature="oha{sv}", out_signature="")
        def NewConnection(self, device, fd_handle, properties):
            self._on_new_connection(str(device), fd_handle.take())

        @dbus.service.method("org.bluez.Profile1", in_signature="o", out_signature="")
        def RequestDisconnection(self, device): pass

        @dbus.service.method("org.bluez.Profile1", in_signature="", out_signature="")
        def Release(self): pass

    return _Profile1

_Profile1 = _make_profile_class()


class BTSession:
    def __init__(self, address: str = CLASSIC_MAC):
        self.address = address.upper()
        self._fd: int | None = None
        self._fsn = 0
        self._lock = threading.Lock()
        self._mainloop = None
        self._glib_thread = None
        self._bus = None
        self._profile_obj = None
        self._fd_future: Future | None = None

    def connect(self) -> None:
        if not _DBUS_AVAILABLE:
            raise RuntimeError(
                "dbus-python + PyGObject required.\n"
                "Run with: /usr/bin/python3"
            )
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self._mainloop = GLib.MainLoop()
        self._bus = dbus.SystemBus()
        self._fd_future = Future()

        self._profile_obj = _Profile1(
            self._bus, PROFILE_PATH,
            lambda dev, fd: self._fd_future.set_result(fd)
              if not self._fd_future.done() else None
        )

        self._mgr = dbus.Interface(
            self._bus.get_object("org.bluez", "/org/bluez"),
            "org.bluez.ProfileManager1",
        )
        try:
            self._mgr.UnregisterProfile(PROFILE_PATH)
        except Exception:
            pass
        try:
            self._mgr.RegisterProfile(PROFILE_PATH, NOTHING_UUID, {
                "Name": dbus.String("CMF Control"),
                "Role": dbus.String("client"),
                "AutoConnect": dbus.Boolean(False),
            })
        except dbus.exceptions.DBusException as e:
            if "NotPermitted" in str(e) or "UUID already registered" in str(e):
                # Stale registration from crashed process — restart bluetoothd and retry
                import subprocess
                subprocess.run(["sudo", "systemctl", "restart", "bluetooth"], check=True)
                time.sleep(2)
                self._bus = dbus.SystemBus()
                self._mgr = dbus.Interface(
                    self._bus.get_object("org.bluez", "/org/bluez"),
                    "org.bluez.ProfileManager1",
                )
                self._mgr.RegisterProfile(PROFILE_PATH, NOTHING_UUID, {
                    "Name": dbus.String("CMF Control"),
                    "Role": dbus.String("client"),
                    "AutoConnect": dbus.Boolean(False),
                })
            else:
                raise

        self._glib_thread = threading.Thread(target=self._mainloop.run, daemon=True)
        self._glib_thread.start()

        device_path = self._find_device_path()
        device = dbus.Interface(
            self._bus.get_object("org.bluez", device_path),
            "org.bluez.Device1",
        )
        try:
            device.ConnectProfile(NOTHING_UUID)
        except Exception:
            pass  # BlueZ calls NewConnection before returning — timeout is harmless

        self._fd = self._fd_future.result(timeout=CONNECT_TIMEOUT)

    def disconnect(self) -> None:
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None
        if hasattr(self, '_mgr') and self._mgr:
            try:
                self._mgr.UnregisterProfile(PROFILE_PATH)
            except Exception:
                pass
        if self._mainloop and self._mainloop.is_running():
            self._mainloop.quit()

    def send(self, cmd: int, payload: bytes = b"") -> Message:
        with self._lock:
            if self._fd is None:
                raise ConnectionError("Not connected")
            fsn = self._fsn
            self._fsn = (self._fsn + 1) & 0xFF
            msg = Message(command=cmd, payload=payload, fsn=fsn)
            self._write(msg.encode())
            return self._recv_response(cmd)

    def send_nowait(self, cmd: int, payload: bytes = b"") -> None:
        with self._lock:
            if self._fd is None:
                raise ConnectionError("Not connected")
            fsn = self._fsn
            self._fsn = (self._fsn + 1) & 0xFF
            msg = Message(command=cmd, payload=payload, fsn=fsn)
            self._write(msg.encode())

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()

    def _find_device_path(self) -> str:
        om = dbus.Interface(
            self._bus.get_object("org.bluez", "/"),
            "org.freedesktop.DBus.ObjectManager",
        )
        target = self.address.replace(":", "_")
        for path, ifaces in om.GetManagedObjects().items():
            if "org.bluez.Device1" in ifaces and target in str(path).upper():
                return str(path)
        raise ConnectionError(
            f"Device {self.address} not found in BlueZ. Pair it first via bluetoothctl."
        )

    def _write(self, data: bytes) -> None:
        sent = 0
        while sent < len(data):
            n = os.write(self._fd, data[sent:])
            if n <= 0:
                raise ConnectionError("RFCOMM write failed")
            sent += n

    def _recv_response(self, expected_cmd: int) -> Message:
        buf = b""
        deadline = time.monotonic() + RECV_TIMEOUT
        while time.monotonic() < deadline:
            remaining = max(0.0, deadline - time.monotonic())
            ready, _, _ = select.select([self._fd], [], [], remaining)
            if not ready:
                break
            chunk = os.read(self._fd, 512)
            if not chunk:
                raise ConnectionError("RFCOMM closed by device")
            buf += chunk
            try:
                msg = Message.decode(buf)
                # Response cmd has bit 15 cleared vs request
                if (msg.command & 0x7FFF) == (expected_cmd & 0x7FFF):
                    return msg
                buf = buf[msg.wire_size:]
            except ValueError:
                continue
        raise TimeoutError(f"No response for cmd={expected_cmd:#x}")
