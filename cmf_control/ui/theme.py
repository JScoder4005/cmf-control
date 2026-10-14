NOTHING_DARK_QSS = """
QWidget {
    background-color: #0a0a0a;
    color: #ffffff;
    font-family: "Space Mono", "Courier New", monospace;
    font-size: 13px;
}

QMainWindow {
    background-color: #0a0a0a;
}

QLabel {
    color: #ffffff;
}

QLabel#subtitle {
    color: #666666;
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
}

QPushButton {
    background-color: transparent;
    color: #ffffff;
    border: 1px solid #333333;
    border-radius: 14px;
    padding: 6px 16px;
    font-family: "Space Mono", monospace;
    font-size: 11px;
    letter-spacing: 1px;
}

QPushButton:hover {
    border-color: #666666;
}

QPushButton:checked, QPushButton#active {
    background-color: #ffffff;
    color: #000000;
    border-color: #ffffff;
}

QPushButton:disabled {
    color: #333333;
    border-color: #1a1a1a;
}

QComboBox {
    background-color: #111111;
    color: #ffffff;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 4px 8px;
    font-family: "Space Mono", monospace;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #111111;
    color: #ffffff;
    selection-background-color: #222222;
    border: 1px solid #333333;
}

QProgressBar {
    background-color: #111111;
    border: 1px solid #222222;
    border-radius: 3px;
    text-align: center;
    color: #ffffff;
    font-size: 10px;
}

QProgressBar::chunk {
    background-color: #ffffff;
    border-radius: 2px;
}

QFrame#separator {
    background-color: #1a1a1a;
    max-height: 1px;
}

QStatusBar {
    background-color: #050505;
    color: #444444;
    font-size: 10px;
}
"""
