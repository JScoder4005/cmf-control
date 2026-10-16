from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt


class DotMatrixBackground(QWidget):
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor("#0f0f0f"))
        p.setPen(Qt.PenStyle.NoPen)
        spacing = 16
        for x in range(0, self.width() + spacing, spacing):
            for y in range(0, self.height() + spacing, spacing):
                p.drawEllipse(x - 1, y - 1, 2, 2)
        p.end()
