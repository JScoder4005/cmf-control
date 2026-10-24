"""Headless screenshot renderer for the main window.

Spins up MainWindow in offscreen Qt, feeds synthetic state so the
connected UI (battery / ANC / EQ / toggles / graph / gestures) is
visible, and saves PNGs to docs/screenshots/.

Run with the installed system Python so python3-pyqt6 / python3-gi
are available:

    QT_QPA_PLATFORM=offscreen /usr/bin/python3 tools/capture_shots.py
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from cmf_control.ui.theme import NOTHING_DARK_QSS
from cmf_control.bt.session import BTSession
from cmf_control.ui.main_window import MainWindow

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _pump(app: QApplication, ms: int = 300) -> None:
    end = time.monotonic() + ms / 1000.0
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(0.01)


def _find_scroll_container(window: MainWindow):
    from PyQt6.QtWidgets import QScrollArea
    for sa in window.findChildren(QScrollArea):
        inner = sa.widget()
        if inner is not None:
            return inner
    return None


def _render(window: MainWindow, path: Path) -> None:
    inner = _find_scroll_container(window)
    if inner is None:
        pix = window.grab()
    else:
        inner.adjustSize()
        # ensure a sane target width for the shot
        inner.setFixedWidth(520)
        inner.adjustSize()
        pix = inner.grab()
    pix.save(str(path), "PNG")
    print(f"wrote {path}  ({pix.width()}x{pix.height()})")


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(NOTHING_DARK_QSS)

    session = BTSession("2C:BE:EE:F0:00:3C")
    window = MainWindow(session)
    window.resize(520, 1600)
    window.show()
    _pump(app, 300)

    _render(window, OUT_DIR / "main_disconnected.png")

    window.on_connected()
    window._battery.update_status(95, 90, 72, False, False, True)
    window.battery_updated.emit(95, 90, 72)
    window._fw_label.setText("FW 1.0.1")
    window._rssi_label.setText("▂▄▆█ -48 dBm")
    try:
        window._anc.set_mode(7)
    except Exception:
        pass
    try:
        window._eq.set_preset(0)
    except Exception:
        pass
    try:
        window._game_mode.set_state(False)
        window._spatial.set_state(True)
        window._in_ear.set_state(True)
    except Exception:
        pass
    try:
        window._bass.set_state(True, 3)
    except Exception:
        pass
    _pump(app, 400)

    _render(window, OUT_DIR / "main_connected.png")

    app.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
