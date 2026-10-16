from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSlider, QLabel
from PyQt6.QtCore import pyqtSignal, Qt

class BassControl(QWidget):
    changed = pyqtSignal(bool, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        self._on_btn = QPushButton("ON")
        self._on_btn.setCheckable(True)
        self._off_btn = QPushButton("OFF")
        self._off_btn.setCheckable(True)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 5)
        self._slider.setFixedWidth(120)

        self._level_lbl = QLabel("0")

        self._on_btn.clicked.connect(lambda: self._on_toggle(True))
        self._off_btn.clicked.connect(lambda: self._on_toggle(False))
        self._slider.valueChanged.connect(self._on_slider)

        layout.addWidget(self._on_btn)
        layout.addWidget(self._off_btn)
        layout.addWidget(self._slider)
        layout.addWidget(self._level_lbl)
        layout.addStretch()

        self.set_state(False, 0)

    def _on_toggle(self, state: bool):
        self.set_state(state, self._slider.value())
        self.changed.emit(state, self._slider.value())

    def _on_slider(self, value: int):
        self._level_lbl.setText(str(value))
        if self._on_btn.isChecked():
            self.changed.emit(True, value)

    def set_state(self, enable: bool, level: int):
        self._on_btn.setChecked(enable)
        self._off_btn.setChecked(not enable)
        self._slider.setEnabled(enable)
        self._slider.setValue(level)
        self._level_lbl.setText(str(level))
