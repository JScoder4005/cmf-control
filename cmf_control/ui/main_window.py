from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QStatusBar, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, QThreadPool, QRunnable, pyqtSlot
from cmf_control.ui.widgets.battery_bar import BatteryBar
from cmf_control.ui.widgets.anc_toggle import ANCToggle
from cmf_control.ui.widgets.eq_picker import EQPicker
from cmf_control.ui.widgets.gesture_map import GestureMap
from cmf_control.bt.session import BTSession
from cmf_control.features.battery import get_battery
from cmf_control.features.anc import get_anc, set_anc
from cmf_control.features.eq import get_eq, set_eq
from cmf_control.features.gestures import get_gestures, set_gesture

BATTERY_POLL_MS = 30_000  # 30s

class MainWindow(QMainWindow):
    def __init__(self, session: BTSession):
        super().__init__()
        self._session = session
        self.setWindowTitle("CMF CONTROL")
        self.setMinimumWidth(520)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(20)

        # Header
        title = QLabel("CMF CONTROL")
        title.setStyleSheet("font-size: 18px; letter-spacing: 4px;")
        subtitle = QLabel("BUDS PRO 2")
        subtitle.setObjectName("subtitle")
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(self._separator())

        # Battery
        root.addWidget(QLabel("BATTERY"))
        self._battery = BatteryBar()
        root.addWidget(self._battery)
        root.addWidget(self._separator())

        # ANC
        root.addWidget(QLabel("NOISE CONTROL"))
        self._anc = ANCToggle()
        self._anc.mode_changed.connect(self._on_anc_changed)
        root.addWidget(self._anc)
        root.addWidget(self._separator())

        # EQ
        root.addWidget(QLabel("SOUND PROFILE"))
        self._eq = EQPicker()
        self._eq.preset_changed.connect(self._on_eq_changed)
        root.addWidget(self._eq)
        root.addWidget(self._separator())

        # Gestures
        root.addWidget(QLabel("TOUCH CONTROLS"))
        self._gestures = GestureMap()
        self._gestures.gesture_changed.connect(self._on_gesture_changed)
        root.addWidget(self._gestures)

        root.addStretch()

        self._status = QStatusBar()
        self.setStatusBar(self._status)

        # Battery poll timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_battery)
        self._timer.start(BATTERY_POLL_MS)

        self._load_initial_state()

    def _separator(self) -> QFrame:
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        return sep

    def _load_initial_state(self):
        try:
            status = get_battery(self._session)
            self._battery.update_status(status.left, status.right, status.case)
            anc_mode = get_anc(self._session)
            self._anc.set_mode(anc_mode)
            eq_preset = get_eq(self._session)
            self._eq.set_preset(eq_preset)
            self._status.showMessage("Connected")
        except Exception as e:
            self._status.showMessage(f"Load failed: {e}")

    def _poll_battery(self):
        try:
            status = get_battery(self._session)
            self._battery.update_status(status.left, status.right, status.case)
        except Exception:
            pass

    def _on_anc_changed(self, mode: int):
        session = self._session
        status = self._status
        def run():
            try:
                set_anc(session, mode)
            except Exception as e:
                status.showMessage(f"ANC error: {e}")
        import threading
        threading.Thread(target=run, daemon=True).start()

    def _on_eq_changed(self, preset: int):
        try:
            set_eq(self._session, preset)
        except Exception as e:
            self._status.showMessage(f"EQ error: {e}")

    def _on_gesture_changed(self, position: int, action: int):
        try:
            set_gesture(self._session, position, action)
        except Exception as e:
            self._status.showMessage(f"Gesture error: {e}")
