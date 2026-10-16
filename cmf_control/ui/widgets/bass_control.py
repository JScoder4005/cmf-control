from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from cmf_control.ui.widgets.toggle_switch import ToggleSwitch


class BassControl(QWidget):
    changed = pyqtSignal(bool, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        row = QHBoxLayout()
        self._lbl = QLabel("BASS ENHANCE")
        self._lbl.setStyleSheet("color:#333333; font-size:10px; letter-spacing:3px;")
        self._toggle = ToggleSwitch()
        self._toggle.toggled.connect(self._on_toggle)
        row.addWidget(self._lbl)
        row.addStretch()
        row.addWidget(self._toggle)
        layout.addLayout(row)

        slider_row = QHBoxLayout()
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 5)
        self._slider.setEnabled(False)
        self._level_lbl = QLabel("0")
        self._level_lbl.setStyleSheet("color:#555555; font-size:11px; min-width:12px;")
        self._slider.valueChanged.connect(self._on_slider)
        slider_row.addWidget(self._slider)
        slider_row.addWidget(self._level_lbl)
        self._slider_widget = QWidget()
        self._slider_widget.setLayout(slider_row)
        self._slider_widget.hide()
        layout.addWidget(self._slider_widget)

    def _on_toggle(self, state: bool):
        self._slider.setEnabled(state)
        self._slider_widget.setVisible(state)
        self.changed.emit(state, self._slider.value())

    def _on_slider(self, value: int):
        self._level_lbl.setText(str(value))
        if self._toggle._state:
            self.changed.emit(True, value)

    def set_state(self, enable: bool, level: int):
        self._toggle.set_state(enable)
        self._slider.setValue(level)
        self._level_lbl.setText(str(level))
        self._slider.setEnabled(enable)
        self._slider_widget.setVisible(enable)
