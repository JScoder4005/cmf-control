from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from PyQt6.QtCore import Qt, QPointF, QRectF


class DeviceBadge(QWidget):
    """Nothing-authentic earbuds render: filled dark body + white outline + red accent."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(64, 64)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        outline = QPen(QColor("#ffffff"))
        outline.setWidthF(1.8)
        outline.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        outline.setCapStyle(Qt.PenCapStyle.RoundCap)

        for cx in (18, 46):  # left bud, right bud
            # Bud head
            p.setPen(outline)
            p.setBrush(QBrush(QColor("#1a1a1a")))
            p.drawEllipse(QPointF(cx, 24), 11, 15)
            # Driver circle
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor("#ffffff")))
            p.drawEllipse(QPointF(cx, 24), 4, 4)
            p.setBrush(QBrush(QColor("#0a0a0a")))
            p.drawEllipse(QPointF(cx, 24), 2.2, 2.2)
            # Stem
            p.setPen(outline)
            p.setBrush(QBrush(QColor("#1a1a1a")))
            p.drawRoundedRect(QRectF(cx - 3.5, 38, 7, 16), 3, 3)
            # Red Nothing-accent dot at stem bottom
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor("#FF1744")))
            p.drawEllipse(QPointF(cx, 50), 1.3, 1.3)

        p.end()
