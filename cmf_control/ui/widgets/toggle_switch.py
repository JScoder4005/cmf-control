from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal

class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        self._on_btn = QPushButton("ON")
        self._on_btn.setCheckable(True)
        self._off_btn = QPushButton("OFF")
        self._off_btn.setCheckable(True)

        self._on_btn.clicked.connect(lambda: self._on_click(True))
        self._off_btn.clicked.connect(lambda: self._on_click(False))

        layout.addWidget(self._on_btn)
        layout.addWidget(self._off_btn)
        layout.addStretch()

        self.set_state(False)

    def _on_click(self, state: bool):
        self.set_state(state)
        self.toggled.emit(state)

    def set_state(self, state: bool):
        self._on_btn.setChecked(state)
        self._off_btn.setChecked(not state)
