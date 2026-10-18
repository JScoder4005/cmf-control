import sys
import os
import time
import threading
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QFont, QColor
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from cmf_control.ui.theme import NOTHING_DARK_QSS
from cmf_control.ui.main_window import MainWindow
from cmf_control.features.anc import ANC_MODES, set_anc
from cmf_control.features.eq import EQ_PRESETS, set_eq
from cmf_control.features.battery import get_battery
from cmf_control.ui.widgets.connect_popup import ConnectPopup

if sys.platform == "darwin":
    from cmf_control.bt.session_macos import BTSession
else:
    from cmf_control.bt.session import BTSession

ICON_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.png")
RED = "#FF1744"


def _placeholder_icon() -> QIcon:
    scale = 2
    pixmap = QPixmap(16 * scale, 16 * scale)
    pixmap.setDevicePixelRatio(scale)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(RED))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(2, 2, 12, 12)
    painter.end()
    return QIcon(pixmap)


def _battery_pixmap(text: str) -> QPixmap:
    scale = 2  # retina-crisp
    pixmap = QPixmap(44 * scale, 20 * scale)
    pixmap.setDevicePixelRatio(scale)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor(RED))
    font = QFont()
    font.setPointSize(12)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(
        0, 0, 44, 20, Qt.AlignmentFlag.AlignCenter, text
    )
    painter.end()
    return pixmap


def _safe(fn, *args):
    try:
        fn(*args)
    except Exception:
        pass


class ConnectThread(QThread):
    success = pyqtSignal()

    def __init__(self, session: BTSession):
        super().__init__()
        self._session = session
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        while self._running:
            try:
                self._session.connect()
                self.success.emit()
                return
            except Exception:
                time.sleep(5)


