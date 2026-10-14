from cmf_control.bt.session import BTSession
from cmf_control.protocol.constants import (
    CMD_GET_GESTURE, CMD_SET_GESTURE,
    GESTURE_LEFT_SINGLE, GESTURE_LEFT_DOUBLE, GESTURE_LEFT_TRIPLE, GESTURE_LEFT_HOLD,
    GESTURE_RIGHT_SINGLE, GESTURE_RIGHT_DOUBLE, GESTURE_RIGHT_TRIPLE, GESTURE_RIGHT_HOLD,
    GESTURE_NONE, GESTURE_PLAY_PAUSE, GESTURE_NEXT_TRACK, GESTURE_PREV_TRACK,
    GESTURE_VOLUME_UP, GESTURE_VOLUME_DOWN, GESTURE_ANC_TOGGLE, GESTURE_VOICE_ASSIST,
)

GESTURE_POSITIONS = [
    GESTURE_LEFT_SINGLE, GESTURE_LEFT_DOUBLE, GESTURE_LEFT_TRIPLE, GESTURE_LEFT_HOLD,
    GESTURE_RIGHT_SINGLE, GESTURE_RIGHT_DOUBLE, GESTURE_RIGHT_TRIPLE, GESTURE_RIGHT_HOLD,
]

GESTURE_ACTIONS = {
    GESTURE_NONE:         "None",
    GESTURE_PLAY_PAUSE:   "Play/Pause",
    GESTURE_NEXT_TRACK:   "Next Track",
    GESTURE_PREV_TRACK:   "Prev Track",
    GESTURE_VOLUME_UP:    "Volume Up",
    GESTURE_VOLUME_DOWN:  "Volume Down",
    GESTURE_ANC_TOGGLE:   "ANC Toggle",
    GESTURE_VOICE_ASSIST: "Voice Assistant",
}

GestureMap = dict[int, int]

def get_gestures(session: BTSession) -> GestureMap:
    pkt = session.send(CMD_GET_GESTURE)
    if len(pkt.payload) < len(GESTURE_POSITIONS) * 2:
        raise ValueError(f"Gesture response too short: {pkt.payload.hex()}")
    result = {}
    for i, pos in enumerate(GESTURE_POSITIONS):
        result[pos] = pkt.payload[i * 2 + 1]
    return result

def set_gesture(session: BTSession, position: int, action: int) -> None:
    if position not in GESTURE_POSITIONS:
        raise ValueError(f"Unknown gesture position: {position:#x}")
    if action not in GESTURE_ACTIONS:
        raise ValueError(f"Unknown gesture action: {action:#x}")
    session.send(CMD_SET_GESTURE, payload=bytes([position, action]))
