from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt

class BatteryBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(16)

        self._bars = {}
        for label_text, key in [("L", "left"), ("R", "right"), ("CASE", "case")]:
            col = QVBoxLayout()
            lbl = QLabel(label_text)
            lbl.setObjectName("subtitle")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setFixedHeight(4)
            bar.setTextVisible(False)
            pct = QLabel("—%")
            pct.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(lbl)
            col.addWidget(bar)
            col.addWidget(pct)
            layout.addLayout(col)
            self._bars[key] = (bar, pct)

    def update_status(self, left: int, right: int, case: int):
        for key, val in [("left", left), ("right", right), ("case", case)]:
            bar, pct = self._bars[key]
            bar.setValue(val)
            pct.setText(f"{val}%")
