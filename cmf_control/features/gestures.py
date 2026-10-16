from dataclasses import dataclass
from cmf_control.bt.session import BTSession
from cmf_control.protocol.constants import CMD_GET_GESTURE, CMD_SET_GESTURE

ACTIONS = {
    0x01: "None",
    0x02: "Play/Pause",
    0x08: "Prev Track",
    0x09: "Next Track",
    0x0B: "Voice Assistant",
    0x12: "Volume Up",
    0x13: "Volume Down",
    0x0A: "Noise Control",
}

GESTURE_TYPES = {
    0x02: "Double Tap",
    0x03: "Triple Tap",
    0x07: "Hold",
}

SLOTS = [
    ("Left Double",  0x02, 0x01, 0x02),
    ("Left Triple",  0x02, 0x01, 0x03),
    ("Left Hold",    0x02, 0x01, 0x07),
    ("Right Double", 0x03, 0x01, 0x02),
    ("Right Triple", 0x03, 0x01, 0x03),
    ("Right Hold",   0x03, 0x01, 0x07),
]

@dataclass
class GestureSlot:
    device: int
    button_id: int
    gesture_type: int
    action: int

def get_gestures(session: BTSession) -> list[GestureSlot]:
    pkt = session.send(CMD_GET_GESTURE)
    p = pkt.payload
    if not p:
        return []
    count = p[0]
    slots = []
    offset = 1
    for _ in range(count):
        if offset + 3 >= len(p):
            break
        slots.append(GestureSlot(p[offset], p[offset+1], p[offset+2], p[offset+3]))
        offset += 4
    return slots

def set_gesture(session: BTSession, device: int, button_id: int, gesture_type: int, action: int) -> None:
    session.send_nowait(CMD_SET_GESTURE, payload=bytes([0x01, device, button_id, gesture_type, action]))
