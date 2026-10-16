import threading
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QLabel, QFrame, QStatusBar, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
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

class MainWindow(QMainWindow):
    def __init__(self, session: BTSession):
        super().__init__()
        self._session = session
        self._connected = False
        self.setWindowTitle("CMF CONTROL")
        self.setMinimumWidth(540)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        root = QVBoxLayout(container)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(20)

        title = QLabel("CMF CONTROL")
        title.setStyleSheet("font-size: 18px; letter-spacing: 4px;")
        subtitle = QLabel("BUDS PRO 2")
        subtitle.setObjectName("subtitle")
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(self._sep())

        root.addWidget(QLabel("BATTERY"))
        self._battery = BatteryBar()
        root.addWidget(self._battery)
        root.addWidget(self._sep())

        root.addWidget(QLabel("NOISE CONTROL"))
        self._anc = ANCToggle()
        self._anc.mode_changed.connect(self._on_anc_changed)
        root.addWidget(self._anc)
        root.addWidget(self._sep())

        root.addWidget(QLabel("SOUND PROFILE"))
        self._eq = EQPicker()
        self._eq.preset_changed.connect(self._on_eq_changed)
        root.addWidget(self._eq)
        root.addWidget(self._sep())

        root.addWidget(QLabel("GAME MODE"))
        self._game_mode = ToggleSwitch()
        self._game_mode.toggled.connect(self._on_game_mode_changed)
        root.addWidget(self._game_mode)
        root.addWidget(self._sep())

        root.addWidget(QLabel("SPATIAL AUDIO"))
        self._spatial = ToggleSwitch()
        self._spatial.toggled.connect(self._on_spatial_changed)
        root.addWidget(self._spatial)
        root.addWidget(self._sep())

        root.addWidget(QLabel("IN-EAR DETECTION"))
        self._in_ear = ToggleSwitch()
        self._in_ear.toggled.connect(self._on_in_ear_changed)
        root.addWidget(self._in_ear)
        root.addWidget(self._sep())

        root.addWidget(QLabel("BASS ENHANCE"))
        self._bass = BassControl()
        self._bass.changed.connect(self._on_bass_changed)
        root.addWidget(self._bass)
        root.addWidget(self._sep())

        root.addWidget(QLabel("TOUCH CONTROLS"))
        self._gestures = GestureMap()
        self._gestures.gesture_changed.connect(self._on_gesture_changed)
        root.addWidget(self._gestures)

        root.addStretch()

        self._status = QStatusBar()
        self.setStatusBar(self._status)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_battery)

        self._status.showMessage("Connecting to CMF Buds Pro 2...")

    def on_connected(self):
        self._connected = True
        self._load_initial_state()
        self._timer.start(BATTERY_POLL_MS)

    def _sep(self) -> QFrame:
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        return sep

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
        self._status.showMessage("Connected")

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
        session, status = self._session, self._status
        def run():
            try:
                set_anc(session, mode)
            except Exception as e:
                status.showMessage(f"ANC error: {e}")
        self._bg(run)

    def _on_eq_changed(self, preset: int):
        session, status = self._session, self._status
        def run():
            try:
                set_eq(session, preset)
            except Exception as e:
                status.showMessage(f"EQ error: {e}")
        self._bg(run)

    def _on_game_mode_changed(self, enable: bool):
        session, status = self._session, self._status
        def run():
            try:
                set_game_mode(session, enable)
            except Exception as e:
                status.showMessage(f"Game mode error: {e}")
        self._bg(run)

    def _on_spatial_changed(self, enable: bool):
        session, status = self._session, self._status
        def run():
            try:
                set_spatial(session, enable)
            except Exception as e:
                status.showMessage(f"Spatial audio error: {e}")
        self._bg(run)

    def _on_in_ear_changed(self, enable: bool):
        session, status = self._session, self._status
        def run():
            try:
                set_in_ear(session, enable)
            except Exception as e:
                status.showMessage(f"In-ear error: {e}")
        self._bg(run)

    def _on_bass_changed(self, enable: bool, level: int):
        session, status = self._session, self._status
        def run():
            try:
                set_bass(session, enable, level)
            except Exception as e:
                status.showMessage(f"Bass error: {e}")
        self._bg(run)

    def _on_gesture_changed(self, device: int, button_id: int, gesture_type: int, action: int):
        session, status = self._session, self._status
        def run():
            try:
                set_gesture(session, device, button_id, gesture_type, action)
            except Exception as e:
                status.showMessage(f"Gesture error: {e}")
        self._bg(run)
