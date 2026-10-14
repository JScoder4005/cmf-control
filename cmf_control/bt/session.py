"""
BTSession: RFCOMM connection to CMF Buds Pro 2 via BlueZ D-Bus profile.

BlueZ profile flow (mirrors BudsLink profileManager.js):
  1. Register a D-Bus object implementing org.bluez.Profile1 interface
  2. Call org.bluez.ProfileManager1.RegisterProfile(path, uuid, options)
  3. Call org.bluez.Device1.ConnectProfile(uuid) on the device
  4. BlueZ calls our Profile1.NewConnection(device_path, fd, properties)
  5. Read/write the RFCOMM fd directly

UUID: aeac4a03-dff5-498f-843a-34487cf133eb (Nothing/CMF control service)
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

# Backward-compat alias
Packet = Message

NOTHING_UUID    = "aeac4a03-dff5-498f-843a-34487cf133eb"
PROFILE_PATH    = "/org/cmfcontrol/profile0"
RECV_TIMEOUT    = 5.0
CONNECT_TIMEOUT = 20.0


class _Profile1(dbus.service.Object if _DBUS_AVAILABLE else object):
    """Minimal BlueZ Profile1 D-Bus object."""

    def __init__(self, bus, path, on_new_connection):
        super().__init__(bus, path)
        self._on_new_connection = on_new_connection

    @dbus.service.method("org.bluez.Profile1",
                         in_signature="oha{sv}", out_signature="")
    def NewConnection(self, device, fd_handle, properties):
        # fd_handle is a dbus.types.UnixFd — extract raw int
        fd = fd_handle.take()
        self._on_new_connection(str(device), fd)

    @dbus.service.method("org.bluez.Profile1",
                         in_signature="o", out_signature="")
    def RequestDisconnection(self, device):
        pass

    @dbus.service.method("org.bluez.Profile1",
                         in_signature="", out_signature="")
    def Release(self):
        pass


class BTSession:
    def __init__(self, address: str):
        self.address = address.upper()
        self._fd: int | None = None
        self._fsn = 0
        self._lock = threading.Lock()
        self._mainloop: GLib.MainLoop | None = None
        self._glib_thread: threading.Thread | None = None
        self._bus: dbus.SystemBus | None = None
        self._profile_obj: _Profile1 | None = None
        self._fd_future: Future | None = None

    # ------------------------------------------------------------------ #
    #  Public sync API                                                     #
    # ------------------------------------------------------------------ #

    def connect(self) -> None:
        if not _DBUS_AVAILABLE:
            raise RuntimeError("dbus-python and PyGObject (gi) required. Install via system packages.")
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self._mainloop = GLib.MainLoop()
        self._bus = dbus.SystemBus()

        self._fd_future = Future()

        def on_new_connection(device_path: str, fd: int):
            if not self._fd_future.done():
                self._fd_future.set_result(fd)

        self._profile_obj = _Profile1(self._bus, PROFILE_PATH, on_new_connection)

        manager = dbus.Interface(
            self._bus.get_object("org.bluez", "/org/bluez"),
            "org.bluez.ProfileManager1",
        )
        manager.RegisterProfile(
            PROFILE_PATH,
            NOTHING_UUID,
            {
                "Name": dbus.String("CMF Control"),
                "Role": dbus.String("client"),
                "AutoConnect": dbus.Boolean(False),
            },
        )

        # Start GLib mainloop in background (needed for D-Bus callbacks)
        self._glib_thread = threading.Thread(
            target=self._mainloop.run, daemon=True
        )
        self._glib_thread.start()

        # Find BlueZ device object path for our MAC
        device_path = self._find_device_path()

        device = dbus.Interface(
            self._bus.get_object("org.bluez", device_path),
            "org.bluez.Device1",
        )
        device.ConnectProfile(NOTHING_UUID)

        # Wait for BlueZ to call NewConnection
        try:
            self._fd = self._fd_future.result(timeout=CONNECT_TIMEOUT)
        except Exception as e:
            raise ConnectionError(f"BlueZ did not open RFCOMM connection: {e}") from e

    def disconnect(self) -> None:
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None
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

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()

    # ------------------------------------------------------------------ #
    #  Internals                                                           #
    # ------------------------------------------------------------------ #

    def _find_device_path(self) -> str:
        obj_manager = dbus.Interface(
            self._bus.get_object("org.bluez", "/"),
            "org.freedesktop.DBus.ObjectManager",
        )
        objects = obj_manager.GetManagedObjects()
        target = self.address.replace(":", "_")
        for path, ifaces in objects.items():
            if "org.bluez.Device1" in ifaces:
                if target in str(path).upper():
                    return str(path)
        raise ConnectionError(
            f"Device {self.address} not found in BlueZ. Pair it first via bluetoothctl."
        )

    def _write(self, data: bytes) -> None:
        view = memoryview(data)
        sent = 0
        while sent < len(data):
            n = os.write(self._fd, bytes(view[sent:]))
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
                raise ConnectionError("RFCOMM socket closed by device")
            buf += chunk
            try:
                msg = Message.decode(buf)
                if msg.command == expected_cmd:
                    return msg
                buf = buf[msg.wire_size:]
            except ValueError:
                continue
        raise TimeoutError(f"No response for cmd={expected_cmd:#x}")
