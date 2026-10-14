import sys
from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen, QLabel
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QPixmap
from cmf_control.ui.theme import NOTHING_DARK_QSS
from cmf_control.ui.main_window import MainWindow
from cmf_control.bt.session import BTSession


class ConnectThread(QThread):
    success = pyqtSignal(object)   # emits BTSession
    failure = pyqtSignal(str)      # emits error message

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

    # Show scanning label while BLE scan runs
    splash = QLabel("Scanning for CMF Buds Pro 2...\n\nMake sure buds are in your ears.")
    splash.setStyleSheet("background:#0a0a0a; color:white; font-size:16px; padding:40px;")
    splash.setAlignment(Qt.AlignmentFlag.AlignCenter)
    splash.setWindowFlags(Qt.WindowType.SplashScreen)
    splash.resize(400, 160)
    splash.show()
    app.processEvents()

    session = BTSession("61:12:9A:45:F5:5F")  # BLE MAC (BlueZ resolves from paired device)
    result = {}

    thread = ConnectThread(session)

    def on_success(s):
        result["session"] = s
        app.exit(0)

    def on_failure(msg):
        result["error"] = msg
        app.exit(1)

    thread.success.connect(on_success)
    thread.failure.connect(on_failure)
    thread.start()

    code = app.exec()
    splash.close()

    if code != 0 or "error" in result:
        QMessageBox.critical(
            None, "CMF Control",
            f"Could not connect to CMF Buds Pro 2:\n{result.get('error', 'Unknown error')}"
        )
        return 1

    app2 = QApplication.instance()
    window = MainWindow(result["session"])
    window.show()

    try:
        ret = app2.exec()
    finally:
        result["session"].disconnect()
    return ret
