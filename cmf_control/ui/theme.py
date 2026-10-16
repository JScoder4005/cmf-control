NOTHING_DARK_QSS = """
QWidget {
    background-color: #0d0d0d;
    color: #f0f0f0;
    font-family: "Space Mono", "Courier New", monospace;
    font-size: 13px;
}

QMainWindow, QScrollArea, QScrollArea > QWidget > QWidget {
    background-color: #0d0d0d;
}

QScrollBar:vertical {
    background: #0d0d0d;
    width: 4px;
    border-radius: 2px;
}
QScrollBar::handle:vertical {
    background: #2a2a2a;
    border-radius: 2px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QLabel {
    color: #f0f0f0;
}

QLabel#section {
    color: #555555;
    font-size: 10px;
    letter-spacing: 3px;
}

QLabel#device-name {
    color: #ffffff;
    font-size: 20px;
    letter-spacing: 5px;
    font-weight: bold;
}

QLabel#status-dot {
    font-size: 10px;
}

QPushButton {
    background-color: transparent;
    color: #aaaaaa;
    border: 1px solid #252525;
    border-radius: 16px;
    padding: 7px 18px;
    font-family: "Space Mono", monospace;
    font-size: 10px;
    letter-spacing: 1px;
}

QPushButton:hover {
    border-color: #444444;
    color: #ffffff;
}

QPushButton:checked {
    background-color: #ffffff;
    color: #000000;
    border-color: #ffffff;
}

QPushButton:disabled {
    color: #2a2a2a;
    border-color: #1a1a1a;
}

QComboBox {
    background-color: #141414;
    color: #cccccc;
    border: 1px solid #252525;
    border-radius: 8px;
    padding: 5px 10px;
    font-family: "Space Mono", monospace;
    font-size: 10px;
    min-width: 140px;
}

QComboBox:hover {
    border-color: #444444;
}

QComboBox::drop-down { border: none; width: 20px; }
QComboBox::down-arrow { image: none; width: 0; }

QComboBox QAbstractItemView {
    background-color: #141414;
    color: #cccccc;
    selection-background-color: #222222;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    padding: 2px;
}

QProgressBar {
    background-color: #141414;
    border: none;
    border-radius: 3px;
    max-height: 4px;
}

QProgressBar::chunk {
    background-color: #ffffff;
    border-radius: 3px;
}

QFrame#separator {
    background-color: #161616;
    max-height: 1px;
    margin: 2px 0;
}

QFrame#card {
    background-color: #111111;
    border: 1px solid #1e1e1e;
    border-radius: 12px;
}

QSlider::groove:horizontal {
    background: #252525;
    height: 3px;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    width: 14px;
    height: 14px;
    margin: -6px 0;
    border-radius: 7px;
}

QSlider::sub-page:horizontal {
    background: #ffffff;
    border-radius: 2px;
}

QStatusBar {
    background-color: #080808;
    color: #333333;
    font-size: 10px;
    border-top: 1px solid #161616;
}
"""
