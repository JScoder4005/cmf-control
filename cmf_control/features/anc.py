from cmf_control.bt.session import BTSession
from cmf_control.protocol.constants import (
    CMD_GET_ANC, CMD_SET_ANC,
    ANC_OFF, ANC_TRANSPARENCY, ANC_LIGHT, ANC_MAX,
)

ANC_MODES = {
    ANC_OFF: "Off",
    ANC_TRANSPARENCY: "Transparency",
    ANC_LIGHT: "Light ANC",
    ANC_MAX: "Max ANC",
}

def get_anc(session: BTSession) -> int:
    pkt = session.send(CMD_GET_ANC)
    if len(pkt.payload) < 1:
        raise ValueError("Empty ANC response")
    return pkt.payload[0]

def set_anc(session: BTSession, mode: int) -> None:
    if mode not in ANC_MODES:
        raise ValueError(f"Unknown ANC mode: {mode:#x}")
    session.send(CMD_SET_ANC, payload=bytes([mode]))
