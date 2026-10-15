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
    p = pkt.payload
    # Payload: 3-byte tuples (type, value, padding); type=1 = mode
    i = 0
    while i + 2 < len(p):
        t, v = p[i], p[i + 1]
        if t == 1:  # NOISE_REDUCTION_MODE
            return v
        i += 3
    if len(p) >= 1:
        return p[0]
    raise ValueError("Empty ANC response")

def set_anc(session: BTSession, mode: int) -> None:
    # Payload: single 3-byte tuple (NOISE_REDUCTION_MODE=1, value, 0)
    session.send(CMD_SET_ANC, payload=bytes([1, mode, 0]))
