import pytest
import struct
from cmf_control.protocol.codec import Message, _crc16
from cmf_control.protocol.constants import (
    SOF, CMD_BATTERY, CMD_NOISE_REDUCTION, MAX_PAYLOAD, CTRL_CRC
)


def test_encode_roundtrip():
    msg = Message(command=CMD_BATTERY, payload=b"")
    decoded = Message.decode(msg.encode())
    assert decoded.command == msg.command
    assert decoded.payload == msg.payload
    assert decoded.is_request


def test_encode_starts_with_sof():
    msg = Message(command=CMD_BATTERY, payload=b"")
    assert msg.encode()[0] == SOF


def test_encode_with_payload_roundtrip():
    payload = bytes([0x01, 0x01, 0x00])
    msg = Message(command=CMD_NOISE_REDUCTION, payload=payload)
    decoded = Message.decode(msg.encode())
    assert decoded.command == CMD_NOISE_REDUCTION
    assert decoded.payload == payload


def test_decode_bad_sof():
    data = Message(command=CMD_BATTERY).encode()
    bad = bytes([0x00]) + data[1:]
    with pytest.raises(ValueError, match="Bad SOF"):
        Message.decode(bad)


def test_decode_crc_mismatch():
    data = bytearray(Message(command=CMD_BATTERY, payload=b"\x01").encode())
    data[-1] ^= 0xFF
    with pytest.raises(ValueError, match="CRC mismatch"):
        Message.decode(bytes(data))


def test_decode_too_short():
    with pytest.raises(ValueError, match="too short"):
        Message.decode(bytes([SOF, 0x20, 0x00]))


def test_empty_payload():
    msg = Message(command=CMD_BATTERY, payload=b"")
    assert Message.decode(msg.encode()).payload == b""


def test_decode_truncated_payload():
    # claim 5 bytes payload but provide only 2
    header = struct.pack("<BHHHB", SOF, CTRL_CRC, CMD_BATTERY, 5, 0)
    with pytest.raises(ValueError, match="truncated"):
        Message.decode(header + bytes([0x01, 0x02]))


def test_encode_payload_too_large():
    with pytest.raises(ValueError, match="too large"):
        Message(command=CMD_BATTERY, payload=bytes(MAX_PAYLOAD + 1)).encode()


def test_crc16_known_value():
    # CRC-16/ARC of empty bytes: 0xFFFF
    assert _crc16(b"") == 0xFFFF


def test_wire_size():
    msg = Message(command=CMD_BATTERY, payload=b"\x01\x02", crc=True)
    assert len(msg.encode()) == msg.wire_size
    msg_nocrc = Message(command=CMD_BATTERY, payload=b"\x01\x02", crc=False)
    assert len(msg_nocrc.encode()) == msg_nocrc.wire_size
