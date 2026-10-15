from unittest.mock import patch
import pytest
from cmf_control.features.battery import get_battery, BatteryStatus
from cmf_control.protocol.codec import Packet
from cmf_control.protocol.constants import CMD_GET_BATTERY, BATT_KEY_LEFT, BATT_KEY_RIGHT, BATT_KEY_CASE

def test_get_battery_parses_payload(mock_session):
    # Real wire format: count byte, then (key, value) pairs
    payload = bytes([3, BATT_KEY_LEFT, 87, BATT_KEY_RIGHT, 91, BATT_KEY_CASE, 100])
    response = Packet(cmd=CMD_GET_BATTERY, seq=0, payload=payload)
    with patch.object(mock_session, "send", return_value=response):
        status = get_battery(mock_session)
    assert status == BatteryStatus(left=87, right=91, case=100)

def test_get_battery_short_payload_raises(mock_session):
    response = Packet(cmd=CMD_GET_BATTERY, seq=0, payload=bytes([87]))
    with patch.object(mock_session, "send", return_value=response):
        with pytest.raises(ValueError, match="too short"):
            get_battery(mock_session)
