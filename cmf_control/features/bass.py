from cmf_control.bt.session import BTSession
from cmf_control.protocol.constants import CMD_BASS_GET, CMD_BASS_SET

def get_bass(session: BTSession) -> tuple[bool, int]:
    pkt = session.send(CMD_BASS_GET)
    p = pkt.payload
    if len(p) < 2:
        raise ValueError(f"Bass response too short: {p.hex()}")
    return p[0] == 0x01, p[1] // 2

def set_bass(session: BTSession, enable: bool, level: int) -> None:
    session.send_nowait(CMD_BASS_SET, payload=bytes([0x01 if enable else 0x00, level * 2]))
