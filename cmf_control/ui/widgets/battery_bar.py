from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt

RED = "#FF1744"
GREEN = "#2ECC71"
WHITE = "#ffffff"
LOW_THRESHOLD = 20
BAR_QSS = """
QProgressBar {{
    background:#1a1a1a; border:none; border-radius:1px;
}}
QProgressBar::chunk {{
    background:{color}; border-radius:1px;
}}
"""


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
            col.setSpacing(6)
            col.setAlignment(Qt.AlignmentFlag.AlignCenter)

            lbl = QLabel(label_text)
            lbl.setStyleSheet("color:#333333; font-size:10px; letter-spacing:3px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setFixedHeight(3)
            bar.setTextVisible(False)
            bar.setStyleSheet(BAR_QSS.format(color=WHITE))

            pct = QLabel("—")
            pct.setStyleSheet(f"color:{WHITE}; font-size:28px; letter-spacing:-1px; font-weight:600;")
            pct.setAlignment(Qt.AlignmentFlag.AlignCenter)

            col.addWidget(lbl)
            col.addWidget(bar)
            col.addWidget(pct)

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
                pct.setStyleSheet(f"color:#555555; font-size:28px; letter-spacing:-1px; font-weight:600;")
                bar.setStyleSheet(BAR_QSS.format(color="#1a1a1a"))
            else:
                if chg:
                    color = GREEN
                    bolt = " ⚡"
                elif val <= LOW_THRESHOLD:
                    color = RED
                    bolt = ""
                else:
                    color = WHITE
                    bolt = ""
                pct.setText(f"{val}%{bolt}")
                pct.setStyleSheet(f"color:{color}; font-size:28px; letter-spacing:-1px; font-weight:600;")
                bar.setStyleSheet(BAR_QSS.format(color=color))
