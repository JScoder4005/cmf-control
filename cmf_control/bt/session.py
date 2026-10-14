import socket
import threading
import time
from cmf_control.protocol.codec import Packet

SPP_UUID = "00001101-0000-1000-8000-00805f9b34fb"
RFCOMM_CHANNEL = 1
RECV_TIMEOUT = 5.0
RECONNECT_DELAY = 3.0

class BTSession:
    def __init__(self, address: str):
        self.address = address
        self._sock: socket.socket | None = None
        self._seq = 0
        self._lock = threading.Lock()

    def connect(self) -> None:
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.settimeout(RECV_TIMEOUT)
        sock.connect((self.address, RFCOMM_CHANNEL))
        self._sock = sock

    def disconnect(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def send(self, cmd: int, payload: bytes = b"") -> Packet:
        with self._lock:
            if not self._sock:
                raise ConnectionError("Not connected")
            seq = self._seq
            self._seq = (self._seq + 1) & 0xFF
            pkt = Packet(cmd=cmd, seq=seq, payload=payload)
            self._sock.sendall(pkt.encode())
            return self._recv_response(seq)

    def _recv_response(self, expected_seq: int) -> Packet:
        buf = b""
        deadline = time.monotonic() + RECV_TIMEOUT
        while time.monotonic() < deadline:
            try:
                chunk = self._sock.recv(256)
            except TimeoutError:
                break
            if not chunk:
                raise ConnectionError("Socket closed by device")
            buf += chunk
            try:
                pkt = Packet.decode(buf)
                if pkt.seq == expected_seq:
                    return pkt
                buf = buf[pkt.wire_size:]
            except ValueError:
                continue
        raise TimeoutError(f"No response for seq={expected_seq}")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()
