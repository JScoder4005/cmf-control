import pytest
from cmf_control.bt.session import BTSession
from cmf_control.protocol.codec import Packet

@pytest.fixture
def mock_session():
    """BTSession — configure .send()/.send_nowait() return value per test."""
    return BTSession("AA:BB:CC:DD:EE:FF")

def make_response(cmd: int, seq: int, payload: bytes) -> Packet:
    return Packet(cmd=cmd, seq=seq, payload=payload)
