from dataclasses import dataclass
from cmf_control.bt.session import BTSession
from cmf_control.protocol.constants import CMD_GET_BATTERY

@dataclass
class BatteryStatus:
    left: int    # 0-100
    right: int   # 0-100
    case: int    # 0-100

def get_battery(session: BTSession) -> BatteryStatus:
    pkt = session.send(CMD_GET_BATTERY)
    if len(pkt.payload) < 3:
        raise ValueError(f"Battery response too short: {pkt.payload.hex()}")
    return BatteryStatus(
        left=pkt.payload[0],
        right=pkt.payload[1],
        case=pkt.payload[2],
    )
