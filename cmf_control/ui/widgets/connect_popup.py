from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QPoint
from PyQt6.QtGui import QPainter, QColor
from cmf_control.ui.widgets.battery_bar import BatteryBar

RED = "#FF1744"
HOLD_MS = 3500
SLIDE_MS = 350


class ConnectPopup(QWidget):
    """AirPods-style slide-down-from-top notification — shown on reconnect, not on every launch."""

    def __init__(self):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(320, 120)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)

        header = QHBoxLayout()
        name = QLabel("CMF BUDS PRO 2")
        name.setStyleSheet("color:#ffffff; font-size:12px; letter-spacing:3px; background:transparent;")
        dot = QLabel("●")
        dot.setStyleSheet(f"color:{RED}; font-size:11px; background:transparent;")
        header.addWidget(name)
        header.addStretch()
        header.addWidget(dot)
        root.addLayout(header)

        self._battery = BatteryBar()
        root.addWidget(self._battery)

        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self._slide_up)

        self._anim = None  # kept alive while animating

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 235))
        painter.setPen(QColor(RED))
        painter.drawLine(0, 0, self.width(), 0)

    def show_with(self, left: int, right: int, case: int):
        self._battery.update_status(left, right, case)

        screen = self.screen() or self.window().screen()
        geo = screen.availableGeometry() if screen else None
        x = geo.center().x() - self.width() // 2 if geo else 100
        rest_y = (geo.top() if geo else 0) + 8
        start_y = rest_y - self.height() - 20

        self.move(x, start_y)
        self.show()
        self.raise_()

        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(SLIDE_MS)
        self._anim.setStartValue(QPoint(x, start_y))
        self._anim.setEndValue(QPoint(x, rest_y))
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

        self._dismiss_timer.start(HOLD_MS)

    def _slide_up(self):
        x = self.x()
        start_y = self.y()
        end_y = start_y - self.height() - 20

        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(SLIDE_MS)
        self._anim.setStartValue(QPoint(x, start_y))
        self._anim.setEndValue(QPoint(x, end_y))
        self._anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._anim.finished.connect(self.hide)
        self._anim.start()