def run() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("CMF Control")
    app.setDesktopFileName("cmf-control")
    app.setStyleSheet(NOTHING_DARK_QSS)

    icon_path = os.path.abspath(ICON_PATH)
    icon = QIcon(icon_path) if os.path.exists(icon_path) else _placeholder_icon()
    app.setWindowIcon(icon)

    session = BTSession("2C:BE:EE:F0:00:3C")
    window = MainWindow(session)

    # System tray
    tray = QSystemTrayIcon(icon, app)
    menu = QMenu()
    menu.setStyleSheet("""
        QMenu { background:#0a0a0a; color:#cccccc; border:1px solid #222222;
                font-family:'Space Mono','Courier New',monospace; font-size:11px; padding:4px; }
        QMenu::item { padding:6px 24px 6px 12px; }
        QMenu::item:selected { background:#1a1a1a; color:#ffffff; }
        QMenu::item:disabled { color:#333333; }
        QMenu::separator { background:#1a1a1a; height:1px; margin:4px 0; }
        QMenu::indicator:checked { width:8px; height:8px; background:#FF1744;
                                    border-radius:4px; margin-right:6px; }
    """)

    # Battery header (disabled label, updated dynamically)
    battery_action = QAction("● NOT CONNECTED")
    battery_action.setEnabled(False)
    menu.addAction(battery_action)
    menu.addSeparator()

    # ANC submenu with checkmarks
    anc_menu = menu.addMenu("⊕  NOISE CONTROL")
    anc_actions = {}
    for mode, label in ANC_MODES.items():
        action = QAction(label.upper())
        action.setCheckable(True)
        action.triggered.connect(lambda _=False, m=mode: (
            threading.Thread(target=lambda: _safe(set_anc, session, m), daemon=True).start(),
            [a.setChecked(False) for a in anc_actions.values()],
            anc_actions[m].setChecked(True),
        ))
        anc_menu.addAction(action)
        anc_actions[mode] = action

    # EQ submenu with checkmarks
    eq_menu = menu.addMenu("◈  SOUND PROFILE")
    eq_actions = {}
    for preset, label in EQ_PRESETS.items():
        action = QAction(label.upper())
        action.setCheckable(True)
        action.triggered.connect(lambda _=False, p=preset: (
            threading.Thread(target=lambda: _safe(set_eq, session, p), daemon=True).start(),
            [a.setChecked(False) for a in eq_actions.values()],
            eq_actions[p].setChecked(True),
        ))
        eq_menu.addAction(action)
        eq_actions[preset] = action

    menu.addSeparator()

    show_action = QAction("↗  OPEN CMF CONTROL")
    show_action.triggered.connect(lambda: (window.show(), window.raise_(), window.activateWindow()))
    menu.addAction(show_action)

    menu.addSeparator()

    quit_action = QAction("✕  QUIT")
    quit_action.triggered.connect(app.quit)
    menu.addAction(quit_action)

    tray.setContextMenu(menu)
    tray.setToolTip("CMF Control — CMF Buds Pro 2")
    tray.activated.connect(lambda reason: (
        window.show(), window.raise_(), window.activateWindow()
    ) if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
    # Qt 6.11's QSystemTrayIcon on macOS 26 fails to register its
    # com.apple.appkit.status-items scene with MenuBarAgent ("XPC error
    # received on message reply handler") and retries once a second,
    # forever, with no visible icon ever appearing — confirmed via Console
    # logs, persists even ad-hoc code-signed. Qt/macOS incompatibility, not
    # fixable here. Not calling .show() avoids the infinite retry churn;
    # menu/battery-pixmap code stays in place to re-enable once fixed upstream.
    if sys.platform != "darwin":
        tray.show()

    def update_tray_battery(left: int, right: int, case: int):
        parts = []
        if left > 0:  parts.append(f"L {left}%")
        if right > 0: parts.append(f"R {right}%")
        if case > 0:  parts.append(f"CASE {case}%")
        if parts:
            battery_action.setText("  " + "   ·   ".join(parts))
            levels = [v for v in (left, right) if v > 0]
            tray.setIcon(QIcon(_battery_pixmap(f"{min(levels)}%")))
            tray.setToolTip("CMF Buds Pro 2  ·  " + "  ".join(parts))

    def update_tray_anc(mode: int):
        for m, a in anc_actions.items():
            a.setChecked(m == mode)

    def update_tray_eq(preset: int):
        for p, a in eq_actions.items():
            a.setChecked(p == preset)

    window.battery_updated.connect(update_tray_battery)
    window.anc_updated.connect(update_tray_anc)
    window.eq_updated.connect(update_tray_eq)

    window.show()
    window.raise_()
    window.activateWindow()

    if sys.platform == "darwin":
        # IOBluetooth only delivers async delegate callbacks to the main
        # thread's run loop, so connect() must run there too — a QThread
        # (like the Linux path below) would never see its callbacks fire.
        popup = ConnectPopup()
        connect_state = {"attempts": 0, "was_connected": False}

        def is_live_connected() -> bool:
            # session._channel alone can go stale: if the delegate's
            # rfcommChannelClosed_ callback doesn't fire on a disconnect,
            # the cached reference never gets nulled and we'd believe
            # we're connected forever. Verify against IOBluetooth directly.
            return (
                session._channel is not None
                and session._device is not None
                and session._device.isConnected()
            )

        def try_connect():
            if is_live_connected():
                return  # already connected — nothing to do this tick
            try:
                session.connect()
                window.on_connected()
                if connect_state["attempts"] > 0 or connect_state["was_connected"]:
                    # Not the instant-success-at-launch case — a real
                    # reconnect (case opened, buds came back in range).
                    try:
                        s = get_battery(session)
                        popup.show_with(s.left, s.right, s.case)
                    except Exception:
                        pass
                connect_state["was_connected"] = True
                connect_state["attempts"] = 0
            except Exception:
                connect_state["attempts"] += 1

        # A recurring watchdog, not a one-shot-on-failure timer: after the
        # first successful connect() nothing else was ever checking for a
        # later disconnect (case closed) and reconnect (case opened again),
        # so that transition was silently never noticed.
        watchdog_timer = QTimer()
        watchdog_timer.setInterval(5000)
        watchdog_timer.timeout.connect(try_connect)
        watchdog_timer.start()
        QTimer.singleShot(0, try_connect)

        ret = app.exec()
        session.disconnect()
        return ret

    thread = ConnectThread(session)
    thread.success.connect(window.on_connected)
    thread.start()

    ret = app.exec()
    thread.stop()
    session.disconnect()
    return ret
