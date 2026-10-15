#!/usr/bin/env python3
"""Launch UI immediately with a mock session — no BLE required."""
import sys
sys.path.insert(0, "/home/uday/Documents/NothingEarbuds")

from unittest.mock import MagicMock
from PyQt6.QtWidgets import QApplication
from cmf_control.ui.theme import NOTHING_DARK_QSS
from cmf_control.ui.main_window import MainWindow
from cmf_control.protocol.codec import Message
from cmf_control.protocol.constants import (
    CMD_BATTERY, CMD_NOISE_REDUCTION, CMD_EQ_PRESET
)

# Mock session that returns plausible responses
session = MagicMock()

def mock_send(cmd, payload=b""):
    if cmd == CMD_BATTERY:
        # left=72%, right=68%, case=45%
        return Message(command=cmd, payload=bytes([
            0x02, 72, 0x03, 68, 0x04, 45
        ]))
    if cmd == CMD_NOISE_REDUCTION:
        return Message(command=cmd, payload=bytes([0x05]))  # ANC off
    if cmd == CMD_EQ_PRESET:
        return Message(command=cmd, payload=bytes([0x00]))  # balanced
    return Message(command=cmd, payload=b"")

session.send.side_effect = mock_send

app = QApplication(sys.argv)
app.setStyleSheet(NOTHING_DARK_QSS)
window = MainWindow(session)
window.show()
sys.exit(app.exec())
