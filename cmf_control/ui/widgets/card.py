from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt

CARD_BG = "#141414"
TITLE_COLOR = "#FF1744"
TITLE_STYLE = f"color:{TITLE_COLOR}; font-size:9px; letter-spacing:4px; background:transparent;"


class Card(QFrame):
    """Rounded dark card container, MiBuds-inspired."""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            Card {{
                background:{CARD_BG};
                border:1px solid #1f1f1f;
                border-radius:12px;
            }}
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(18, 14, 18, 16)
        self._layout.setSpacing(10)

        if title:
            self._title_label = QLabel(title.upper())
            self._title_label.setStyleSheet(TITLE_STYLE)
            self._layout.addWidget(self._title_label)

    def add(self, widget: QWidget):
        self._layout.addWidget(widget)

    def add_layout(self, layout):
        self._layout.addLayout(layout)
