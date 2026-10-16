"""
BTSession: RFCOMM connection to CMF Buds Pro 2 via macOS IOBluetooth.

Mirrors the public interface of bt/session.py (BlueZ/D-Bus version) so
features/* and ui/* need zero changes on mac.

Flow:
  1. Look up IOBluetoothDevice by address.
  2. If not paired, run IOBluetoothDevicePair to trigger OS pairing.
     Auto-accepts SSP numeric confirmation (CMF buds have no
     display/keypad, so confirmation rather than a typed PIN is expected).
  3. SDP query for NOTHING_UUID to find the RFCOMM channel ID.
  4. Open the RFCOMM channel async; read/write via its delegate.

UNVERIFIED against real hardware (only checked against IOBluetooth
headers/docs, not run against the actual buds): the SDP channel-ID
lookup, and whether pairing actually goes through SSP confirmation vs.
some other path. Start debugging here if connect() fails.

Requires: pip install pyobjc-framework-IOBluetooth
"""
import threading
import time
from concurrent.futures import Future

try:
    import objc
    from Foundation import NSObject, NSRunLoop, NSDate
    from IOBluetooth import (
        IOBluetoothDevice,
        IOBluetoothDevicePair,
        IOBluetoothSDPUUID,
    )
    _IOBT_AVAILABLE = True
except ImportError:
    _IOBT_AVAILABLE = False

from cmf_control.protocol.codec import Message
from cmf_control.bt.session import NOTHING_UUID, CLASSIC_MAC, RECV_TIMEOUT, CONNECT_TIMEOUT

Packet = Message  # backward-compat


def _make_delegate_class():
    if not _IOBT_AVAILABLE:
        class _Stub:
            def __init__(self, *a, **k):
                pass
        return _Stub

    class _SessionDelegate(NSObject):
        def initWithSession_(self, session):
            self = objc.super(_SessionDelegate, self).init()
            self._session = session
            return self

        # --- pairing ---
        def devicePairingStarted_(self, sender):
            pass

        def devicePairingConnecting_(self, sender):
            pass

        def devicePairingPINCodeRequest_(self, sender):
            pass  # legacy PIN path — not expected to be hit (buds use SSP)

        def devicePairingUserConfirmationRequest_numericValue_(self, sender, numericValue):
            sender.replyUserConfirmation_(True)

        def devicePairingUserPasskeyNotification_passkey_(self, sender, passkey):
            pass

        def devicePairingFinished_error_(self, sender, error):
            fut = self._session._pair_future
            if fut and not fut.done():
                if error == 0:
                    fut.set_result(None)
                else:
                    fut.set_exception(ConnectionError(f"Pairing failed: status={error}"))

        # --- SDP ---
        def sdpQueryComplete_status_(self, device, status):
            fut = self._session._sdp_future
            if fut and not fut.done():
                if status == 0:
                    fut.set_result(None)
                else:
                    fut.set_exception(ConnectionError(f"SDP query failed: status={status}"))

        # --- RFCOMM channel ---
        def rfcommChannelOpenComplete_status_(self, channel, status):
            fut = self._session._channel_future
            if fut and not fut.done():
                if status == 0:
                    fut.set_result(channel)
                else:
                    fut.set_exception(ConnectionError(f"RFCOMM open failed: status={status}"))

        def rfcommChannelData_data_length_(self, channel, data, length):
            chunk = bytes(data[:int(length)])
            self._session._rx_buf += chunk

        def rfcommChannelClosed_(self, channel):
            self._session._channel = None

    return _SessionDelegate


_SessionDelegate = _make_delegate_class()


