from dataclasses import dataclass
from cmf_control.protocol.constants import MAGIC, MAX_PAYLOAD

@dataclass
class Packet:
    cmd: int
    seq: int
    payload: bytes

    def encode(self) -> bytes:
        length = len(self.payload).to_bytes(2, "big")
        body = bytes([self.cmd, self.seq]) + length + self.payload
        checksum = _checksum(body)
        return MAGIC + body + bytes([checksum])

    @staticmethod
    def decode(data: bytes) -> "Packet":
        if len(data) < 7:
            raise ValueError(f"Packet too short: {len(data)} bytes")
        if data[:2] != MAGIC:
            raise ValueError(f"Bad magic: {data[:2].hex()}")
        cmd = data[2]
        seq = data[3]
        payload_len = int.from_bytes(data[4:6], "big")
        if len(data) < 6 + payload_len + 1:
            raise ValueError("Packet truncated")
        payload = data[6:6 + payload_len]
        checksum = data[6 + payload_len]
        body = data[2:6 + payload_len]
        if checksum != _checksum(body):
            raise ValueError(f"Checksum mismatch: got {checksum:#x}")
        return Packet(cmd=cmd, seq=seq, payload=payload)

def _checksum(data: bytes) -> int:
    return sum(data) & 0xFF
