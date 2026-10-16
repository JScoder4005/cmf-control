from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal, QPropertyAnimation, QEasingCurve, Qt, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import QSize


class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = False
        self._offset = 0.0
        self._anim = QPropertyAnimation(self, b"offset", self)
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(44, 24)

    def _get_offset(self):
        return self._offset

    def _set_offset(self, val):
        self._offset = val
        self.update()

    offset = pyqtProperty(float, _get_offset, _set_offset)

    def set_state(self, state: bool):
        self._state = state
        self._offset = 1.0 if state else 0.0
        self.update()

    def mousePressEvent(self, e):
        self._state = not self._state
        self._anim.setStartValue(self._offset)
        self._anim.setEndValue(1.0 if self._state else 0.0)
        self._anim.start()
        self.toggled.emit(self._state)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        r = h / 2

        # Track
        track_color = QColor("#ffffff") if self._state else QColor("#1e1e1e")
        border_color = QColor("#ffffff") if self._state else QColor("#333333")
        p.setPen(QPen(border_color, 1))
        p.setBrush(track_color)
        p.drawRoundedRect(0, 0, w, h, r, r)

        # Circle
        pad = 3
        diameter = h - pad * 2
        travel = w - diameter - pad * 2
        x = pad + self._offset * travel
        circle_color = QColor("#000000") if self._state else QColor("#555555")
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(circle_color)
        p.drawEllipse(int(x), pad, diameter, diameter)
        p.end()

    def sizeHint(self):
        return QSize(44, 24)
