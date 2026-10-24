from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QPointF, QRectF, QSize
from cmf_control.features.custom_eq import GAIN_MIN, GAIN_MAX

BANDS = ("BASS", "MID", "TREBLE")
SEND_DEBOUNCE_MS = 250

DOT = 6          # dot diameter
PITCH = 12       # vertical distance between dot centres
HANDLE = 10      # diameter of the dot marking the current gain
STEPS = GAIN_MAX - GAIN_MIN + 1

LIT = QColor("#ffffff")
DIM = QColor("#2a2a2a")
DIM_HOVER = QColor("#3a3a3a")
AXIS = QColor("#242424")
ZERO_RING = QColor("#5a5a5a")
FOCUS = QColor("#6a6a6a")
SCALE = QColor("#4a4a4a")


class DotFader(QWidget):
    """One EQ band as a column of dots, -6 dB at the bottom, +6 dB at the top.
    Dots light from the 0 dB axis toward the current gain. Drag, click,
    scroll, or use arrow keys (Home resets to 0)."""
    valueChanged = pyqtSignal(int)

    def __init__(self, name: str, show_scale: bool = False, parent=None):
        super().__init__(parent)
        self._show_scale = show_scale
        self._value = 0
        self._hover = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(f"{name.title()} gain")
        self.setMinimumWidth(40)
        self.setFixedHeight(STEPS * PITCH + 8)

    def sizeHint(self) -> QSize:
        return QSize(60, STEPS * PITCH + 8)

    def value(self) -> int:
        return self._value

    def setValue(self, v: int):
        v = max(GAIN_MIN, min(GAIN_MAX, int(v)))
        if v == self._value:
            return
        self._value = v
        self.update()
        if not self.signalsBlocked():
            self.valueChanged.emit(v)

    def _y_for(self, v: int) -> float:
        top = (self.height() - (STEPS - 1) * PITCH) / 2
        return top + (GAIN_MAX - v) * PITCH

    def _value_at(self, y: float) -> int:
        top = (self.height() - (STEPS - 1) * PITCH) / 2
        return GAIN_MAX - round((y - top) / PITCH)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = self.width() / 2
        y0 = self._y_for(0)

        # 0 dB axis spans the full width so adjacent faders read as one line
        p.setPen(QPen(AXIS, 1))
        p.drawLine(QPointF(0, y0), QPointF(self.width(), y0))

        lo, hi = sorted((0, self._value))
        dim = DIM_HOVER if self._hover else DIM
        p.setPen(Qt.PenStyle.NoPen)
        for v in range(GAIN_MIN, GAIN_MAX + 1):
            y = self._y_for(v)
            lit = lo <= v <= hi and (v != 0 or self._value == 0)
            if v == self._value:
                p.setBrush(LIT)
                p.drawEllipse(QPointF(cx, y), HANDLE / 2, HANDLE / 2)
            elif lit:
                p.setBrush(LIT)
                p.drawEllipse(QPointF(cx, y), DOT / 2, DOT / 2)
            elif v == 0:
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(ZERO_RING, 1))
                p.drawEllipse(QPointF(cx, y), DOT / 2, DOT / 2)
                p.setPen(Qt.PenStyle.NoPen)
            else:
                p.setBrush(dim)
                p.drawEllipse(QPointF(cx, y), DOT / 2, DOT / 2)

        if self._show_scale:
            f = QFont("Space Mono")
            f.setPixelSize(9)
            p.setFont(f)
            p.setPen(SCALE)
            for v, txt in ((GAIN_MAX, "+6"), (0, "0"), (GAIN_MIN, "−6")):
                y = self._y_for(v)
                p.drawText(QRectF(self.width() - 26, y - 7, 24, 14),
                           Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, txt)

        if self.hasFocus():
            # Corner brackets around the column
            p.setPen(QPen(FOCUS, 1))
            x1, x2 = cx - 12, cx + 12
            y1, y2 = 1, self.height() - 1
            for x, dx in ((x1, 5), (x2, -5)):
                p.drawLine(QPointF(x, y1), QPointF(x + dx, y1))
                p.drawLine(QPointF(x, y1), QPointF(x, y1 + 5))
                p.drawLine(QPointF(x, y2), QPointF(x + dx, y2))
                p.drawLine(QPointF(x, y2), QPointF(x, y2 - 5))
        p.end()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.setValue(self._value_at(e.position().y()))

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.MouseButton.LeftButton:
            self.setValue(self._value_at(e.position().y()))

    def mouseDoubleClickEvent(self, _e):
        self.setValue(0)

    def wheelEvent(self, e):
        step = 1 if e.angleDelta().y() > 0 else -1 if e.angleDelta().y() < 0 else 0
        self.setValue(self._value + step)
        e.accept()

    def keyPressEvent(self, e):
        k = e.key()
        if k in (Qt.Key.Key_Up, Qt.Key.Key_Right):
            self.setValue(self._value + 1)
        elif k in (Qt.Key.Key_Down, Qt.Key.Key_Left):
            self.setValue(self._value - 1)
        elif k == Qt.Key.Key_PageUp or k == Qt.Key.Key_End:
            self.setValue(GAIN_MAX)
        elif k == Qt.Key.Key_PageDown:
            self.setValue(GAIN_MIN)
        elif k in (Qt.Key.Key_Home, Qt.Key.Key_0):
            self.setValue(0)
        else:
            super().keyPressEvent(e)

    def enterEvent(self, _e):
        self._hover = True
        self.update()

    def leaveEvent(self, _e):
        self._hover = False
        self.update()

    def focusInEvent(self, e):
        self.update()
        super().focusInEvent(e)

    def focusOutEvent(self, e):
        self.update()
        super().focusOutEvent(e)


