import sys
import threading
import logging
import time
log = logging.getLogger("cmf_control.window")
_WIN_START = time.monotonic()
def _el(): return f"{time.monotonic()-_WIN_START:.2f}s"
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QStatusBar, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from cmf_control.ui.widgets.dot_matrix_background import DotMatrixBackground
from cmf_control.ui.widgets.battery_bar import BatteryBar
from cmf_control.ui.widgets.anc_toggle import ANCToggle
from cmf_control.ui.widgets.eq_picker import EQPicker
from cmf_control.ui.widgets.gesture_map import GestureMap
from cmf_control.ui.widgets.toggle_switch import ToggleSwitch
from cmf_control.ui.widgets.bass_control import BassControl
from cmf_control.ui.widgets.battery_graph import BatteryGraph
from cmf_control.ui.widgets.sleep_timer import SleepTimer
from cmf_control.features import battery_history
from cmf_control.features.sleep_timer import pause_all_players
from cmf_control.bt.session import BTSession
from cmf_control.features.battery import get_battery, is_low_battery
from cmf_control.features.firmware import get_firmware_version
from cmf_control.features.rssi import get_rssi, rssi_to_bars
from cmf_control.features.notify import notify
from cmf_control.features.anc import get_anc, set_anc
from cmf_control.features.eq import get_eq, set_eq
from cmf_control.features.gestures import get_gestures, set_gesture
from cmf_control.features.in_ear import get_in_ear, set_in_ear
from cmf_control.features.game_mode import get_game_mode, set_game_mode
from cmf_control.features.bass import get_bass, set_bass
from cmf_control.features.spatial import get_spatial, set_spatial

BATTERY_POLL_MS = 30_000
RSSI_POLL_MS = 10_000
RED = "#FF1744"
GREEN = "#2ECC71"
SECTION_STYLE = f"color:{RED}; font-size:9px; letter-spacing:4px; background:transparent;"
ROW_STYLE = "color:#555555; font-size:11px; letter-spacing:2px; background:transparent;"


def _sep():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet("background:#111111; max-height:1px; border:none;")
    return f


def _section_label(text):
    lbl = QLabel(text)
    lbl.setStyleSheet(SECTION_STYLE)
    return lbl


