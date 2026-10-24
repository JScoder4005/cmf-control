import struct
from unittest.mock import patch
import pytest
from cmf_control.features.custom_eq import (
    build_custom_eq_payload, parse_custom_eq_payload,
    get_custom_eq, set_custom_eq, GAIN_MIN, GAIN_MAX,
)
from cmf_control.features.eq import EQ_PRESETS
from cmf_control.protocol.codec import Packet
from cmf_control.protocol.constants import (
    CMD_CUSTOM_EQ_GET, CMD_CUSTOM_EQ_SET, EQ_CUSTOM,
)

# Template captured from BudsLink nothingBudsSocket.js setCustomEq() with all gains at 0.
FLAT_PAYLOAD = bytes([
    0x03, 0x00, 0x00, 0x00, 0x80, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x75, 0x44,
    0xc3, 0xf5, 0x28, 0x3f, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0xc0, 0x5a, 0x45, 0x00,
    0x00, 0x80, 0x3f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0c, 0x43, 0xcd, 0xcc,
    0x4c, 0x3f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
])

def _f(b: bytes, off: int) -> float:
    return struct.unpack_from("<f", b, off)[0]


def test_custom_is_a_preset():
    assert EQ_CUSTOM == 0x06
    assert EQ_PRESETS[EQ_CUSTOM] == "Custom"

def test_flat_payload_matches_budslink():
    assert build_custom_eq_payload(0, 0, 0) == FLAT_PAYLOAD

def test_payload_band_order_is_mid_treble_bass():
    p = build_custom_eq_payload(bass=4, mid=-2, treble=1)
    assert len(p) == 53
    assert _f(p, 6) == -2.0    # mid
    assert _f(p, 19) == 1.0    # treble
    assert _f(p, 32) == 4.0    # bass

def test_payload_total_is_negative_peak_gain():
    p = build_custom_eq_payload(bass=-5, mid=3, treble=0)
    assert _f(p, 1) == -5.0

def test_payload_clamps_out_of_range():
    p = build_custom_eq_payload(bass=99, mid=-99, treble=0)
    assert _f(p, 32) == GAIN_MAX
    assert _f(p, 6) == GAIN_MIN

def test_parse_roundtrip():
    p = build_custom_eq_payload(bass=6, mid=-3, treble=2)
    assert parse_custom_eq_payload(p) == (6, -3, 2)

def test_parse_short_payload_raises():
    with pytest.raises(ValueError):
        parse_custom_eq_payload(b"\x03" * 10)

def test_get_custom_eq(mock_session):
    resp = Packet(cmd=0x4044, seq=0, payload=build_custom_eq_payload(1, 2, 3))
    with patch.object(mock_session, "send", return_value=resp) as send:
        assert get_custom_eq(mock_session) == (1, 2, 3)
        send.assert_called_once_with(CMD_CUSTOM_EQ_GET, timeout=None)

def test_set_custom_eq(mock_session):
    with patch.object(mock_session, "send_nowait") as send:
        set_custom_eq(mock_session, bass=2, mid=0, treble=-1)
        send.assert_called_once_with(
            CMD_CUSTOM_EQ_SET, payload=build_custom_eq_payload(2, 0, -1))
