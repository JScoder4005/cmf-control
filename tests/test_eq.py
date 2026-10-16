from unittest.mock import patch
import pytest
from cmf_control.features.eq import get_eq, set_eq
from cmf_control.protocol.codec import Packet
from cmf_control.protocol.constants import CMD_GET_EQ, CMD_SET_EQ, EQ_BASS_BOOST

def test_get_eq(mock_session):
    response = Packet(cmd=CMD_GET_EQ, seq=0, payload=bytes([EQ_BASS_BOOST]))
    with patch.object(mock_session, "send", return_value=response):
        assert get_eq(mock_session) == EQ_BASS_BOOST

def test_set_eq_sends_correct_cmd(mock_session):
    ack = Packet(cmd=CMD_SET_EQ, seq=0, payload=b"")
    with patch.object(mock_session, "send_nowait", return_value=ack) as mock_send:
        set_eq(mock_session, EQ_BASS_BOOST)
        mock_send.assert_called_once_with(CMD_SET_EQ, payload=bytes([EQ_BASS_BOOST, 0x00]))

def test_set_eq_invalid_raises(mock_session):
    with pytest.raises(ValueError, match="Unknown EQ preset"):
        set_eq(mock_session, 0xFF)
