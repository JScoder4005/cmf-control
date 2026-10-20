from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QPointF
from cmf_control.features.anc import ANC_MODES


def _draw_off(p: QPainter):
    p.drawEllipse(QPointF(12, 12), 9, 9)
    p.drawLine(QPointF(5.6, 5.6), QPointF(18.4, 18.4))


def _draw_transparency(p: QPainter):
    # Ear outline (lucide-style)
    p.drawEllipse(QPointF(12, 11), 6, 7)
    p.drawEllipse(QPointF(12, 11), 2.5, 2.5)
    p.drawLine(QPointF(9, 20), QPointF(13, 20))


def _draw_bars(p: QPainter, heights: list[tuple[int, int]]):
    # heights: list of (y_top, y_bot) for 5 bars
    xs = [3, 7, 11, 15, 19]
    for x, (y1, y2) in zip(xs, heights):
        p.drawLine(QPointF(x, y1), QPointF(x, y2))


def _draw_light(p: QPainter):
    _draw_bars(p, [(11, 13), (9, 15), (10, 14), (8, 16), (6, 18)])


def _draw_medium(p: QPainter):
    _draw_bars(p, [(10, 14), (7, 17), (4, 20), (7, 17), (10, 14)])


def _draw_max(p: QPainter):
    # Shield with checkmark
    p.drawLine(QPointF(12, 2), QPointF(4, 5))
    p.drawLine(QPointF(4, 5), QPointF(4, 12))
    p.drawLine(QPointF(4, 12), QPointF(12, 22))
    p.drawLine(QPointF(12, 22), QPointF(20, 12))
    p.drawLine(QPointF(20, 12), QPointF(20, 5))
    p.drawLine(QPointF(20, 5), QPointF(12, 2))
    p.drawLine(QPointF(9, 12), QPointF(11, 14))
    p.drawLine(QPointF(11, 14), QPointF(15, 10))


DRAWERS = {
    0x05: _draw_off,
    0x07: _draw_transparency,
    0x03: _draw_light,
    0x02: _draw_medium,
    0x01: _draw_max,
}


def _make_icon(mode: int, color: str, size: int = 22) -> QPixmap:
    scale = 2  # retina sharp
    pix = QPixmap(size * scale, size * scale)
    pix.setDevicePixelRatio(scale)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(1.8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    # Our drawers assume 24x24 viewBox but canvas is `size`; translate accordingly
    p.scale(size / 24, size / 24)
    drawer = DRAWERS.get(mode, _draw_off)
    drawer(p)
    p.end()
    return pix


class ANCToggle(QWidget):
    mode_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self._buttons: dict[int, QPushButton] = {}
        self._icons: dict[int, tuple[QPixmap, QPixmap]] = {}

        modes = list(ANC_MODES.items())
        for i, (mode, label) in enumerate(modes):
            icon_inactive = _make_icon(mode, "#777777")
            icon_active = _make_icon(mode, "#000000")
            self._icons[mode] = (icon_inactive, icon_active)

            btn = QPushButton(label.upper())
            btn.setIcon(QIcon(icon_inactive))
            btn.setIconSize(QSize(22, 22))
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, m=mode: self._on_click(m))

            if len(modes) == 1:
                radius = "border-radius:4px;"
            elif i == 0:
                radius = "border-radius:4px 0 0 4px; border-right:none;"
            elif i == len(modes) - 1:
                radius = "border-radius:0 4px 4px 0;"
            else:
                radius = "border-radius:0; border-right:none;"

            btn.setStyleSheet(f"""
                QPushButton {{ {radius} border:1px solid #1c1c1c; background:transparent;
                    color:#555555; padding:10px 10px; font-family:'Space Mono',monospace;
                    font-size:9px; letter-spacing:1px; text-align:center; }}
                QPushButton:hover {{ color:#aaaaaa; border-color:#333333; }}
                QPushButton:checked {{ background:#ffffff; color:#000000; border-color:#ffffff; }}
            """)

            layout.addWidget(btn)
            self._buttons[mode] = btn

    def _on_click(self, mode: int):
        self.set_mode(mode)
        self.mode_changed.emit(mode)

    def set_mode(self, mode: int):
        for m, btn in self._buttons.items():
            is_active = (m == mode)
            btn.setChecked(is_active)
            inactive, active = self._icons[m]
            btn.setIcon(QIcon(active if is_active else inactive))
