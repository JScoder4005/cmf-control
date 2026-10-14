"""
BTSession: RFCOMM connection to CMF Buds Pro 2 using service UUID AEAC4A03.

Connection flow:
  1. sdptool browse to find RFCOMM channel for AEAC4A03 UUID
  2. Connect via raw AF_BLUETOOTH/RFCOMM socket (ctypes, AF_BLUETOOTH=31)
  3. Send/receive Nothing protocol Messages
"""
import ctypes
import ctypes.util
import re
import select
import subprocess
import threading
import time

from cmf_control.protocol.codec import Message
from cmf_control.protocol.constants import SERVICE_UUID

# Backward-compat alias
Packet = Message

# AF_BLUETOOTH = 31, BTPROTO_RFCOMM = 3 (kernel constants, not Python build flags)
AF_BLUETOOTH  = 31
BTPROTO_RFCOMM = 3
SOCK_STREAM   = 1

RECV_TIMEOUT  = 5.0

_libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)


class _SockaddrRfcomm(ctypes.Structure):
    _fields_ = [
        ("sa_family", ctypes.c_ushort),
        ("btaddr",    ctypes.c_uint8 * 6),
        ("channel",   ctypes.c_uint8),
        ("_pad",      ctypes.c_uint8),
    ]


def _str_to_btaddr(addr: str) -> ctypes.Array:
    parts = [int(x, 16) for x in addr.split(":")]
    parts.reverse()  # BlueZ stores address in reverse byte order
    return (ctypes.c_uint8 * 6)(*parts)


def find_rfcomm_channel(address: str, uuid: str = SERVICE_UUID) -> int:
    """Query SDP for the RFCOMM channel advertising the given UUID."""
    try:
        out = subprocess.check_output(
            ["sdptool", "browse", "--uuid", uuid, address],
            stderr=subprocess.DEVNULL,
            timeout=10,
        ).decode(errors="replace")
        m = re.search(r"Channel:\s*(\d+)", out)
        if m:
            return int(m.group(1))
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    # Fallback: scan all records for RFCOMM channel associated with UUID
    try:
        out = subprocess.check_output(
            ["sdptool", "browse", address],
            stderr=subprocess.DEVNULL,
            timeout=10,
        ).decode(errors="replace")
        # Find the record block containing our UUID, then the nearest Channel:
        uuid_short = uuid[:8].upper()
        idx = out.upper().find(uuid_short)
        if idx != -1:
            m = re.search(r"Channel:\s*(\d+)", out[idx:])
            if m:
                return int(m.group(1))
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    raise ConnectionError(
        f"Could not find RFCOMM channel for UUID {uuid} on {address}. "
        "Ensure device is paired and in range."
    )


class BTSession:
    def __init__(self, address: str, channel: int | None = None):
        self.address = address
        self._channel = channel  # if None, SDP lookup on connect
        self._fd: int | None = None
        self._lock = threading.Lock()
        self._fsn = 0

    def connect(self) -> None:
        if self._channel is None:
            self._channel = find_rfcomm_channel(self.address)
        fd = _libc.socket(AF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM)
        if fd < 0:
            raise OSError(ctypes.get_errno(), "socket() failed")
        sa = _SockaddrRfcomm()
        sa.sa_family = AF_BLUETOOTH
        sa.btaddr = _str_to_btaddr(self.address)
        sa.channel = self._channel
        ret = _libc.connect(fd, ctypes.byref(sa), ctypes.sizeof(sa))
        if ret < 0:
            err = ctypes.get_errno()
            _libc.close(fd)
            raise OSError(err, f"RFCOMM connect to {self.address} ch={self._channel} failed")
        self._fd = fd

    def disconnect(self) -> None:
        if self._fd is not None:
            try:
                _libc.close(self._fd)
            except Exception:
                pass
            self._fd = None

    def send(self, cmd: int, payload: bytes = b"") -> Message:
        with self._lock:
            if self._fd is None:
                raise ConnectionError("Not connected")
            fsn = self._fsn
            self._fsn = (self._fsn + 1) & 0xFF
            msg = Message(command=cmd, payload=payload, fsn=fsn)
            self._write(msg.encode())
            return self._recv_response(cmd)

    def _write(self, data: bytes) -> None:
        view = memoryview(data)
        sent = 0
        while sent < len(data):
            n = _libc.write(self._fd, ctypes.c_char_p(bytes(view[sent:])), len(data) - sent)
            if n < 0:
                raise OSError(ctypes.get_errno(), "write failed")
            sent += n

    def _recv_response(self, expected_cmd: int) -> Message:
        buf = b""
        deadline = time.monotonic() + RECV_TIMEOUT
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            ready, _, _ = select.select([self._fd], [], [], max(0, remaining))
            if not ready:
                break
            raw = ctypes.create_string_buffer(512)
            n = _libc.read(self._fd, raw, 512)
            if n < 0:
                raise OSError(ctypes.get_errno(), "read failed")
            if n == 0:
                raise ConnectionError("Socket closed by device")
            buf += raw.raw[:n]
            try:
                msg = Message.decode(buf)
                if msg.command == expected_cmd:
                    return msg
                buf = buf[msg.wire_size:]
            except ValueError:
                continue
        raise TimeoutError(f"No response for cmd={expected_cmd:#x}")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()
