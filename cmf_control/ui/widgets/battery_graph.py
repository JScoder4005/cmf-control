from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt
import time

LEFT_COLOR = "#FF1744"
RIGHT_COLOR = "#2ECC71"
CASE_COLOR = "#4A90E2"
AXIS_COLOR = "#1f1f1f"
TEXT_COLOR = "#333333"


class BatteryGraph(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._points: list[dict] = []
        self.setMinimumHeight(100)
        self.setMaximumHeight(140)

    def set_points(self, points: list[dict]) -> None:
        self._points = points
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        margin_l, margin_r = 36, 10
        margin_t, margin_b = 8, 18
        plot_w = w - margin_l - margin_r
        plot_h = h - margin_t - margin_b

        # Grid lines at 0%, 50%, 100%
        p.setPen(QPen(QColor(AXIS_COLOR), 1))
        p.setFont(QFont("", 7))
        for pct in (0, 50, 100):
            y = margin_t + plot_h - (pct / 100) * plot_h
            p.drawLine(margin_l, int(y), w - margin_r, int(y))
            p.setPen(QColor(TEXT_COLOR))
            p.drawText(0, int(y) + 4, margin_l - 4, 12, Qt.AlignmentFlag.AlignRight, f"{pct}%")
            p.setPen(QPen(QColor(AXIS_COLOR), 1))

        if not self._points:
            p.setPen(QColor(TEXT_COLOR))
            p.drawText(
                self.rect(), Qt.AlignmentFlag.AlignCenter,
                "NO HISTORY YET — DATA COLLECTS DURING USE"
            )
            p.end()
            return

        now = int(time.time())
        start = now - 24 * 3600
        span = now - start

        def xpos(t: int) -> float:
            return margin_l + ((t - start) / span) * plot_w

        def ypos(v: int) -> float:
            return margin_t + plot_h - (v / 100) * plot_h

        # Plot three series
        for key, color in (("l", LEFT_COLOR), ("r", RIGHT_COLOR), ("c", CASE_COLOR)):
            p.setPen(QPen(QColor(color), 1.5))
            prev = None
            for pt in self._points:
                if pt[key] == 0:
                    prev = None
                    continue
                cx, cy = xpos(pt["t"]), ypos(pt[key])
                if prev is not None:
                    p.drawLine(int(prev[0]), int(prev[1]), int(cx), int(cy))
                prev = (cx, cy)

        # Legend
        p.setFont(QFont("", 7))
        legend_y = h - 10
        x = margin_l
        for label, color in (("L", LEFT_COLOR), ("R", RIGHT_COLOR), ("CASE", CASE_COLOR)):
            p.setPen(QColor(color))
            p.drawText(x, legend_y, f"— {label}")
            x += 50

        # X-axis labels: now, -12h, -24h
        p.setPen(QColor(TEXT_COLOR))
        p.drawText(margin_l - 10, h - 2, "-24h")
        p.drawText(margin_l + plot_w // 2 - 10, h - 2, "-12h")
        p.drawText(w - margin_r - 20, h - 2, "NOW")

        p.end()
