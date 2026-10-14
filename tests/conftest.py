import pytest
from unittest.mock import MagicMock
from cmf_control.bt.session import BTSession
from cmf_control.protocol.codec import Packet

@pytest.fixture
def mock_session():
    """BTSession with mocked socket — configure .send() return value per test."""
    session = BTSession("AA:BB:CC:DD:EE:FF")
    session._sock = MagicMock()
    session._seq = 0
    return session

def make_response(cmd: int, seq: int, payload: bytes) -> Packet:
    return Packet(cmd=cmd, seq=seq, payload=payload)
