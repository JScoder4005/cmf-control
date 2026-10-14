from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox
from PyQt6.QtCore import pyqtSignal
from cmf_control.features.gestures import GESTURE_ACTIONS, GESTURE_POSITIONS
from cmf_control.protocol.constants import (
    GESTURE_LEFT_SINGLE, GESTURE_LEFT_DOUBLE, GESTURE_LEFT_TRIPLE, GESTURE_LEFT_HOLD,
    GESTURE_RIGHT_SINGLE, GESTURE_RIGHT_DOUBLE, GESTURE_RIGHT_TRIPLE, GESTURE_RIGHT_HOLD,
)

POSITION_LABELS = {
    GESTURE_LEFT_SINGLE:  "L · Single",
    GESTURE_LEFT_DOUBLE:  "L · Double",
    GESTURE_LEFT_TRIPLE:  "L · Triple",
    GESTURE_LEFT_HOLD:    "L · Hold",
    GESTURE_RIGHT_SINGLE: "R · Single",
    GESTURE_RIGHT_DOUBLE: "R · Double",
    GESTURE_RIGHT_TRIPLE: "R · Triple",
    GESTURE_RIGHT_HOLD:   "R · Hold",
}

class GestureMap(QWidget):
    gesture_changed = pyqtSignal(int, int)  # (position, action)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setSpacing(8)
        self._combos: dict[int, QComboBox] = {}
        self._action_keys = list(GESTURE_ACTIONS.keys())

        for row, pos in enumerate(GESTURE_POSITIONS):
            lbl = QLabel(POSITION_LABELS[pos])
            lbl.setObjectName("subtitle")
            combo = QComboBox()
            for action, name in GESTURE_ACTIONS.items():
                combo.addItem(name.upper(), action)
            combo.currentIndexChanged.connect(
                lambda _, p=pos, c=combo: self._on_change(p, c)
            )
            layout.addWidget(lbl, row, 0)
            layout.addWidget(combo, row, 1)
            self._combos[pos] = combo

    def _on_change(self, position: int, combo: QComboBox):
        action = combo.currentData()
        self.gesture_changed.emit(position, action)

    def set_map(self, gmap: dict[int, int]):
        for pos, action in gmap.items():
            if pos in self._combos:
                idx = self._action_keys.index(action) if action in self._action_keys else 0
                self._combos[pos].blockSignals(True)
                self._combos[pos].setCurrentIndex(idx)
                self._combos[pos].blockSignals(False)
