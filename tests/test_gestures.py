from unittest.mock import patch
import pytest
from cmf_control.features.gestures import get_gestures, set_gesture, GESTURE_POSITIONS
from cmf_control.protocol.codec import Packet
from cmf_control.protocol.constants import (
    CMD_GET_GESTURE, CMD_SET_GESTURE,
    GESTURE_LEFT_SINGLE, GESTURE_PLAY_PAUSE, GESTURE_RIGHT_DOUBLE, GESTURE_NEXT_TRACK,
)

def _make_gesture_payload():
    payload = bytearray()
    for pos in GESTURE_POSITIONS:
        payload += bytes([pos, GESTURE_PLAY_PAUSE])
    return bytes(payload)

def test_get_gestures_parses_all_positions(mock_session):
    response = Packet(cmd=CMD_GET_GESTURE, seq=0, payload=_make_gesture_payload())
    with patch.object(mock_session, "send", return_value=response):
        gmap = get_gestures(mock_session)
    assert gmap[GESTURE_LEFT_SINGLE] == GESTURE_PLAY_PAUSE
    assert len(gmap) == len(GESTURE_POSITIONS)

def test_set_gesture_sends_correct_bytes(mock_session):
    ack = Packet(cmd=CMD_SET_GESTURE, seq=0, payload=b"")
    with patch.object(mock_session, "send", return_value=ack) as mock_send:
        set_gesture(mock_session, GESTURE_RIGHT_DOUBLE, GESTURE_NEXT_TRACK)
        mock_send.assert_called_once_with(
            CMD_SET_GESTURE,
            payload=bytes([GESTURE_RIGHT_DOUBLE, GESTURE_NEXT_TRACK])
        )

def test_set_gesture_invalid_position_raises(mock_session):
    with pytest.raises(ValueError, match="Unknown gesture position"):
        set_gesture(mock_session, 0xFF, GESTURE_PLAY_PAUSE)

def test_set_gesture_invalid_action_raises(mock_session):
    with pytest.raises(ValueError, match="Unknown gesture action"):
        set_gesture(mock_session, GESTURE_LEFT_SINGLE, 0xFF)
