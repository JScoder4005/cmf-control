from cmf_control.bt.session import BTSession
from cmf_control.protocol.constants import (
    CMD_GET_ANC, CMD_SET_ANC,
    ANC_VAL_OFF, ANC_VAL_PASS_THROUGH, ANC_VAL_STRONG, ANC_VAL_MEDIUM, ANC_VAL_WEAK,
)

ANC_MODES = {
    ANC_VAL_OFF:          "Off",
    ANC_VAL_PASS_THROUGH: "Transparency",
    ANC_VAL_WEAK:         "Light ANC",
    ANC_VAL_MEDIUM:       "Medium ANC",
    ANC_VAL_STRONG:       "Max ANC",
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
    # Device doesn't reliably respond to SET — fire and forget
    session.send_nowait(CMD_SET_ANC, payload=bytes([1, mode, 0]))