class MainWindow(QMainWindow):
    battery_updated = pyqtSignal(int, int, int)  # left, right, case
    battery_full_updated = pyqtSignal(object)  # BatteryStatus with charging flags
    anc_updated = pyqtSignal(int)
    eq_updated = pyqtSignal(int)

    def __init__(self, session: BTSession):
        super().__init__()
        self._session = session
        self._low_battery_notified = False
        self._connected = False
        self.setWindowTitle("CMF Control")
        self.setMinimumWidth(400)
        self.setMaximumWidth(520)

        # Dot matrix as central widget background
        bg = DotMatrixBackground()
        bg_layout = QVBoxLayout(bg)
        bg_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background:transparent;")
        bg_layout.addWidget(scroll)

        self.setCentralWidget(bg)

        container = QWidget()
        container.setStyleSheet("background:transparent;")
        scroll.setWidget(container)
        root = QVBoxLayout(container)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        # Header
        header = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(3)
        name = QLabel("CMF BUDS PRO 2")
        name.setStyleSheet("color:#ffffff; font-size:15px; letter-spacing:4px; background:transparent;")
        brand = QLabel("NOTHING TECHNOLOGY")
        brand.setStyleSheet("color:#1f1f1f; font-size:9px; letter-spacing:3px; background:transparent;")
        left.addWidget(name)
        left.addWidget(brand)

        right_col = QVBoxLayout()
        right_col.setSpacing(3)
        right_col.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._dot = QLabel("●")
        self._dot.setStyleSheet(f"color:#1a1a1a; font-size:13px; background:transparent;")
        self._dot.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._fw_label = QLabel("")
        self._fw_label.setStyleSheet("color:#1f1f1f; font-size:9px; letter-spacing:2px; background:transparent;")
        self._fw_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._rssi_label = QLabel("")
        self._rssi_label.setStyleSheet("color:#1f1f1f; font-size:9px; letter-spacing:2px; background:transparent;")
        self._rssi_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_col.addWidget(self._dot)
        right_col.addWidget(self._rssi_label)
        right_col.addWidget(self._fw_label)

        header.addLayout(left)
        header.addStretch()
        header.addLayout(right_col)
        root.addLayout(header)
        root.addWidget(_sep())

        # Battery
        self._battery = BatteryBar()
        root.addWidget(self._battery)
        root.addWidget(_sep())

        # Battery history graph
        root.addWidget(_section_label("LAST 24H"))
        self._graph = BatteryGraph()
        self._graph.set_points(battery_history.load_last_24h())
        root.addWidget(self._graph)
        root.addWidget(_sep())

        # Noise Control
        root.addWidget(_section_label("NOISE CONTROL"))
        self._anc = ANCToggle()
        self._anc.mode_changed.connect(self._on_anc_changed)
        root.addWidget(self._anc)
        root.addWidget(_sep())

        # Sound Profile
        root.addWidget(_section_label("SOUND PROFILE"))
        self._eq = EQPicker()
        self._eq.preset_changed.connect(self._on_eq_changed)
        root.addWidget(self._eq)
        root.addWidget(_sep())

        # Toggle rows
        root.addWidget(_section_label("SETTINGS"))
        toggles = QVBoxLayout()
        toggles.setSpacing(16)
        toggles.setContentsMargins(0, 4, 0, 0)

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
            lbl.setStyleSheet(ROW_STYLE)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(widget)
            toggles.addLayout(row)

        root.addLayout(toggles)
        root.addWidget(_sep())

        # Bass
        root.addWidget(_section_label("BASS ENHANCE"))
        self._bass = BassControl()
        self._bass.changed.connect(self._on_bass_changed)
        root.addWidget(self._bass)
        root.addWidget(_sep())

        # Sleep timer
        root.addWidget(_section_label("SLEEP TIMER"))
        self._sleep = SleepTimer()
        self._sleep.expired.connect(self._on_sleep_expired)
        root.addWidget(self._sleep)
        root.addWidget(_sep())

        # Touch Controls
        root.addWidget(_section_label("TOUCH CONTROLS"))
        self._gestures = GestureMap()
        self._gestures.gesture_changed.connect(self._on_gesture_changed)
        root.addWidget(self._gestures)

        root.addStretch()

        self._status = QStatusBar()
        self.setStatusBar(self._status)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_battery)

        self._rssi_timer = QTimer(self)
        self._rssi_timer.timeout.connect(self._poll_rssi)

        self._dot_colors = ["#1a1a1a", "#252525", "#333333", "#252525"]
        self._dot_idx = 0
        self._dot_timer = QTimer(self)
        self._dot_timer.timeout.connect(self._pulse_dot)
        self._dot_timer.start(500)

        self._status.showMessage("SEARCHING FOR CMF BUDS PRO 2...")

    def _pulse_dot(self):
        c = self._dot_colors[self._dot_idx % len(self._dot_colors)]
        self._dot.setStyleSheet(f"color:{c}; font-size:13px; background:transparent;")
        self._dot_idx += 1

    def on_connected(self):
        self._connected = True
        self._dot_timer.stop()
        self._dot.setStyleSheet(f"color:{GREEN}; font-size:13px; background:transparent;")
        self._status.showMessage("CONNECTED  ·  CMF BUDS PRO 2")
        self._fw_label.setText("FW ...")
        self._rssi_label.setText("...")
        self._timer.start(BATTERY_POLL_MS)
        self._rssi_timer.start(RSSI_POLL_MS)
        QTimer.singleShot(0, self._poll_rssi)
        QTimer.singleShot(0, self._load_initial_state)

    def on_disconnected(self, searching: bool = False):
        self._connected = False
        self._low_battery_notified = False
        self._timer.stop()
        self._rssi_timer.stop()
        self._battery.update_status(0, 0, 0)
        self._fw_label.setText("")
        self._rssi_label.setText("")
        self._dot_timer.start(500)
        if searching:
            self._status.showMessage("SEARCHING FOR CMF BUDS PRO 2...")
        else:
            self._status.showMessage("NOT CONNECTED  ·  BUDS IN CASE / OUT OF RANGE")

    def _load_initial_state(self):
        def load():
            log.info(f"[+{_el()}] load_initial_state: begin")
            try:
                s = get_battery(self._session)
                log.info(f"[+{_el()}] battery L={s.left}{'c' if s.left_charging else ''} R={s.right}{'c' if s.right_charging else ''} C={s.case}{'c' if s.case_charging else ''}")
                def ui_update():
                    self._battery.update_status(
                        s.left, s.right, s.case,
                        s.left_charging, s.right_charging, s.case_charging,
                    )
                QTimer.singleShot(0, ui_update)
                QTimer.singleShot(0, lambda: self.battery_updated.emit(s.left, s.right, s.case))
                QTimer.singleShot(0, lambda: self.battery_full_updated.emit(s))
                battery_history.record(s.left, s.right, s.case)
                QTimer.singleShot(0, lambda: self._graph.set_points(battery_history.load_last_24h()))
            except Exception as e:
                log.error(f"battery FAIL: {e}")
            try:
                mode = get_anc(self._session, timeout=1.5)
                log.info(f"anc OK mode={mode}")
                QTimer.singleShot(0, lambda m=mode: self._anc.set_mode(m))
                QTimer.singleShot(0, lambda m=mode: self.anc_updated.emit(m))
            except Exception as e:
                log.error(f"anc FAIL: {e}")
            try:
                preset = get_eq(self._session, timeout=1.5)
                log.info(f"eq OK preset={preset}")
                QTimer.singleShot(0, lambda p=preset: self._eq.set_preset(p))
                QTimer.singleShot(0, lambda p=preset: self.eq_updated.emit(p))
            except Exception as e:
                log.error(f"eq FAIL: {e}")
            try:
                gm = get_game_mode(self._session, timeout=1.5)
                QTimer.singleShot(0, lambda: self._game_mode.set_state(gm))
            except Exception:
                pass
            try:
                sp = get_spatial(self._session, timeout=1.5)
                QTimer.singleShot(0, lambda: self._spatial.set_state(sp))
            except Exception:
                pass
            try:
                ie = get_in_ear(self._session, timeout=1.5)
                QTimer.singleShot(0, lambda: self._in_ear.set_state(ie))
            except Exception:
                pass
            try:
                enable, level = get_bass(self._session, timeout=1.5)
                QTimer.singleShot(0, lambda: self._bass.set_state(enable, level))
            except Exception:
                pass
            try:
                fw = get_firmware_version(self._session, timeout=1.5)
                log.info(f"firmware: {fw!r}")
                QTimer.singleShot(0, lambda f=fw: self._fw_label.setText(f"FW {f}"))
            except Exception as e:
                log.error(f"firmware FAIL: {e}")
        if sys.platform == "darwin":
            # mac IOBluetooth only delivers response callbacks to the main
            # thread's run loop — a background thread here would hang every
            # get_*() call until RECV_TIMEOUT, silently (caught above).
            load()
        else:
            threading.Thread(target=load, daemon=True).start()

    def _poll_battery(self):
        if not self._connected:
            return
        try:
            s = get_battery(self._session)
            self._battery.update_status(
                s.left, s.right, s.case,
                s.left_charging, s.right_charging, s.case_charging,
            )
            self.battery_updated.emit(s.left, s.right, s.case)
            self.battery_full_updated.emit(s)
            battery_history.record(s.left, s.right, s.case)
            self._graph.set_points(battery_history.load_last_24h())
            self._check_low_battery(s)
        except Exception:
            pass

    def _poll_rssi(self):
        if not self._connected:
            return
        def run():
            rssi = get_rssi(self._session.address)
            bars = rssi_to_bars(rssi)
            text = f"{bars}  {rssi} dBm" if rssi is not None else ""
            QTimer.singleShot(0, lambda: self._rssi_label.setText(text))
        threading.Thread(target=run, daemon=True).start()

    def _check_low_battery(self, status):
        if is_low_battery(status):
            if not self._low_battery_notified:
                self._low_battery_notified = True
                notify("CMF Control", f"Earbud battery low — {min(v for v in (status.left, status.right) if v > 0)}%")
        else:
            self._low_battery_notified = False

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

    def _on_sleep_expired(self):
        def run():
            n = pause_all_players()
            log.info(f"sleep timer expired, paused {n} player(s)")
        threading.Thread(target=run, daemon=True).start()

    def _on_gesture_changed(self, device: int, button_id: int, gesture_type: int, action: int):
        s = self._session
        def run():
            try: set_gesture(s, device, button_id, gesture_type, action)
            except Exception: pass
        self._bg(run)
