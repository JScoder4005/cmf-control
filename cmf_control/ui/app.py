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

    anc_menu = menu.addMenu("Noise Control")
    for mode, label in ANC_MODES.items():
        action = QAction(label)
        action.triggered.connect(lambda _checked=False, m=mode: threading.Thread(
            target=lambda: _safe(set_anc, session, m), daemon=True
        ).start())
        anc_menu.addAction(action)
    menu.addSeparator()

    show_action = QAction("Show")
    show_action.triggered.connect(lambda: (window.show(), window.raise_(), window.activateWindow()))
    menu.addAction(show_action)

    quit_action = QAction("Quit")
    quit_action.triggered.connect(app.quit)
    menu.addAction(quit_action)

    tray.setContextMenu(menu)
    tray.setToolTip("CMF Control — Buds Pro 2")
    tray.activated.connect(lambda reason: (
        window.show(), window.raise_(), window.activateWindow()
    ) if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
    tray.show()

    def update_tray_battery(left: int, right: int, case: int):
        levels = [v for v in (left, right) if v > 0]
        if not levels:
            return
        tray.setIcon(QIcon(_battery_pixmap(f"{min(levels)}%")))

    window.battery_updated.connect(update_tray_battery)

    window.show()
    window.raise_()
    window.activateWindow()

    if sys.platform == "darwin":
        # IOBluetooth only delivers async delegate callbacks to the main
        # thread's run loop, so connect() must run there too — a QThread
        # (like the Linux path below) would never see its callbacks fire.
        retry_timer = QTimer()
        retry_timer.setSingleShot(True)

        def try_connect():
            try:
                session.connect()
                window.on_connected()
            except Exception:
                retry_timer.start(5000)

        retry_timer.timeout.connect(try_connect)
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
