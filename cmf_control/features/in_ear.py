from cmf_control.bt.session import BTSession
from cmf_control.protocol.constants import CMD_IN_EAR_GET, CMD_IN_EAR_SET

def get_in_ear(session: BTSession, timeout: float | None = None) -> bool:
    pkt = session.send(CMD_IN_EAR_GET, timeout=timeout)
    p = pkt.payload
    if len(p) < 3:
        raise ValueError(f"In-ear response too short: {p.hex()}")
    return p[2] == 0x01

def set_in_ear(session: BTSession, enable: bool) -> None:
    session.send_nowait(CMD_IN_EAR_SET, payload=bytes([0x01, 0x01, 0x01 if enable else 0x00]))
