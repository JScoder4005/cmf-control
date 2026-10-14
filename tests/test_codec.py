import pytest
from cmf_control.protocol.codec import Packet, _checksum
from cmf_control.protocol.constants import MAGIC, CMD_GET_BATTERY

def test_encode_roundtrip():
    pkt = Packet(cmd=CMD_GET_BATTERY, seq=1, payload=bytes([0x01]))
    encoded = pkt.encode()
    decoded = Packet.decode(encoded)
    assert decoded.cmd == pkt.cmd
    assert decoded.seq == pkt.seq
    assert decoded.payload == pkt.payload

def test_encode_starts_with_magic():
    pkt = Packet(cmd=CMD_GET_BATTERY, seq=0, payload=b"")
    assert pkt.encode()[:2] == MAGIC

def test_decode_bad_magic():
    pkt = Packet(cmd=CMD_GET_BATTERY, seq=0, payload=b"").encode()
    bad = b"\x00\x00" + pkt[2:]
    with pytest.raises(ValueError, match="Bad magic"):
        Packet.decode(bad)

def test_decode_bad_checksum():
    pkt = Packet(cmd=CMD_GET_BATTERY, seq=0, payload=b"\x01").encode()
    corrupted = pkt[:-1] + bytes([pkt[-1] ^ 0xFF])
    with pytest.raises(ValueError, match="Checksum mismatch"):
        Packet.decode(corrupted)

def test_decode_too_short():
    with pytest.raises(ValueError, match="too short"):
        Packet.decode(b"\xAA\xBB\x05")

def test_empty_payload():
    pkt = Packet(cmd=0x05, seq=0, payload=b"")
    assert Packet.decode(pkt.encode()).payload == b""
