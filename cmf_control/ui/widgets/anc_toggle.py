from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal
from cmf_control.features.anc import ANC_MODES


class ANCToggle(QWidget):
    mode_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self._buttons: dict[int, QPushButton] = {}

        modes = list(ANC_MODES.items())
        for i, (mode, label) in enumerate(modes):
            btn = QPushButton(label.upper())
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, m=mode: self._on_click(m))

            if len(modes) == 1:
                radius = "border-radius:4px;"
            elif i == 0:
                radius = "border-radius:4px 0 0 4px; border-right:none;"
            elif i == len(modes) - 1:
                radius = "border-radius:0 4px 4px 0;"
            else:
                radius = "border-radius:0; border-right:none;"

            btn.setStyleSheet(f"""
                QPushButton {{ {radius} border:1px solid #1c1c1c; background:transparent;
                    color:#555555; padding:8px 14px; font-family:'Space Mono',monospace;
                    font-size:10px; letter-spacing:1px; }}
                QPushButton:hover {{ color:#aaaaaa; border-color:#333333; }}
                QPushButton:checked {{ background:#ffffff; color:#000000; border-color:#ffffff; }}
            """)

            layout.addWidget(btn)
            self._buttons[mode] = btn

    def _on_click(self, mode: int):
        self.set_mode(mode)
        self.mode_changed.emit(mode)

    def set_mode(self, mode: int):
        for m, btn in self._buttons.items():
            btn.setChecked(m == mode)
