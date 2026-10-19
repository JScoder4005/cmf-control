import logging
from dataclasses import dataclass
from cmf_control.bt.session import BTSession
from cmf_control.protocol.constants import (
    CMD_GET_BATTERY, BATT_KEY_LEFT, BATT_KEY_RIGHT, BATT_KEY_CASE,
    BATT_LEVEL_MASK, BATT_CHARGING_MASK,
)

log = logging.getLogger("cmf_control.battery")

LOW_BATTERY_THRESHOLD = 20

@dataclass
class BatteryStatus:
    left: int
    right: int
    case: int
    left_charging: bool = False
    right_charging: bool = False
    case_charging: bool = False

def is_low_battery(status: "BatteryStatus") -> bool:
    levels = [v for v in (status.left, status.right) if v > 0]
    if not levels:
        return False
    return min(levels) <= LOW_BATTERY_THRESHOLD

def get_battery(session: BTSession, timeout: float | None = None) -> BatteryStatus:
    pkt = session.send(CMD_GET_BATTERY, timeout=timeout)
    p = pkt.payload
    if len(p) < 2:
        raise ValueError(f"Battery response too short: {p.hex()}")
    log.info(f"raw payload: {p.hex()}")
    levels, charging = {}, {}
    i = 1
    while i + 1 <= len(p) - 1:
        key, val = p[i], p[i + 1]
        levels[key] = val & BATT_LEVEL_MASK
        charging[key] = bool(val & BATT_CHARGING_MASK)
        log.info(f"  key={key} byte=0x{val:02x} level={val & 0x7F}% chg={bool(val & 0x80)}")
        i += 2
    return BatteryStatus(
        left=levels.get(BATT_KEY_LEFT, 0),
        right=levels.get(BATT_KEY_RIGHT, 0),
        case=levels.get(BATT_KEY_CASE, 0),
        left_charging=charging.get(BATT_KEY_LEFT, False),
        right_charging=charging.get(BATT_KEY_RIGHT, False),
        case_charging=charging.get(BATT_KEY_CASE, False),
    )
