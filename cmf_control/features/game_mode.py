from cmf_control.bt.session import BTSession
from cmf_control.protocol.constants import CMD_LATENCY_GET, CMD_LATENCY_SET

def get_game_mode(session: BTSession) -> bool:
    pkt = session.send(CMD_LATENCY_GET)
    p = pkt.payload
    if len(p) < 1:
        raise ValueError(f"Game mode response too short: {p.hex()}")
    return p[0] == 0x01

def set_game_mode(session: BTSession, enable: bool) -> None:
    session.send_nowait(CMD_LATENCY_SET, payload=bytes([0x01 if enable else 0x02, 0x00]))
