from cmf_control.bt.session import BTSession
from cmf_control.protocol.constants import CMD_SPATIAL_GET, CMD_SPATIAL_SET

def get_spatial(session: BTSession) -> bool:
    pkt = session.send(CMD_SPATIAL_GET)
    p = pkt.payload
    if len(p) < 1:
        raise ValueError(f"Spatial audio response too short: {p.hex()}")
    return p[0] == 0x01

def set_spatial(session: BTSession, enable: bool) -> None:
    session.send_nowait(CMD_SPATIAL_SET, payload=bytes([0x01 if enable else 0x00]))
