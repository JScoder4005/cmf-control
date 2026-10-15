"""
Packet codec matching Nothing SmartCenter Message.java wire format.

Wire layout (all little-endian ints per q3.q helpers):
  [0]     SOF      = 0x55
  [1:3]   control  = 2 bytes  (bits: 0-4=rspCode, 5=crc, 6=multiframe, 8-11=deviceType)
  [3:5]   command  = 2 bytes
  [5:7]   length   = 2 bytes  (payload byte count)
  [7]     fsn      = 1 byte   (frame sequence number)
  [8:8+n] payload  = n bytes
  [8+n:8+n+2] crc  = 2 bytes  (CRC-16/ARC, poly=0xA001, init=0xFFFF) if ctrl bit 5 set
"""
import struct
from dataclasses import dataclass, field
from cmf_control.protocol.constants import SOF, MAX_PAYLOAD, CTRL_CRC, CTRL_MULTIFRAME, DEVICE_TYPE_CORSOLA


@dataclass
class Message:
    command: int
    payload: bytes = field(default_factory=bytes)
    device_type: int = DEVICE_TYPE_CORSOLA
    fsn: int = 0
    crc: bool = True
    # response code (0 = request / success, non-zero = error)
    rsp_code: int = 0

    @property
    def is_request(self) -> bool:
        return self.rsp_code == 0

    @property
    def wire_size(self) -> int:
        base = 8 + len(self.payload)
        return base + (2 if self.crc else 0)

    def encode(self) -> bytes:
        if len(self.payload) > MAX_PAYLOAD:
            raise ValueError(f"Payload too large: {len(self.payload)}")
        ctrl = self.rsp_code & 0x1F
        if self.crc:
            ctrl |= CTRL_CRC
        ctrl |= CTRL_MULTIFRAME  # BudsLink always sets this (0x60 ctrl_lo)
        ctrl |= (self.device_type & 0xF) << 8
        header = struct.pack(
            "<BHHHB",
            SOF,
            ctrl,
            self.command & 0xFFFF,
            len(self.payload) & 0xFFFF,
            self.fsn & 0xFF,
        )
        body = header + self.payload
        if self.crc:
            body += struct.pack("<H", _crc16(body))
        return body

    @staticmethod
    def decode(data: bytes) -> "Message":
        if len(data) < 8:
            raise ValueError(f"Packet too short: {len(data)} bytes")
        if data[0] != SOF:
            raise ValueError(f"Bad SOF: {data[0]:#x}")
        ctrl, cmd, length, fsn = struct.unpack_from("<HHHB", data, 1)
        if length > MAX_PAYLOAD:
            raise ValueError(f"Payload too large: {length}")
        end = 8 + length
        if len(data) < end:
            raise ValueError("Packet truncated")
        payload = data[8:end]
        has_crc = bool(ctrl & CTRL_CRC)
        if has_crc:
            if len(data) < end + 2:
                raise ValueError("CRC bytes missing")
            # CRC present but not validated — device uses variant we haven't pinned yet
        rsp_code = ctrl & 0x1F
        device_type = (ctrl >> 8) & 0xF
        return Message(
            command=cmd,
            payload=payload,
            device_type=device_type,
            fsn=fsn,
            crc=has_crc,
            rsp_code=rsp_code,
        )


def Packet(cmd: int = 0, seq: int = 0, payload: bytes = b"", **kwargs) -> "Message":
    """Backward-compat shim: Packet(cmd, seq, payload) → Message(command, fsn, payload)."""
    return Message(command=cmd, fsn=seq, payload=payload, **kwargs)


def _crc16(data: bytes) -> int:
    """CRC-16/ARC (poly=0xA001, init=0xFFFF) — verified from Message.java q() method."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte & 0xFF
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF
