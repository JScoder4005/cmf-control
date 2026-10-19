from cmf_control.bt.session import BTSession
from cmf_control.protocol.constants import CMD_FIRMWARE_VERSION


def get_firmware_version(session: BTSession, timeout: float | None = None) -> str:
    pkt = session.send(CMD_FIRMWARE_VERSION, timeout=timeout)
    p = pkt.payload
    if not p:
        return "—"
    try:
        s = p.decode("ascii", errors="ignore").strip("\x00").strip()
        return s if s else p.hex()
    except Exception:
        return p.hex()
