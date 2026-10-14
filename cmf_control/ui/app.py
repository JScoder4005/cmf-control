import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from cmf_control.ui.theme import NOTHING_DARK_QSS
from cmf_control.ui.main_window import MainWindow
from cmf_control.bt.scanner import scan_devices
from cmf_control.bt.session import BTSession

def run() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(NOTHING_DARK_QSS)

    devices = scan_devices()
    if not devices:
        QMessageBox.critical(None, "CMF Control", "No CMF/Nothing devices found.\n\nPair your earbuds first via bluetoothctl.")
        return 1

    # Pick first match (future: show device picker dialog)
    device = devices[0]
    session = BTSession(device.address)

    try:
        session.connect()
    except OSError as e:
        QMessageBox.critical(None, "CMF Control", f"Could not connect to {device.name} ({device.address}):\n{e}")
        return 1

    window = MainWindow(session)
    window.show()

    ret = app.exec()
    session.disconnect()
    return ret
