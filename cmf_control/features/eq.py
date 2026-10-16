from cmf_control.bt.session import BTSession
from cmf_control.protocol.constants import CMD_GET_EQ, CMD_SET_EQ

EQ_PRESETS = {
    0x00: "Balanced",
    0x01: "Rock",
    0x02: "Electronic",
    0x03: "Pop",
    0x04: "Enhance Vocals",
    0x05: "Classical",
}

def get_eq(session: BTSession) -> int:
    pkt = session.send(CMD_GET_EQ)
    if len(pkt.payload) < 1:
        raise ValueError("Empty EQ response")
    return pkt.payload[0]

def set_eq(session: BTSession, preset: int) -> None:
    if preset not in EQ_PRESETS:
        raise ValueError(f"Unknown EQ preset: {preset:#x}")
    session.send_nowait(CMD_SET_EQ, payload=bytes([preset, 0x00]))
