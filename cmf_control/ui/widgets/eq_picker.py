from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal
from cmf_control.features.eq import EQ_PRESETS

class EQPicker(QWidget):
    preset_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        self._buttons: dict[int, QPushButton] = {}

        for preset, label in EQ_PRESETS.items():
            btn = QPushButton(label.upper())
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, p=preset: self._on_click(p))
            layout.addWidget(btn)
            self._buttons[preset] = btn

    def _on_click(self, preset: int):
        self.set_preset(preset)
        self.preset_changed.emit(preset)

    def set_preset(self, preset: int):
        for p, btn in self._buttons.items():
            btn.setChecked(p == preset)
