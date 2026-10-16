from unittest.mock import patch
import pytest
from cmf_control.features.anc import get_anc, set_anc
from cmf_control.protocol.codec import Packet
from cmf_control.protocol.constants import CMD_GET_ANC, CMD_SET_ANC, ANC_VAL_OFF, ANC_VAL_PASS_THROUGH, ANC_VAL_STRONG

def test_get_anc_parses_tuple_payload(mock_session):
    # 3-byte tuple: type=1 (mode), value=ANC_VAL_PASS_THROUGH, padding=0
    payload = bytes([1, ANC_VAL_PASS_THROUGH, 0])
    response = Packet(cmd=CMD_GET_ANC, seq=0, payload=payload)
    with patch.object(mock_session, "send", return_value=response):
        assert get_anc(mock_session) == ANC_VAL_PASS_THROUGH

def test_get_anc_empty_payload_raises(mock_session):
    response = Packet(cmd=CMD_GET_ANC, seq=0, payload=b"")
    with patch.object(mock_session, "send", return_value=response):
        with pytest.raises(ValueError, match="Empty ANC"):
            get_anc(mock_session)

def test_set_anc_sends_tuple(mock_session):
    ack = Packet(cmd=CMD_SET_ANC, seq=0, payload=b"")
    with patch.object(mock_session, "send_nowait", return_value=ack) as mock_send:
        set_anc(mock_session, ANC_VAL_STRONG)
        mock_send.assert_called_once_with(CMD_SET_ANC, payload=bytes([1, ANC_VAL_STRONG, 0]))
