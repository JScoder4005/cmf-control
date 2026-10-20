from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QFont, QIcon, QPolygonF
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPointF
from cmf_control.features.mpris import NowPlaying

RED = "#FF1744"
WHITE = "#ffffff"
GREY = "#555555"
ART_SIZE = 56
BTN_SIZE = 28


def _elide(text: str, max_chars: int) -> str:
    return text if len(text) <= max_chars else text[: max_chars - 1] + "…"


def _placeholder_art() -> QPixmap:
    pix = QPixmap(ART_SIZE, ART_SIZE)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(QColor("#1a1a1a")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(0, 0, ART_SIZE, ART_SIZE, 4, 4)
    # dot-matrix inside
    p.setBrush(QBrush(QColor("#2a2a2a")))
    for x in range(6, ART_SIZE, 7):
        for y in range(6, ART_SIZE, 7):
            p.drawEllipse(x - 1, y - 1, 2, 2)
    p.end()
    return pix


def _make_btn_pix(draw, color: str) -> QPixmap:
    scale = 2
    size = BTN_SIZE
    pix = QPixmap(size * scale, size * scale)
    pix.setDevicePixelRatio(scale)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(QBrush(QColor(color)))
    draw(p, size)
    p.end()
    return pix


def _draw_play(p: QPainter, s: int):
    cx, cy = s / 2, s / 2
    r = s / 4
    pts = [QPointF(cx - r * 0.6, cy - r), QPointF(cx - r * 0.6, cy + r), QPointF(cx + r, cy)]
    p.drawPolygon(QPolygonF(pts))


def _draw_pause(p: QPainter, s: int):
    cx, cy = s / 2, s / 2
    w, h = s / 10, s / 3
    p.drawRect(int(cx - 1.8 * w), int(cy - h / 2), int(1.2 * w), int(h))
    p.drawRect(int(cx + 0.6 * w), int(cy - h / 2), int(1.2 * w), int(h))


def _draw_next(p: QPainter, s: int):
    cx, cy = s / 2, s / 2
    r = s / 5
    tri1 = QPolygonF([QPointF(cx - r * 1.3, cy - r), QPointF(cx - r * 1.3, cy + r), QPointF(cx, cy)])
    tri2 = QPolygonF([QPointF(cx, cy - r), QPointF(cx, cy + r), QPointF(cx + r * 1.3, cy)])
    p.drawPolygon(tri1)
    p.drawPolygon(tri2)


def _draw_prev(p: QPainter, s: int):
    cx, cy = s / 2, s / 2
    r = s / 5
    tri1 = QPolygonF([QPointF(cx + r * 1.3, cy - r), QPointF(cx + r * 1.3, cy + r), QPointF(cx, cy)])
    tri2 = QPolygonF([QPointF(cx, cy - r), QPointF(cx, cy + r), QPointF(cx - r * 1.3, cy)])
    p.drawPolygon(tri1)
    p.drawPolygon(tri2)


class NowPlayingWidget(QWidget):
    play_pause = pyqtSignal()
    next_track = pyqtSignal()
    prev_track = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state: NowPlaying | None = None
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # Album art
        self._art = QLabel()
        self._art.setFixedSize(ART_SIZE, ART_SIZE)
        self._art.setPixmap(_placeholder_art())
        self._art.setStyleSheet("background:transparent;")
        root.addWidget(self._art)

        # Text column
        col = QVBoxLayout()
        col.setSpacing(2)
        self._title = QLabel("NOT PLAYING")
        self._title.setStyleSheet(f"color:{GREY}; font-size:12px; letter-spacing:2px; background:transparent;")
        self._artist = QLabel("")
        self._artist.setStyleSheet(f"color:#333333; font-size:10px; letter-spacing:2px; background:transparent;")
        col.addWidget(self._title)
        col.addWidget(self._artist)
        col.addStretch()
        root.addLayout(col, 1)

        # Buttons column
        btn_row = QHBoxLayout()
        btn_row.setSpacing(2)
        self._btn_prev = self._make_btn(_draw_prev)
        self._btn_pp = self._make_btn(_draw_play)
        self._btn_next = self._make_btn(_draw_next)
        self._btn_prev.clicked.connect(self.prev_track)
        self._btn_pp.clicked.connect(self.play_pause)
        self._btn_next.clicked.connect(self.next_track)
        btn_row.addWidget(self._btn_prev)
        btn_row.addWidget(self._btn_pp)
        btn_row.addWidget(self._btn_next)
        root.addLayout(btn_row)

        self._set_buttons_enabled(False)

    def _make_btn(self, draw) -> QPushButton:
        btn = QPushButton()
        btn.setFixedSize(BTN_SIZE, BTN_SIZE)
        btn.setIcon(QIcon(_make_btn_pix(draw, GREY)))
        btn.setIconSize(QSize(BTN_SIZE, BTN_SIZE))
        btn.setStyleSheet("""
            QPushButton { background:transparent; border:1px solid #1c1c1c; border-radius:14px; }
            QPushButton:hover:enabled { border-color:#333333; background:#111111; }
            QPushButton:disabled { border-color:#111111; }
        """)
        btn._drawer = draw
        return btn

    def _set_buttons_enabled(self, on: bool):
        for btn in (self._btn_prev, self._btn_pp, self._btn_next):
            btn.setEnabled(on)
            color = WHITE if on else GREY
            btn.setIcon(QIcon(_make_btn_pix(btn._drawer, color)))

    def update_state(self, state: NowPlaying):
        self._state = state
        if not state.has_player:
            self._title.setText("NOT PLAYING")
            self._title.setStyleSheet(f"color:{GREY}; font-size:12px; letter-spacing:2px; background:transparent;")
            self._artist.setText("")
            self._art.setPixmap(_placeholder_art())
            self._set_buttons_enabled(False)
            return
        title = state.title or "UNKNOWN TITLE"
        artist = state.artist or state.album or ""
        self._title.setText(_elide(title.upper(), 42))
        self._title.setStyleSheet(f"color:{WHITE}; font-size:12px; letter-spacing:2px; background:transparent;")
        self._artist.setText(_elide(artist.upper(), 48))
        self._set_buttons_enabled(True)
        # Swap play/pause icon
        drawer = _draw_pause if state.status == "Playing" else _draw_play
        self._btn_pp._drawer = drawer
        self._btn_pp.setIcon(QIcon(_make_btn_pix(drawer, WHITE)))
        # Art
        if state.art_path:
            pm = QPixmap(state.art_path)
            if not pm.isNull():
                pm = pm.scaled(
                    ART_SIZE, ART_SIZE,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._art.setPixmap(pm)
                return
        self._art.setPixmap(_placeholder_art())
