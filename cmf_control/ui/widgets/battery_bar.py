from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt


class BatteryBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self._bars = {}
        items = [("L", "left"), ("R", "right"), ("CASE", "case")]
        for i, (label_text, key) in enumerate(items):
            col = QVBoxLayout()
            col.setSpacing(4)
            col.setAlignment(Qt.AlignmentFlag.AlignCenter)

            lbl = QLabel(label_text)
            lbl.setStyleSheet("color:#333333; font-size:10px; letter-spacing:3px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            pct = QLabel("—")
            pct.setStyleSheet("color:#ffffff; font-size:26px; letter-spacing:-1px;")
            pct.setAlignment(Qt.AlignmentFlag.AlignCenter)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setFixedHeight(2)
            bar.setTextVisible(False)

            col.addWidget(lbl)
            col.addWidget(pct)
            col.addWidget(bar)

            layout.addLayout(col)
            if i < len(items) - 1:
                layout.addStretch()

            self._bars[key] = (bar, pct)

    def update_status(self, left: int, right: int, case: int,
                      left_chg: bool = False, right_chg: bool = False, case_chg: bool = False):
        data = [("left", left, left_chg), ("right", right, right_chg), ("case", case, case_chg)]
        for key, val, chg in data:
            bar, pct = self._bars[key]
            bar.setValue(val)
            if val == 0:
                pct.setText("—")
            else:
                bolt = " ⚡" if chg else ""
                pct.setText(f"{val}%{bolt}")
