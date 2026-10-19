from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPixmap
from PyQt6.QtCore import Qt


class DotMatrixBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cache: QPixmap | None = None
        self._cache_size = (0, 0)

    def paintEvent(self, e):
        w, h = self.width(), self.height()
        if self._cache is None or self._cache_size != (w, h):
            self._cache = QPixmap(w, h)
            self._cache.fill(Qt.GlobalColor.transparent)
            p = QPainter(self._cache)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setBrush(QColor("#0f0f0f"))
            p.setPen(Qt.PenStyle.NoPen)
            spacing = 16
            for x in range(0, w + spacing, spacing):
                for y in range(0, h + spacing, spacing):
                    p.drawEllipse(x - 1, y - 1, 2, 2)
            p.end()
            self._cache_size = (w, h)
        p = QPainter(self)
        p.drawPixmap(0, 0, self._cache)
        p.end()
