from unittest.mock import patch
from cmf_control.features.gestures import get_gestures, set_gesture, GestureSlot
from cmf_control.protocol.codec import Packet
from cmf_control.protocol.constants import CMD_GET_GESTURE, CMD_SET_GESTURE

def _make_slots_payload(slots: list[tuple[int, int, int, int]]) -> bytes:
    payload = bytearray([len(slots)])
    for device, button_id, gesture_type, action in slots:
        payload += bytes([device, button_id, gesture_type, action])
    return bytes(payload)

def test_get_gestures_parses_all_slots(mock_session):
    raw = [(0x02, 0x01, 0x02, 0x02), (0x03, 0x01, 0x07, 0x0A)]
    response = Packet(cmd=CMD_GET_GESTURE, seq=0, payload=_make_slots_payload(raw))
    with patch.object(mock_session, "send", return_value=response):
        slots = get_gestures(mock_session)
    assert slots == [GestureSlot(*raw[0]), GestureSlot(*raw[1])]

def test_get_gestures_empty_payload_returns_empty_list(mock_session):
    response = Packet(cmd=CMD_GET_GESTURE, seq=0, payload=b"")
    with patch.object(mock_session, "send", return_value=response):
        assert get_gestures(mock_session) == []

def test_set_gesture_sends_correct_bytes(mock_session):
    ack = Packet(cmd=CMD_SET_GESTURE, seq=0, payload=b"")
    with patch.object(mock_session, "send_nowait", return_value=ack) as mock_send:
        set_gesture(mock_session, device=0x03, button_id=0x01, gesture_type=0x02, action=0x09)
        mock_send.assert_called_once_with(
            CMD_SET_GESTURE,
            payload=bytes([0x01, 0x03, 0x01, 0x02, 0x09])
        )
