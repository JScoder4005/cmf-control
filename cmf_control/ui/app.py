import sys
from PyQt6.QtWidgets import QApplication, QMessageBox, QLabel
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from cmf_control.ui.theme import NOTHING_DARK_QSS
from cmf_control.ui.main_window import MainWindow
from cmf_control.bt.session import BTSession


class ConnectThread(QThread):
    success = pyqtSignal(object)
    failure = pyqtSignal(str)

    def __init__(self, session: BTSession):
        super().__init__()
        self._session = session

    def run(self):
        try:
            self._session.connect()
            self.success.emit(self._session)
        except Exception as e:
            self.failure.emit(str(e))


def run() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(NOTHING_DARK_QSS)

    splash = QLabel("Connecting to CMF Buds Pro 2...")
    splash.setStyleSheet("background:#0a0a0a; color:white; font-size:16px; padding:40px;")
    splash.setAlignment(Qt.AlignmentFlag.AlignCenter)
    splash.setWindowFlags(Qt.WindowType.SplashScreen)
    splash.resize(400, 100)
    splash.show()
    app.processEvents()

    session = BTSession("2C:BE:EE:F0:00:3C")
    window_holder = {}

    thread = ConnectThread(session)

    def on_success(s):
        splash.close()
        window = MainWindow(s)
        window_holder["w"] = window
        window.show()
        window.raise_()
        window.activateWindow()

    def on_failure(msg):
        splash.close()
        QMessageBox.critical(None, "CMF Control",
            f"Could not connect:\n{msg}")
        app.quit()

    thread.success.connect(on_success)
    thread.failure.connect(on_failure)
    thread.start()

    ret = app.exec()
    if "w" in window_holder:
        session.disconnect()
    return ret
