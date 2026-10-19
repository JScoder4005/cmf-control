import subprocess
import re

_RSSI_RE = re.compile(r"RSSI:\s*(-?\d+)")


def get_rssi(address: str, timeout: float = 2.0) -> int | None:
    try:
        out = subprocess.run(
            ["bluetoothctl", "info", address],
            capture_output=True, text=True, timeout=timeout
        ).stdout
    except Exception:
        return None
    m = _RSSI_RE.search(out)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def rssi_to_bars(rssi: int | None) -> str:
    if rssi is None:
        return ""
    # typical range: -40 (great) to -90 (bad)
    if rssi >= -50:
        return "▮▮▮▮▮"
    if rssi >= -60:
        return "▮▮▮▮▯"
    if rssi >= -70:
        return "▮▮▮▯▯"
    if rssi >= -80:
        return "▮▮▯▯▯"
    return "▮▯▯▯▯"
