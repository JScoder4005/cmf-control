from cmf_control.bt.session import BTSession
from cmf_control.protocol.constants import (
    CMD_GET_EQ, CMD_SET_EQ,
    EQ_BALANCED, EQ_BASS_BOOST, EQ_TREBLE_BOOST, EQ_PODCAST, EQ_GAMING,
)

EQ_PRESETS = {
    EQ_BALANCED:     "Balanced",
    EQ_BASS_BOOST:   "Bass Boost",
    EQ_TREBLE_BOOST: "Treble Boost",
    EQ_PODCAST:      "Podcast",
    EQ_GAMING:       "Gaming",
}

def get_eq(session: BTSession) -> int:
    pkt = session.send(CMD_GET_EQ)
    if len(pkt.payload) < 1:
        raise ValueError("Empty EQ response")
    return pkt.payload[0]

def set_eq(session: BTSession, preset: int) -> None:
    if preset not in EQ_PRESETS:
        raise ValueError(f"Unknown EQ preset: {preset:#x}")
    session.send(CMD_SET_EQ, payload=bytes([preset]))
