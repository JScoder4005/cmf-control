import threading
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QStatusBar, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor
from cmf_control.ui.widgets.battery_bar import BatteryBar
from cmf_control.ui.widgets.anc_toggle import ANCToggle
from cmf_control.ui.widgets.eq_picker import EQPicker
from cmf_control.ui.widgets.gesture_map import GestureMap
from cmf_control.ui.widgets.toggle_switch import ToggleSwitch
from cmf_control.ui.widgets.bass_control import BassControl
from cmf_control.bt.session import BTSession
from cmf_control.features.battery import get_battery
from cmf_control.features.anc import get_anc, set_anc
from cmf_control.features.eq import get_eq, set_eq
from cmf_control.features.gestures import get_gestures, set_gesture
from cmf_control.features.in_ear import get_in_ear, set_in_ear
from cmf_control.features.game_mode import get_game_mode, set_game_mode
from cmf_control.features.bass import get_bass, set_bass
from cmf_control.features.spatial import get_spatial, set_spatial

BATTERY_POLL_MS = 30_000


def _card(widget: QWidget) -> QFrame:
    frame = QFrame()
    frame.setObjectName("card")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(16, 14, 16, 14)
    lay.setSpacing(10)
    lay.addWidget(widget)
    return frame


def _section(label: str, widget: QWidget) -> QFrame:
    frame = QFrame()
    frame.setObjectName("card")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(16, 14, 16, 14)
    lay.setSpacing(8)
    lbl = QLabel(label)
    lbl.setObjectName("section")
    lay.addWidget(lbl)
    lay.addWidget(widget)
    return frame


class MainWindow(QMainWindow):
    def __init__(self, session: BTSession):
        super().__init__()
        self._session = session
        self._connected = False
        self.setWindowTitle("CMF Control")
        self.setMinimumWidth(480)
        self.setMinimumHeight(400)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.setCentralWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        root = QVBoxLayout(container)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(10)

        # Header
        header = QWidget()
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(0, 0, 0, 0)

        left = QVBoxLayout()
        name = QLabel("CMF BUDS PRO 2")
        name.setObjectName("device-name")
        name.setStyleSheet("font-size:17px; letter-spacing:4px; color:#ffffff;")
        sub = QLabel("NOTHING TECHNOLOGY")
        sub.setObjectName("section")
        left.addWidget(name)
        left.addWidget(sub)

        self._dot = QLabel("●")
        self._dot.setObjectName("status-dot")
        self._dot.setStyleSheet("color:#333333; font-size:12px;")
        self._dot.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        hlay.addLayout(left)
        hlay.addStretch()
        hlay.addWidget(self._dot)
        root.addWidget(header)

        # Battery card
        self._battery = BatteryBar()
        root.addWidget(_section("BATTERY", self._battery))

        # Noise control card
        self._anc = ANCToggle()
        self._anc.mode_changed.connect(self._on_anc_changed)
        root.addWidget(_section("NOISE CONTROL", self._anc))

        # Sound profile card
        self._eq = EQPicker()
        self._eq.preset_changed.connect(self._on_eq_changed)
        root.addWidget(_section("SOUND PROFILE", self._eq))

        # Toggles row card
        toggles_frame = QFrame()
        toggles_frame.setObjectName("card")
        tlay = QVBoxLayout(toggles_frame)
        tlay.setContentsMargins(16, 14, 16, 14)
        tlay.setSpacing(12)

        for label, attr, signal_name, handler in [
            ("GAME MODE",        "_game_mode", "toggled", self._on_game_mode_changed),
            ("SPATIAL AUDIO",    "_spatial",   "toggled", self._on_spatial_changed),
            ("IN-EAR DETECTION", "_in_ear",    "toggled", self._on_in_ear_changed),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setObjectName("section")
            sw = ToggleSwitch()
            getattr(sw, signal_name).connect(handler)
            setattr(self, attr, sw)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(sw)
            tlay.addLayout(row)

        root.addWidget(toggles_frame)

        # Bass card
        self._bass = BassControl()
        self._bass.changed.connect(self._on_bass_changed)
        root.addWidget(_section("BASS ENHANCE", self._bass))

        # Gestures card
        self._gestures = GestureMap()
        self._gestures.gesture_changed.connect(self._on_gesture_changed)
        root.addWidget(_section("TOUCH CONTROLS", self._gestures))

        root.addStretch()

        self._status = QStatusBar()
        self.setStatusBar(self._status)

        # Battery poll timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_battery)

        # Animated connecting dot
        self._dot_timer = QTimer(self)
        self._dot_states = ["●", "◉", "○", "◉"]
        self._dot_idx = 0
        self._dot_timer.timeout.connect(self._pulse_dot)
        self._dot_timer.start(500)

    def _pulse_dot(self):
        if self._connected:
            return
        self._dot.setText(self._dot_states[self._dot_idx % len(self._dot_states)])
        self._dot_idx += 1

    def on_connected(self):
        self._connected = True
        self._dot_timer.stop()
        self._dot.setText("●")
        self._dot.setStyleSheet("color:#00ff88; font-size:12px;")
        self._load_initial_state()
        self._timer.start(BATTERY_POLL_MS)

    def _load_initial_state(self):
        try:
            status = get_battery(self._session)
            self._battery.update_status(status.left, status.right, status.case)
        except Exception:
            pass
        try:
            self._anc.set_mode(get_anc(self._session))
        except Exception:
            pass
        try:
            self._eq.set_preset(get_eq(self._session))
        except Exception:
            pass
        try:
            self._game_mode.set_state(get_game_mode(self._session))
        except Exception:
            pass
        try:
            self._spatial.set_state(get_spatial(self._session))
        except Exception:
            pass
        try:
            self._in_ear.set_state(get_in_ear(self._session))
        except Exception:
            pass
        try:
            enable, level = get_bass(self._session)
            self._bass.set_state(enable, level)
        except Exception:
            pass
        try:
            slots = get_gestures(self._session)
            self._gestures.set_gestures(slots)
        except Exception:
            pass
        self._status.showMessage("Connected · CMF Buds Pro 2")

    def _poll_battery(self):
        if not self._connected:
            return
        try:
            status = get_battery(self._session)
            self._battery.update_status(status.left, status.right, status.case)
        except Exception:
            pass

    def _bg(self, fn):
        threading.Thread(target=fn, daemon=True).start()

    def _on_anc_changed(self, mode: int):
        s = self._session
        def run():
            try: set_anc(s, mode)
            except Exception: pass
        self._bg(run)

    def _on_eq_changed(self, preset: int):
        s = self._session
        def run():
            try: set_eq(s, preset)
            except Exception: pass
        self._bg(run)

    def _on_game_mode_changed(self, enable: bool):
        s = self._session
        def run():
            try: set_game_mode(s, enable)
            except Exception: pass
        self._bg(run)

    def _on_spatial_changed(self, enable: bool):
        s = self._session
        def run():
            try: set_spatial(s, enable)
            except Exception: pass
        self._bg(run)

    def _on_in_ear_changed(self, enable: bool):
        s = self._session
        def run():
            try: set_in_ear(s, enable)
            except Exception: pass
        self._bg(run)

    def _on_bass_changed(self, enable: bool, level: int):
        s = self._session
        def run():
            try: set_bass(s, enable, level)
            except Exception: pass
        self._bg(run)

    def _on_gesture_changed(self, device: int, button_id: int, gesture_type: int, action: int):
        s = self._session
        def run():
            try: set_gesture(s, device, button_id, gesture_type, action)
            except Exception: pass
        self._bg(run)
