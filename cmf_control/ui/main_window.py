import threading
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
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
LABEL_STYLE = "color:#333333; font-size:10px; letter-spacing:3px;"
ROW_LABEL_STYLE = "color:#444444; font-size:11px; letter-spacing:2px;"


def _sep():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet("background:#0f0f0f; max-height:1px; border:none;")
    return f


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(LABEL_STYLE)
    return lbl


class MainWindow(QMainWindow):
    def __init__(self, session: BTSession):
        super().__init__()
        self._session = session
        self._connected = False
        self.setWindowTitle("CMF Control")
        self.setMinimumWidth(420)
        self.setMaximumWidth(560)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.setCentralWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        root = QVBoxLayout(container)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(20)

        # ── Header ──────────────────────────────────────────────
        header = QHBoxLayout()
        left_col = QVBoxLayout()
        left_col.setSpacing(2)
        device_lbl = QLabel("CMF BUDS PRO 2")
        device_lbl.setStyleSheet("color:#ffffff; font-size:16px; letter-spacing:4px;")
        brand_lbl = QLabel("NOTHING TECHNOLOGY")
        brand_lbl.setStyleSheet("color:#222222; font-size:10px; letter-spacing:3px;")
        left_col.addWidget(device_lbl)
        left_col.addWidget(brand_lbl)

        self._dot = QLabel("●")
        self._dot.setStyleSheet("color:#222222; font-size:11px;")
        self._dot.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        header.addLayout(left_col)
        header.addStretch()
        header.addWidget(self._dot)
        root.addLayout(header)
        root.addWidget(_sep())

        # ── Battery ─────────────────────────────────────────────
        self._battery = BatteryBar()
        root.addWidget(self._battery)
        root.addWidget(_sep())

        # ── Noise Control ────────────────────────────────────────
        root.addWidget(_section_label("NOISE CONTROL"))
        self._anc = ANCToggle()
        self._anc.mode_changed.connect(self._on_anc_changed)
        root.addWidget(self._anc)
        root.addWidget(_sep())

        # ── Sound Profile ────────────────────────────────────────
        root.addWidget(_section_label("SOUND PROFILE"))
        self._eq = EQPicker()
        self._eq.preset_changed.connect(self._on_eq_changed)
        root.addWidget(self._eq)
        root.addWidget(_sep())

        # ── Toggle rows ──────────────────────────────────────────
        toggles = QVBoxLayout()
        toggles.setSpacing(16)
        toggles.setContentsMargins(0, 0, 0, 0)

        self._game_mode = ToggleSwitch()
        self._spatial = ToggleSwitch()
        self._in_ear = ToggleSwitch()

        self._game_mode.toggled.connect(self._on_game_mode_changed)
        self._spatial.toggled.connect(self._on_spatial_changed)
        self._in_ear.toggled.connect(self._on_in_ear_changed)

        for label, widget in [
            ("GAME MODE", self._game_mode),
            ("SPATIAL AUDIO", self._spatial),
            ("IN-EAR DETECTION", self._in_ear),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet(ROW_LABEL_STYLE)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(widget)
            toggles.addLayout(row)

        root.addLayout(toggles)
        root.addWidget(_sep())

        # ── Bass ─────────────────────────────────────────────────
        self._bass = BassControl()
        self._bass.changed.connect(self._on_bass_changed)
        root.addWidget(self._bass)
        root.addWidget(_sep())

        # ── Touch Controls ───────────────────────────────────────
        root.addWidget(_section_label("TOUCH CONTROLS"))
        self._gestures = GestureMap()
        self._gestures.gesture_changed.connect(self._on_gesture_changed)
        root.addWidget(self._gestures)

        root.addStretch()

        # ── Status bar ───────────────────────────────────────────
        self._status = QStatusBar()
        self.setStatusBar(self._status)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_battery)

        # Pulsing dot animation
        self._dot_states = ["●", "◉", "○", "◉"]
        self._dot_idx = 0
        self._dot_timer = QTimer(self)
        self._dot_timer.timeout.connect(self._pulse_dot)
        self._dot_timer.start(600)

        self._status.showMessage("Searching for CMF Buds Pro 2...")

    def _pulse_dot(self):
        self._dot.setText(self._dot_states[self._dot_idx % len(self._dot_states)])
        self._dot_idx += 1

    def on_connected(self):
        self._connected = True
        self._dot_timer.stop()
        self._dot.setText("●")
        self._dot.setStyleSheet("color:#00e676; font-size:11px;")
        self._status.showMessage("Connected  ·  CMF Buds Pro 2")
        self._timer.start(BATTERY_POLL_MS)
        QTimer.singleShot(100, self._load_initial_state)

    def _load_initial_state(self):
        def load():
            try:
                s = get_battery(self._session)
                QTimer.singleShot(0, lambda: self._battery.update_status(s.left, s.right, s.case))
            except Exception:
                pass
            try:
                mode = get_anc(self._session)
                QTimer.singleShot(0, lambda: self._anc.set_mode(mode))
            except Exception:
                pass
            try:
                preset = get_eq(self._session)
                QTimer.singleShot(0, lambda: self._eq.set_preset(preset))
            except Exception:
                pass
            try:
                gm = get_game_mode(self._session)
                QTimer.singleShot(0, lambda: self._game_mode.set_state(gm))
            except Exception:
                pass
            try:
                sp = get_spatial(self._session)
                QTimer.singleShot(0, lambda: self._spatial.set_state(sp))
            except Exception:
                pass
            try:
                ie = get_in_ear(self._session)
                QTimer.singleShot(0, lambda: self._in_ear.set_state(ie))
            except Exception:
                pass
            try:
                enable, level = get_bass(self._session)
                QTimer.singleShot(0, lambda: self._bass.set_state(enable, level))
            except Exception:
                pass
        threading.Thread(target=load, daemon=True).start()

    def _poll_battery(self):
        if not self._connected:
            return
        try:
            s = get_battery(self._session)
            self._battery.update_status(s.left, s.right, s.case)
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
