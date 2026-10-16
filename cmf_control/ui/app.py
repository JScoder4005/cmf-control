import sys
import time
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal
from cmf_control.ui.theme import NOTHING_DARK_QSS
from cmf_control.ui.main_window import MainWindow
from cmf_control.bt.session import BTSession


class ConnectThread(QThread):
    success = pyqtSignal()
    lost = pyqtSignal()

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
    app.setStyleSheet(NOTHING_DARK_QSS)

    session = BTSession("2C:BE:EE:F0:00:3C")
    window = MainWindow(session)
    window.show()
    window.raise_()
    window.activateWindow()

    thread = ConnectThread(session)

    def on_success():
        window.on_connected()

    thread.success.connect(on_success)
    thread.start()

    ret = app.exec()
    thread.stop()
    session.disconnect()
    return ret
