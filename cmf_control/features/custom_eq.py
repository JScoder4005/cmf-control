"""
3-band custom EQ (bass / mid / treble, ±6 dB).

Takes effect only while listening mode is EQ_CUSTOM (set via features.eq).
Gains are stored on the buds, so they follow the buds across devices.

Wire format ported from BudsLink nothingBudsSocket.js setCustomEq/_parseCustomEq:
  53-byte payload; [1:5] = -(peak |gain|) as float32 LE (pre-gain to avoid clipping);
  band gains as float32 LE at offsets 6 / 19 / 32 in order MID, TREBLE, BASS.
  Remaining bytes are fixed per-band filter params (frequency, Q).
"""
import struct
from cmf_control.bt.session import BTSession
from cmf_control.protocol.constants import CMD_CUSTOM_EQ_GET, CMD_CUSTOM_EQ_SET

GAIN_MIN = -6
GAIN_MAX = 6

_TEMPLATE = bytes([
    0x03, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x75, 0x44,
    0xc3, 0xf5, 0x28, 0x3f, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0xc0, 0x5a, 0x45, 0x00,
    0x00, 0x80, 0x3f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0c, 0x43, 0xcd, 0xcc,
    0x4c, 0x3f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
])
_TOTAL_OFFSET = 1
_BAND_OFFSETS = (6, 19, 32)  # mid, treble, bass
_MIN_RESPONSE_LEN = 45


def _clamp(v: float) -> float:
    return float(min(GAIN_MAX, max(GAIN_MIN, v)))


def build_custom_eq_payload(bass: float, mid: float, treble: float) -> bytes:
    gains = [_clamp(mid), _clamp(treble), _clamp(bass)]
    p = bytearray(_TEMPLATE)
    peak = max(abs(g) for g in gains)
    struct.pack_into("<f", p, _TOTAL_OFFSET, -peak)  # -0.0 when flat, as the app sends
    for off, g in zip(_BAND_OFFSETS, gains):
        struct.pack_into("<f", p, off, g)
    return bytes(p)


def parse_custom_eq_payload(payload: bytes) -> tuple[int, int, int]:
    """Returns (bass, mid, treble) rounded to whole dB."""
    if len(payload) < _MIN_RESPONSE_LEN:
        raise ValueError(f"Custom EQ response too short: {payload.hex()}")
    mid, treble, bass = (round(_clamp(struct.unpack_from("<f", payload, off)[0]))
                         for off in _BAND_OFFSETS)
    return bass, mid, treble


def get_custom_eq(session: BTSession, timeout: float | None = None) -> tuple[int, int, int]:
    pkt = session.send(CMD_CUSTOM_EQ_GET, timeout=timeout)
    return parse_custom_eq_payload(pkt.payload)


def set_custom_eq(session: BTSession, bass: float, mid: float, treble: float) -> None:
    session.send_nowait(CMD_CUSTOM_EQ_SET, payload=build_custom_eq_payload(bass, mid, treble))
