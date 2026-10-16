from PyQt6.QtWidgets import QWidget, QGridLayout, QPushButton
from PyQt6.QtCore import pyqtSignal
from cmf_control.features.eq import EQ_PRESETS

BTN_STYLE = """
    QPushButton {{
        background:transparent; color:#555555;
        border:1px solid #1c1c1c; border-radius:0;
        padding:8px 10px; font-family:'Space Mono',monospace;
        font-size:10px; letter-spacing:1px;
        {extra}
    }}
    QPushButton:hover {{ color:#aaaaaa; border-color:#333333; }}
    QPushButton:checked {{ background:#ffffff; color:#000000; border-color:#ffffff; }}
"""


class EQPicker(QWidget):
    preset_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self._buttons: dict[int, QPushButton] = {}

        items = list(EQ_PRESETS.items())
        cols = 3
        for i, (preset, label) in enumerate(items):
            row, col = divmod(i, cols)
            btn = QPushButton(label.upper())
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, p=preset: self._on_click(p))

            # Border radius for corners
            tl = "4px" if (row == 0 and col == 0) else "0"
            tr = "4px" if (row == 0 and col == cols - 1) else "0"
            bl = "4px" if (row == len(items) // cols and col == 0) else "0"
            br = "4px" if (row == len(items) // cols and col == cols - 1) else "0"
            extra = f"border-radius:{tl} {tr} {br} {bl};"
            if col < cols - 1:
                extra += "border-right:none;"
            if row > 0:
                extra += "border-top:none;"

            btn.setStyleSheet(BTN_STYLE.format(extra=extra))
            layout.addWidget(btn, row, col)
            self._buttons[preset] = btn

    def _on_click(self, preset: int):
        self.set_preset(preset)
        self.preset_changed.emit(preset)

    def set_preset(self, preset: int):
        for p, btn in self._buttons.items():
            btn.setChecked(p == preset)
