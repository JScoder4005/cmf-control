NOTHING_DARK_QSS = """
QWidget { background:#000000; color:#ffffff; font-family:'Space Mono','Courier New',monospace; font-size:12px; }
QScrollArea, QScrollArea>QWidget>QWidget { background:transparent; }
QScrollBar:vertical { background:transparent; width:3px; margin:0; }
QScrollBar::handle:vertical { background:#1a1a1a; border-radius:1px; min-height:30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QLabel { background:transparent; color:#ffffff; }
QPushButton { background:transparent; color:#444444; border:1px solid #1a1a1a; border-radius:0px; padding:9px 16px; font-family:'Space Mono',monospace; font-size:10px; letter-spacing:2px; }
QPushButton:hover { color:#cccccc; border-color:#444444; }
QPushButton:checked { background:#ffffff; color:#000000; border-color:#ffffff; }
QPushButton:disabled { color:#1a1a1a; border-color:#111111; }
QComboBox { background:#000000; color:#555555; border:1px solid #1a1a1a; border-radius:0px; padding:7px 10px; font-family:'Space Mono',monospace; font-size:10px; letter-spacing:1px; min-width:150px; }
QComboBox:hover { border-color:#333333; color:#aaaaaa; }
QComboBox::drop-down { border:none; width:20px; }
QComboBox::down-arrow { image:none; }
QComboBox QAbstractItemView { background:#0a0a0a; color:#888888; selection-background-color:#111111; border:1px solid #1a1a1a; outline:none; }
QSlider::groove:horizontal { background:#1a1a1a; height:1px; }
QSlider::handle:horizontal { background:#ffffff; width:10px; height:10px; margin:-5px 0; border-radius:5px; }
QSlider::sub-page:horizontal { background:#ffffff; height:1px; }
QSlider::handle:horizontal:disabled { background:#2a2a2a; }
QStatusBar { background:#000000; color:#1f1f1f; font-size:10px; letter-spacing:1px; border-top:1px solid #0f0f0f; }
"""