class CustomEQ(QWidget):
    """Bass / mid / treble dot faders. Emits changed(bass, mid, treble)."""
    changed = pyqtSignal(int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(10)

        cols = QHBoxLayout()
        cols.setSpacing(0)
        self._faders: list[DotFader] = []
        self._readouts: list[QLabel] = []
        for name in BANDS:
            col = QVBoxLayout()
            col.setSpacing(6)
            fader = DotFader(name, show_scale=(name == BANDS[-1]))
            fader.valueChanged.connect(self._on_change)

            readout = QLabel(_fmt(0))
            readout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            f = QFont("Space Mono")
            f.setPixelSize(18)
            readout.setFont(f)
            readout.setStyleSheet("color:#ffffff;")

            band = QLabel(name)
            band.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            band.setStyleSheet("color:#5a5a5a; font-size:9px; letter-spacing:3px;")

            col.addWidget(fader)
            col.addWidget(readout)
            col.addWidget(band)
            cols.addLayout(col, 1)
            self._faders.append(fader)
            self._readouts.append(readout)

        layout.addLayout(cols)

        footer = QHBoxLayout()
        hint = QLabel("Saved on the buds")
        hint.setStyleSheet("color:#4a4a4a; font-size:10px;")
        self._flat = QPushButton("RESET TO FLAT")
        self._flat.setCursor(Qt.CursorShape.PointingHandCursor)
        self._flat.setStyleSheet(
            "QPushButton { padding:6px 10px; font-size:9px; letter-spacing:2px; border-radius:4px;"
            " color:#777777; border-color:#2a2a2a; }"
            "QPushButton:hover { color:#cccccc; border-color:#444444; }"
            "QPushButton:disabled { color:#2e2e2e; border-color:#1f1f1f; }")
        self._flat.clicked.connect(lambda: self.set_values(0, 0, 0, emit=True))
        self._flat.setEnabled(False)
        footer.addWidget(hint)
        footer.addStretch()
        footer.addWidget(self._flat)
        layout.addLayout(footer)

        # Coalesce drags into one write; the buds don't need every tick.
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(SEND_DEBOUNCE_MS)
        self._debounce.timeout.connect(lambda: self.changed.emit(*self.values()))

    def values(self) -> tuple[int, int, int]:
        return tuple(f.value() for f in self._faders)

    def _refresh_labels(self):
        for f, lbl in zip(self._faders, self._readouts):
            lbl.setText(_fmt(f.value()))
        self._flat.setEnabled(any(self.values()))

    def _on_change(self, _v: int):
        self._refresh_labels()
        self._debounce.start()

    def set_values(self, bass: int, mid: int, treble: int, emit: bool = False):
        """Update faders; from the device (emit=False) nothing is echoed back."""
        for f, v in zip(self._faders, (bass, mid, treble)):
            f.blockSignals(True)
            f.setValue(v)
            f.blockSignals(False)
        self._refresh_labels()
        if emit:
            self._debounce.start()


def _fmt(v: int) -> str:
    return f"+{v}" if v > 0 else "0" if v == 0 else f"−{-v}"
