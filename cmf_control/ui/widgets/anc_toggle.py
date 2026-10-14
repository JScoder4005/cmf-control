from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal
from cmf_control.features.anc import ANC_MODES

class ANCToggle(QWidget):
    mode_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        self._buttons: dict[int, QPushButton] = {}

        for mode, label in ANC_MODES.items():
            btn = QPushButton(label.upper())
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, m=mode: self._on_click(m))
            layout.addWidget(btn)
            self._buttons[mode] = btn

    def _on_click(self, mode: int):
        self.set_mode(mode)
        self.mode_changed.emit(mode)

    def set_mode(self, mode: int):
        for m, btn in self._buttons.items():
            btn.setChecked(m == mode)
