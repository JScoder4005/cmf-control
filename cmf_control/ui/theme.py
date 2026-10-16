NOTHING_DARK_QSS = """
QWidget { background:#000000; color:#ffffff; font-family:'Space Mono','Courier New',monospace; font-size:12px; }
QScrollArea, QScrollArea>QWidget>QWidget { background:#000000; }
QScrollBar:vertical { background:#000000; width:3px; }
QScrollBar::handle:vertical { background:#1a1a1a; border-radius:2px; min-height:20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QLabel { color:#ffffff; }
QPushButton { background:transparent; color:#555555; border:1px solid #1c1c1c; border-radius:4px; padding:8px 20px; font-family:'Space Mono',monospace; font-size:10px; letter-spacing:2px; }
QPushButton:hover { color:#aaaaaa; border-color:#333333; }
QPushButton:checked { background:#ffffff; color:#000000; border-color:#ffffff; }
QPushButton:disabled { color:#1c1c1c; border-color:#111111; }
QComboBox { background:#0a0a0a; color:#888888; border:1px solid #1c1c1c; border-radius:4px; padding:6px 10px; font-family:'Space Mono',monospace; font-size:10px; letter-spacing:1px; min-width:160px; }
QComboBox:hover { border-color:#333333; color:#cccccc; }
QComboBox::drop-down { border:none; width:24px; }
QComboBox::down-arrow { image:none; }
QComboBox QAbstractItemView { background:#0a0a0a; color:#888888; selection-background-color:#141414; border:1px solid #1c1c1c; }
QSlider::groove:horizontal { background:#1a1a1a; height:2px; border-radius:1px; }
QSlider::handle:horizontal { background:#ffffff; width:12px; height:12px; margin:-5px 0; border-radius:6px; }
QSlider::sub-page:horizontal { background:#ffffff; border-radius:1px; }
QSlider::handle:horizontal:disabled { background:#333333; }
QStatusBar { background:#000000; color:#2a2a2a; font-size:10px; border-top:1px solid #0d0d0d; }
"""
