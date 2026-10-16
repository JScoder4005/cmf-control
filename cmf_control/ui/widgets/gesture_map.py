from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox
from PyQt6.QtCore import pyqtSignal
from cmf_control.features.gestures import SLOTS, ACTIONS, GestureSlot

class GestureMap(QWidget):
    gesture_changed = pyqtSignal(int, int, int, int)  # (device, button_id, gesture_type, action)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setSpacing(8)
        self._combos: dict[tuple, QComboBox] = {}
        self._action_keys = list(ACTIONS.keys())

        for row, (label, device, button_id, gtype) in enumerate(SLOTS):
            lbl = QLabel(label.upper())
            lbl.setObjectName("subtitle")
            combo = QComboBox()
            for action_val, action_name in ACTIONS.items():
                combo.addItem(action_name.upper(), action_val)
            key = (device, button_id, gtype)
            combo.currentIndexChanged.connect(
                lambda _, k=key, c=combo: self._on_change(k, c)
            )
            layout.addWidget(lbl, row, 0)
            layout.addWidget(combo, row, 1)
            self._combos[key] = combo

    def _on_change(self, key: tuple, combo: QComboBox):
        device, button_id, gtype = key
        action = combo.currentData()
        self.gesture_changed.emit(device, button_id, gtype, action)

    def set_gestures(self, slots: list[GestureSlot]):
        for slot in slots:
            key = (slot.device, slot.button_id, slot.gesture_type)
            if key in self._combos:
                combo = self._combos[key]
                idx = self._action_keys.index(slot.action) if slot.action in self._action_keys else 0
                combo.blockSignals(True)
                combo.setCurrentIndex(idx)
                combo.blockSignals(False)
