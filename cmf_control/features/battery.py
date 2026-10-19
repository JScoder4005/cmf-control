from dataclasses import dataclass
from cmf_control.bt.session import BTSession
from cmf_control.protocol.constants import (
    CMD_GET_BATTERY, BATT_KEY_LEFT, BATT_KEY_RIGHT, BATT_KEY_CASE, BATT_LEVEL_MASK
)

LOW_BATTERY_THRESHOLD = 20

@dataclass
class BatteryStatus:
    left: int    # 0-100
    right: int   # 0-100
    case: int    # 0-100

def is_low_battery(status: "BatteryStatus") -> bool:
    """True if either earbud (while worn/in case, i.e. reporting > 0) is at or below threshold."""
    levels = [v for v in (status.left, status.right) if v > 0]
    if not levels:
        return False
    return min(levels) <= LOW_BATTERY_THRESHOLD

def get_battery(session: BTSession, timeout: float | None = None) -> BatteryStatus:
    pkt = session.send(CMD_GET_BATTERY, timeout=timeout)
    p = pkt.payload
    if len(p) < 2:
        raise ValueError(f"Battery response too short: {p.hex()}")
    # Payload: count byte, then (key, value) pairs — DeviceBattery SparseArray
    levels = {}
    i = 1  # skip count byte
    while i + 1 <= len(p) - 1:
        key, val = p[i], p[i + 1]
        levels[key] = val & BATT_LEVEL_MASK
        i += 2
    return BatteryStatus(
        left=levels.get(BATT_KEY_LEFT, 0),
        right=levels.get(BATT_KEY_RIGHT, 0),
        case=levels.get(BATT_KEY_CASE, 0),
    )
