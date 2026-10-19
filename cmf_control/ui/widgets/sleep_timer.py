from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import QTimer, pyqtSignal, Qt

RED = "#FF1744"


class SleepTimer(QWidget):
    expired = pyqtSignal()

    PRESETS = [10, 20, 30, 45, 60]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._remaining_sec = 0
        self._tick = QTimer(self)
        self._tick.timeout.connect(self._on_tick)

        layout = QHBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        self._buttons = []
        for mins in self.PRESETS:
            btn = QPushButton(f"{mins}m")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _=False, m=mins: self._start(m))
            btn.setStyleSheet("""
                QPushButton { background:transparent; color:#555555; border:1px solid #1c1c1c;
                              padding:6px 10px; font-family:'Space Mono',monospace;
                              font-size:10px; letter-spacing:1px; border-radius:2px; }
                QPushButton:hover { color:#aaaaaa; border-color:#333333; }
                QPushButton:checked { background:#ffffff; color:#000000; border-color:#ffffff; }
            """)
            self._buttons.append(btn)
            layout.addWidget(btn)

        self._cancel = QPushButton("CANCEL")
        self._cancel.clicked.connect(self._stop)
        self._cancel.setEnabled(False)
        self._cancel.setStyleSheet(f"""
            QPushButton {{ background:transparent; color:{RED}; border:1px solid #1c1c1c;
                           padding:6px 10px; font-family:'Space Mono',monospace;
                           font-size:10px; letter-spacing:1px; border-radius:2px; }}
            QPushButton:hover:enabled {{ border-color:{RED}; }}
            QPushButton:disabled {{ color:#1a1a1a; }}
        """)
        layout.addWidget(self._cancel)
        layout.addStretch()

        self._status = QLabel("")
        self._status.setStyleSheet("color:#555555; font-size:10px; letter-spacing:2px;")
        self._status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._status)

    def _start(self, minutes: int):
        self._remaining_sec = minutes * 60
        for btn in self._buttons:
            btn.setChecked(int(btn.text().rstrip("m")) == minutes)
        self._cancel.setEnabled(True)
        self._tick.start(1000)
        self._update_status()

    def _stop(self):
        self._tick.stop()
        self._remaining_sec = 0
        for btn in self._buttons:
            btn.setChecked(False)
        self._cancel.setEnabled(False)
        self._status.setText("")

    def _on_tick(self):
        self._remaining_sec -= 1
        if self._remaining_sec <= 0:
            self._stop()
            self.expired.emit()
            return
        self._update_status()

    def _update_status(self):
        m, s = divmod(self._remaining_sec, 60)
        self._status.setText(f"{m:02d}:{s:02d} LEFT")
