import json
import os
import time
from pathlib import Path

HISTORY_PATH = Path.home() / ".cache" / "cmf-control-battery.json"
MAX_POINTS = 288  # 24h at 5min interval


def _load() -> list[dict]:
    try:
        return json.loads(HISTORY_PATH.read_text())
    except Exception:
        return []


def _save(data: list[dict]) -> None:
    try:
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        HISTORY_PATH.write_text(json.dumps(data))
    except Exception:
        pass


def record(left: int, right: int, case: int) -> None:
    if left == 0 and right == 0 and case == 0:
        return
    data = _load()
    now = int(time.time())
    if data and now - data[-1]["t"] < 60:
        return  # dedupe: at most 1 point/min
    data.append({"t": now, "l": left, "r": right, "c": case})
    if len(data) > MAX_POINTS:
        data = data[-MAX_POINTS:]
    _save(data)


def load_last_24h() -> list[dict]:
    cutoff = int(time.time()) - 24 * 3600
    return [p for p in _load() if p["t"] >= cutoff]
