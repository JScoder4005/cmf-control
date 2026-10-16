import sys
import os
import time
import threading
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QThread, QTimer, pyqtSignal
from cmf_control.ui.theme import NOTHING_DARK_QSS
from cmf_control.ui.main_window import MainWindow

if sys.platform == "darwin":
    from cmf_control.bt.session_macos import BTSession
else:
    from cmf_control.bt.session import BTSession

ICON_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.png")


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
    icon = QIcon(icon_path)
    app.setWindowIcon(icon)

    session = BTSession("2C:BE:EE:F0:00:3C")
    window = MainWindow(session)

    # System tray
    tray = QSystemTrayIcon(icon, app)
    menu = QMenu()

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
