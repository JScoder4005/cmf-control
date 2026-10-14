from unittest.mock import patch
import pytest
from cmf_control.features.anc import get_anc, set_anc, ANC_MODES
from cmf_control.protocol.codec import Packet
from cmf_control.protocol.constants import CMD_GET_ANC, CMD_SET_ANC, ANC_OFF, ANC_MAX, ANC_TRANSPARENCY

def test_get_anc_returns_mode(mock_session):
    response = Packet(cmd=CMD_GET_ANC, seq=0, payload=bytes([ANC_TRANSPARENCY]))
    with patch.object(mock_session, "send", return_value=response):
        assert get_anc(mock_session) == ANC_TRANSPARENCY

def test_get_anc_empty_payload_raises(mock_session):
    response = Packet(cmd=CMD_GET_ANC, seq=0, payload=b"")
    with patch.object(mock_session, "send", return_value=response):
        with pytest.raises(ValueError, match="Empty ANC"):
            get_anc(mock_session)

def test_set_anc_sends_correct_cmd(mock_session):
    ack = Packet(cmd=CMD_SET_ANC, seq=0, payload=b"")
    with patch.object(mock_session, "send", return_value=ack) as mock_send:
        set_anc(mock_session, ANC_MAX)
        mock_send.assert_called_once_with(CMD_SET_ANC, payload=bytes([ANC_MAX]))

def test_set_anc_invalid_mode_raises(mock_session):
    with pytest.raises(ValueError, match="Unknown ANC mode"):
        set_anc(mock_session, 0xFF)
