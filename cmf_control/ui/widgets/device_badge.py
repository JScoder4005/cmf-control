from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QFont, QFontMetricsF
from PyQt6.QtCore import Qt


class DeviceBadge(QWidget):
    """Big dot-matrix 'CMF' typographic mark, Nothing-authentic."""

    def __init__(self, size: int = 96, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self._size

        # Dot grid background box
        p.setBrush(QColor("#0f0f0f"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, s, s, 10, 10)

        # Dot matrix pattern inside
        p.setBrush(QColor("#1f1f1f"))
        step = max(6, s // 14)
        for x in range(step // 2, s, step):
            for y in range(step // 2, s, step):
                p.drawEllipse(x - 1, y - 1, 2, 2)

        # Red accent dot top-left
        p.setBrush(QColor("#FF1744"))
        p.drawEllipse(10, 10, 5, 5)

        # Big "CMF" letters
        p.setPen(QColor("#ffffff"))
        font = QFont("Space Mono", int(s * 0.28))
        font.setBold(True)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, s * 0.02)
        p.setFont(font)
        fm = QFontMetricsF(font)
        text = "CMF"
        text_w = fm.horizontalAdvance(text)
        text_h = fm.ascent()
        p.drawText(
            int((s - text_w) / 2),
            int((s + text_h) / 2 - fm.descent() * 0.3),
            text,
        )

        # "BUDS PRO 2" subtitle
        p.setPen(QColor("#555555"))
        sub_font = QFont("Space Mono", int(s * 0.085))
        sub_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        p.setFont(sub_font)
        sub_fm = QFontMetricsF(sub_font)
        sub = "BUDS PRO 2"
        sub_w = sub_fm.horizontalAdvance(sub)
        p.drawText(
            int((s - sub_w) / 2),
            int(s - 12),
            sub,
        )

        p.end()