class BTSession:
    def __init__(self, address: str = CLASSIC_MAC):
        self.address = address.upper()
        self._device = None
        self._channel = None
        self._delegate = None
        self._fsn = 0
        self._lock = threading.Lock()

        self._pair_future: Future | None = None
        self._sdp_future: Future | None = None
        self._channel_future: Future | None = None

        self._rx_buf = b""

    def connect(self) -> None:
        # Must be called from the process's main thread: IOBluetooth only
        # delivers async delegate callbacks (pairing, SDP, RFCOMM) to the
        # main thread's run loop, never to a spawned threading.Thread's —
        # confirmed by direct test, not documented anywhere official.
        if not _IOBT_AVAILABLE:
            raise RuntimeError(
                "pyobjc-framework-IOBluetooth required.\n"
                "Run: pip install pyobjc-framework-IOBluetooth"
            )
        self._delegate = _SessionDelegate.alloc().initWithSession_(self)
        self._device = IOBluetoothDevice.deviceWithAddressString_(self.address)
        if self._device is None:
            raise ConnectionError(f"Device {self.address} not found by IOBluetooth")

        if not self._device.isPaired():
            self._pair_future = Future()
            pairer = IOBluetoothDevicePair.pairWithDevice_(self._device)
            pairer.setDelegate_(self._delegate)
            pairer.start()
            self._spin_until(self._pair_future, CONNECT_TIMEOUT)

        self._sdp_future = Future()
        self._device.performSDPQuery_(self._delegate)
        self._spin_until(self._sdp_future, CONNECT_TIMEOUT)

        uuid = IOBluetoothSDPUUID.uuidWithBytes_length_(
            bytes.fromhex(NOTHING_UUID.replace("-", "")), 16
        )
        record = self._device.getServiceRecordForUUID_(uuid)
        if record is None:
            raise ConnectionError(f"No SDP record for UUID {NOTHING_UUID} on {self.address}")
        status, channel_id = record.getRFCOMMChannelID_(None)
        if status != 0:
            raise ConnectionError(f"No RFCOMM channel for UUID {NOTHING_UUID}")

        self._channel_future = Future()
        status, _ = self._device.openRFCOMMChannelAsync_withChannelID_delegate_(
            None, channel_id, self._delegate
        )
        if status != 0:
            raise ConnectionError(f"openRFCOMMChannelAsync failed: status={status}")
        self._channel = self._spin_until(self._channel_future, CONNECT_TIMEOUT)

    def _spin_until(self, future: Future, timeout: float):
        rl = NSRunLoop.currentRunLoop()
        deadline = time.monotonic() + timeout
        while not future.done():
            if time.monotonic() > deadline:
                raise TimeoutError("Timed out waiting for IOBluetooth callback")
            rl.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.05))
        return future.result()

    def disconnect(self) -> None:
        if self._channel is not None:
            try:
                self._channel.closeChannel()
            except Exception:
                pass
            self._channel = None

    def send(self, cmd: int, payload: bytes = b"") -> Message:
        with self._lock:
            if self._channel is None:
                raise ConnectionError("Not connected")
            fsn = self._fsn
            self._fsn = (self._fsn + 1) & 0xFF
            msg = Message(command=cmd, payload=payload, fsn=fsn)
            self._write(msg.encode())
            return self._recv_response(cmd)

    def send_nowait(self, cmd: int, payload: bytes = b"") -> None:
        with self._lock:
            if self._channel is None:
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

    def _write(self, data: bytes) -> None:
        status = self._channel.writeSync_length_(data, len(data))
        if status != 0:
            raise ConnectionError(f"RFCOMM write failed: status={status}")

    def _recv_response(self, expected_cmd: int) -> Message:
        # Must spin this thread's run loop (not just block) so the
        # rfcommChannelData_data_length_ delegate callback gets a chance to
        # fire and append to _rx_buf — same main-thread constraint as connect().
        rl = NSRunLoop.currentRunLoop()
        deadline = time.monotonic() + RECV_TIMEOUT
        while True:
            try:
                msg = Message.decode(self._rx_buf)
                self._rx_buf = self._rx_buf[msg.wire_size:]
                # Response cmd has bit 15 cleared vs request
                if (msg.command & 0x7FFF) == (expected_cmd & 0x7FFF):
                    return msg
                continue
            except ValueError:
                pass
            if time.monotonic() > deadline:
                raise TimeoutError(f"No response for cmd={expected_cmd:#x}")
            rl.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.05))
