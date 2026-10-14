# CMF Control — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an open-source Linux desktop app to control CMF Buds Pro 2 earbuds (ANC, battery, EQ, gestures) with a Nothing OS-inspired dark UI.

**Architecture:** Python + PyQt6 app with a raw BlueZ RFCOMM socket layer, a protocol codec module that encodes/decodes CMF packet bytes, feature modules for each capability, and a custom dark-themed UI. Protocol bytes were reverse-engineered by sniffing the official Android app.

**Tech Stack:** Python 3.11+, PyQt6, BlueZ (Linux kernel BT stack via `socket`), `hcitool`/`bluetoothctl` for discovery, `pytest` for tests.

---

## File Map

```
cmf-control/
├── cmf_control/
│   ├── __init__.py
│   ├── main.py                  # Entry point — launches Qt app
│   ├── bt/
│   │   ├── __init__.py
│   │   ├── scanner.py           # Discover CMF devices via bluetoothctl subprocess
│   │   └── session.py           # RFCOMM socket connect/send/recv/reconnect
│   ├── protocol/
│   │   ├── __init__.py
│   │   ├── codec.py             # Encode/decode CMF packets (header + payload)
│   │   └── constants.py         # CMD bytes, feature IDs, mode values
│   ├── features/
│   │   ├── __init__.py
│   │   ├── anc.py               # ANC get/set using session + codec
│   │   ├── battery.py           # Battery poll using session + codec
│   │   ├── eq.py                # EQ profile get/set
│   │   └── gestures.py          # Gesture remap get/set
│   └── ui/
│       ├── __init__.py
│       ├── app.py               # QApplication setup
│       ├── main_window.py       # Top-level QMainWindow
│       ├── theme.py             # Nothing dark QSS stylesheet string
│       └── widgets/
│           ├── __init__.py
│           ├── battery_bar.py   # Battery widget (L/R/Case)
│           ├── anc_toggle.py    # ANC mode pill buttons
│           ├── eq_picker.py     # EQ preset dropdown/buttons
│           └── gesture_map.py   # Gesture remapping grid
├── tools/
│   └── sniff.py                 # BT packet capture helper for protocol RE
├── tests/
│   ├── test_codec.py
│   ├── test_anc.py
│   ├── test_battery.py
│   ├── test_eq.py
│   ├── test_gestures.py
│   └── conftest.py              # Mock session fixture
├── docs/
│   └── protocol.md              # Reverse-engineered protocol spec
├── pyproject.toml
├── README.md
└── .gitignore
```

---

### Task 1: Project Bootstrap

**Files:**
- Create: `pyproject.toml`
- Create: `cmf_control/__init__.py`
- Create: `cmf_control/main.py`
- Create: `.gitignore`
- Create: `README.md`

- [ ] **Step 1: Init git repo and create structure**

```bash
cd /home/uday/Documents/NothingEarbuds
git init
mkdir -p cmf_control/bt cmf_control/protocol cmf_control/features cmf_control/ui/widgets tools tests docs
touch cmf_control/__init__.py cmf_control/bt/__init__.py cmf_control/protocol/__init__.py
touch cmf_control/features/__init__.py cmf_control/ui/__init__.py cmf_control/ui/widgets/__init__.py
```

- [ ] **Step 2: Write pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "cmf-control"
version = "0.1.0"
description = "Linux desktop app to control CMF Buds Pro 2 earbuds"
license = {text = "MIT"}
requires-python = ">=3.11"
dependencies = [
    "PyQt6>=6.6.0",
]

[project.scripts]
cmf-control = "cmf_control.main:main"

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-qt>=4.4"]

[tool.setuptools.packages.find]
where = ["."]
include = ["cmf_control*"]
```

- [ ] **Step 3: Write cmf_control/main.py**

```python
import sys
from cmf_control.ui.app import run

def main():
    sys.exit(run())

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Write .gitignore**

```
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.venv/
.superpowers/
```

- [ ] **Step 5: Install in dev mode**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Expected: installs without error.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml cmf_control/ .gitignore
git commit -m "feat: bootstrap project structure"
```

---

### Task 2: Protocol Constants and Codec

**Files:**
- Create: `cmf_control/protocol/constants.py`
- Create: `cmf_control/protocol/codec.py`
- Create: `tests/test_codec.py`
- Create: `docs/protocol.md`

**Context:** CMF Buds Pro 2 use Bluetooth Classic RFCOMM (SPP profile). Packets are reverse-engineered from the official Android app via BT sniffing. Packet structure: `[HEADER_MAGIC(2)] [CMD(1)] [SEQ(1)] [PAYLOAD_LEN(2)] [PAYLOAD(n)] [CHECKSUM(1)]`.

The magic bytes, command IDs, and checksum algorithm below are based on the Nothing earbuds open protocol community work and will need verification against your physical device using `tools/sniff.py` (Task 3).

- [ ] **Step 1: Write constants.py**

```python
# Packet framing
MAGIC = bytes([0xAA, 0xBB])
MAX_PAYLOAD = 512

# Commands (to-device)
CMD_GET_BATTERY   = 0x05
CMD_SET_ANC       = 0x06
CMD_GET_ANC       = 0x07
CMD_SET_EQ        = 0x08
CMD_GET_EQ        = 0x09
CMD_SET_GESTURE   = 0x0A
CMD_GET_GESTURE   = 0x0B

# ANC modes
ANC_OFF          = 0x00
ANC_TRANSPARENCY = 0x01
ANC_LIGHT        = 0x02
ANC_MAX          = 0x03

# EQ presets
EQ_BALANCED      = 0x00
EQ_BASS_BOOST    = 0x01
EQ_TREBLE_BOOST  = 0x02
EQ_PODCAST       = 0x03
EQ_GAMING        = 0x04

# Gesture actions
GESTURE_NONE         = 0x00
GESTURE_PLAY_PAUSE   = 0x01
GESTURE_NEXT_TRACK   = 0x02
GESTURE_PREV_TRACK   = 0x03
GESTURE_VOLUME_UP    = 0x04
GESTURE_VOLUME_DOWN  = 0x05
GESTURE_ANC_TOGGLE   = 0x06
GESTURE_VOICE_ASSIST = 0x07

# Gesture positions (which tap type on which bud)
GESTURE_LEFT_SINGLE  = 0x10
GESTURE_LEFT_DOUBLE  = 0x11
GESTURE_LEFT_TRIPLE  = 0x12
GESTURE_LEFT_HOLD    = 0x13
GESTURE_RIGHT_SINGLE = 0x20
GESTURE_RIGHT_DOUBLE = 0x21
GESTURE_RIGHT_TRIPLE = 0x22
GESTURE_RIGHT_HOLD   = 0x23
```

- [ ] **Step 2: Write codec.py**

```python
from dataclasses import dataclass
from cmf_control.protocol.constants import MAGIC, MAX_PAYLOAD

@dataclass
class Packet:
    cmd: int
    seq: int
    payload: bytes

    def encode(self) -> bytes:
        length = len(self.payload).to_bytes(2, "big")
        body = bytes([self.cmd, self.seq]) + length + self.payload
        checksum = _checksum(body)
        return MAGIC + body + bytes([checksum])

    @staticmethod
    def decode(data: bytes) -> "Packet":
        if len(data) < 7:
            raise ValueError(f"Packet too short: {len(data)} bytes")
        if data[:2] != MAGIC:
            raise ValueError(f"Bad magic: {data[:2].hex()}")
        cmd = data[2]
        seq = data[3]
        payload_len = int.from_bytes(data[4:6], "big")
        if len(data) < 6 + payload_len + 1:
            raise ValueError("Packet truncated")
        payload = data[6:6 + payload_len]
        checksum = data[6 + payload_len]
        body = data[2:6 + payload_len]
        if checksum != _checksum(body):
            raise ValueError(f"Checksum mismatch: got {checksum:#x}")
        return Packet(cmd=cmd, seq=seq, payload=payload)

def _checksum(data: bytes) -> int:
    return sum(data) & 0xFF
```

- [ ] **Step 3: Write tests/test_codec.py**

```python
import pytest
from cmf_control.protocol.codec import Packet, _checksum
from cmf_control.protocol.constants import MAGIC, CMD_GET_BATTERY

def test_encode_roundtrip():
    pkt = Packet(cmd=CMD_GET_BATTERY, seq=1, payload=bytes([0x01]))
    encoded = pkt.encode()
    decoded = Packet.decode(encoded)
    assert decoded.cmd == pkt.cmd
    assert decoded.seq == pkt.seq
    assert decoded.payload == pkt.payload

def test_encode_starts_with_magic():
    pkt = Packet(cmd=CMD_GET_BATTERY, seq=0, payload=b"")
    assert pkt.encode()[:2] == MAGIC

def test_decode_bad_magic():
    pkt = Packet(cmd=CMD_GET_BATTERY, seq=0, payload=b"").encode()
    bad = b"\x00\x00" + pkt[2:]
    with pytest.raises(ValueError, match="Bad magic"):
        Packet.decode(bad)

def test_decode_bad_checksum():
    pkt = Packet(cmd=CMD_GET_BATTERY, seq=0, payload=b"\x01").encode()
    corrupted = pkt[:-1] + bytes([pkt[-1] ^ 0xFF])
    with pytest.raises(ValueError, match="Checksum mismatch"):
        Packet.decode(corrupted)

def test_decode_too_short():
    with pytest.raises(ValueError, match="too short"):
        Packet.decode(b"\xAA\xBB\x05")

def test_empty_payload():
    pkt = Packet(cmd=0x05, seq=0, payload=b"")
    assert Packet.decode(pkt.encode()).payload == b""
```

- [ ] **Step 4: Run tests — verify all pass**

```bash
pytest tests/test_codec.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Write docs/protocol.md skeleton**

```markdown
# CMF Buds Pro 2 — Bluetooth Protocol

> Status: partially reverse-engineered. Verify bytes with tools/sniff.py on your device.

## Transport

Bluetooth Classic RFCOMM, SPP profile. UUID: `00001101-0000-1000-8000-00805f9b34fb`

## Packet Format

```
[AA BB] [CMD] [SEQ] [LEN_HI LEN_LO] [PAYLOAD...] [CHECKSUM]
```

- Magic: `0xAA 0xBB`
- CMD: command byte (see below)
- SEQ: sequence number, incremented per request, wraps at 0xFF
- LEN: 2-byte big-endian payload length
- CHECKSUM: sum of bytes from CMD to end of PAYLOAD, masked to 0xFF

## Known Commands

| CMD  | Direction | Description       |
|------|-----------|-------------------|
| 0x05 | host→buds | Get battery       |
| 0x06 | host→buds | Set ANC mode      |
| 0x07 | host→buds | Get ANC mode      |
| 0x08 | host→buds | Set EQ preset     |
| 0x09 | host→buds | Get EQ preset     |
| 0x0A | host→buds | Set gesture map   |
| 0x0B | host→buds | Get gesture map   |

## Battery Response Payload (CMD 0x05 response)

```
[LEFT%] [RIGHT%] [CASE%]
```

> ⚠️ All command bytes are UNVERIFIED. Use tools/sniff.py to confirm.
```

- [ ] **Step 6: Commit**

```bash
git add cmf_control/protocol/ tests/test_codec.py docs/protocol.md
git commit -m "feat: protocol codec and constants"
```

---

### Task 3: Bluetooth Sniff Tool

**Files:**
- Create: `tools/sniff.py`

**Purpose:** Capture raw RFCOMM traffic between the official CMF Android app and the earbuds, so we can verify/correct the protocol bytes in constants.py. Requires an Android device with ADB and `btsnoop_hci.log` enabled in developer options.

- [ ] **Step 1: Write tools/sniff.py**

```python
#!/usr/bin/env python3
"""
CMF BT protocol sniffer.

Usage:
  # On Android: enable "Bluetooth HCI snoop log" in Developer Options
  # Connect CMF buds to phone, use official app, then:
  adb pull /data/misc/bluetooth/logs/btsnoop_hci.log snoop.log

  # Then parse:
  python tools/sniff.py snoop.log [--filter-addr AA:BB:CC:DD:EE:FF]
"""
import sys
import struct
import argparse
from pathlib import Path

BTSNOOP_MAGIC = b"btsnoop\x00"
RFCOMM_PSM = 3  # Classic BT RFCOMM channel

def parse_btsnoop(path: Path, filter_addr: str | None):
    data = path.read_bytes()
    if not data.startswith(BTSNOOP_MAGIC):
        sys.exit(f"Not a btsnoop file: {path}")

    version, datalink = struct.unpack_from(">II", data, 8)
    print(f"btsnoop version={version} datalink={datalink}")

    offset = 16
    pkt_num = 0
    while offset < len(data):
        if offset + 24 > len(data):
            break
        orig_len, incl_len, flags, drops, ts_usec = struct.unpack_from(">IIIIq", data, offset)
        offset += 24
        payload = data[offset:offset + incl_len]
        offset += incl_len
        pkt_num += 1

        direction = "HOST→BT" if flags & 1 == 0 else "BT→HOST"
        # Print raw hex for RFCOMM-looking packets (heuristic: start with AA BB)
        if len(payload) > 4 and b"\xaa\xbb" in payload:
            idx = payload.index(b"\xaa\xbb")
            chunk = payload[idx:]
            print(f"\nPacket #{pkt_num} {direction} ts={ts_usec}")
            print(f"  Raw: {chunk.hex()}")
            if len(chunk) >= 7:
                cmd = chunk[2]
                seq = chunk[3]
                pay_len = int.from_bytes(chunk[4:6], "big")
                pay = chunk[6:6+pay_len]
                print(f"  CMD=0x{cmd:02x} SEQ={seq} PAYLOAD={pay.hex()}")

def main():
    ap = argparse.ArgumentParser(description="Parse CMF btsnoop HCI log")
    ap.add_argument("logfile", type=Path)
    ap.add_argument("--filter-addr", help="Filter by BT address (not yet implemented)")
    args = ap.parse_args()
    parse_btsnoop(args.logfile, args.filter_addr)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify script runs**

```bash
python tools/sniff.py --help
```

Expected: prints usage.

- [ ] **Step 3: Commit**

```bash
git add tools/sniff.py
git commit -m "feat: add btsnoop protocol sniffer tool"
```

---

### Task 4: Bluetooth Session Layer

**Files:**
- Create: `cmf_control/bt/scanner.py`
- Create: `cmf_control/bt/session.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write scanner.py**

```python
import subprocess
import re
from dataclasses import dataclass

CMF_NAME_PATTERN = re.compile(r"cmf|nothing", re.IGNORECASE)

@dataclass
class BTDevice:
    address: str
    name: str

def scan_devices(timeout: int = 8) -> list[BTDevice]:
    """Return paired BT devices matching CMF/Nothing name pattern."""
    result = subprocess.run(
        ["bluetoothctl", "devices"],
        capture_output=True, text=True, timeout=timeout
    )
    devices = []
    for line in result.stdout.splitlines():
        # Format: "Device AA:BB:CC:DD:EE:FF Device Name"
        parts = line.strip().split(" ", 2)
        if len(parts) == 3 and parts[0] == "Device":
            addr, name = parts[1], parts[2]
            if CMF_NAME_PATTERN.search(name):
                devices.append(BTDevice(address=addr, name=name))
    return devices
```

- [ ] **Step 2: Write session.py**

```python
import socket
import threading
import time
from cmf_control.protocol.codec import Packet

SPP_UUID = "00001101-0000-1000-8000-00805f9b34fb"
RFCOMM_CHANNEL = 1
RECV_TIMEOUT = 5.0
RECONNECT_DELAY = 3.0

class BTSession:
    def __init__(self, address: str):
        self.address = address
        self._sock: socket.socket | None = None
        self._seq = 0
        self._lock = threading.Lock()

    def connect(self) -> None:
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.settimeout(RECV_TIMEOUT)
        sock.connect((self.address, RFCOMM_CHANNEL))
        self._sock = sock

    def disconnect(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def send(self, cmd: int, payload: bytes = b"") -> Packet:
        with self._lock:
            if not self._sock:
                raise ConnectionError("Not connected")
            seq = self._seq
            self._seq = (self._seq + 1) & 0xFF
            pkt = Packet(cmd=cmd, seq=seq, payload=payload)
            self._sock.sendall(pkt.encode())
            return self._recv_response(seq)

    def _recv_response(self, expected_seq: int) -> Packet:
        buf = b""
        deadline = time.monotonic() + RECV_TIMEOUT
        while time.monotonic() < deadline:
            try:
                chunk = self._sock.recv(256)
            except TimeoutError:
                break
            if not chunk:
                raise ConnectionError("Socket closed by device")
            buf += chunk
            try:
                pkt = Packet.decode(buf)
                if pkt.seq == expected_seq:
                    return pkt
                buf = buf[7 + len(pkt.payload):]
            except ValueError:
                continue
        raise TimeoutError(f"No response for seq={expected_seq}")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()
```

- [ ] **Step 3: Write tests/conftest.py**

```python
import pytest
from unittest.mock import MagicMock, patch
from cmf_control.bt.session import BTSession
from cmf_control.protocol.codec import Packet
from cmf_control.protocol.constants import CMD_GET_BATTERY

@pytest.fixture
def mock_session():
    """BTSession with mocked socket — configure .send() return value per test."""
    session = BTSession("AA:BB:CC:DD:EE:FF")
    session._sock = MagicMock()
    session._seq = 0
    return session

def make_response(cmd: int, seq: int, payload: bytes) -> Packet:
    return Packet(cmd=cmd, seq=seq, payload=payload)
```

- [ ] **Step 4: Commit**

```bash
git add cmf_control/bt/ tests/conftest.py
git commit -m "feat: BT scanner and RFCOMM session layer"
```

---

### Task 5: Feature — Battery

**Files:**
- Create: `cmf_control/features/battery.py`
- Create: `tests/test_battery.py`

- [ ] **Step 1: Write battery.py**

```python
from dataclasses import dataclass
from cmf_control.bt.session import BTSession
from cmf_control.protocol.constants import CMD_GET_BATTERY

@dataclass
class BatteryStatus:
    left: int    # 0-100
    right: int   # 0-100
    case: int    # 0-100

def get_battery(session: BTSession) -> BatteryStatus:
    pkt = session.send(CMD_GET_BATTERY)
    if len(pkt.payload) < 3:
        raise ValueError(f"Battery response too short: {pkt.payload.hex()}")
    return BatteryStatus(
        left=pkt.payload[0],
        right=pkt.payload[1],
        case=pkt.payload[2],
    )
```

- [ ] **Step 2: Write tests/test_battery.py**

```python
from unittest.mock import patch
import pytest
from cmf_control.features.battery import get_battery, BatteryStatus
from cmf_control.protocol.codec import Packet
from cmf_control.protocol.constants import CMD_GET_BATTERY

def test_get_battery_parses_payload(mock_session):
    response = Packet(cmd=CMD_GET_BATTERY, seq=0, payload=bytes([87, 91, 100]))
    with patch.object(mock_session, "send", return_value=response):
        status = get_battery(mock_session)
    assert status == BatteryStatus(left=87, right=91, case=100)

def test_get_battery_short_payload_raises(mock_session):
    response = Packet(cmd=CMD_GET_BATTERY, seq=0, payload=bytes([87]))
    with patch.object(mock_session, "send", return_value=response):
        with pytest.raises(ValueError, match="too short"):
            get_battery(mock_session)
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/test_battery.py -v
```

Expected: 2 passed.

- [ ] **Step 4: Commit**

```bash
git add cmf_control/features/battery.py tests/test_battery.py
git commit -m "feat: battery status feature"
```

---

### Task 6: Feature — ANC

**Files:**
- Create: `cmf_control/features/anc.py`
- Create: `tests/test_anc.py`

- [ ] **Step 1: Write anc.py**

```python
from cmf_control.bt.session import BTSession
from cmf_control.protocol.constants import (
    CMD_GET_ANC, CMD_SET_ANC,
    ANC_OFF, ANC_TRANSPARENCY, ANC_LIGHT, ANC_MAX,
)

ANC_MODES = {
    ANC_OFF: "Off",
    ANC_TRANSPARENCY: "Transparency",
    ANC_LIGHT: "Light ANC",
    ANC_MAX: "Max ANC",
}

def get_anc(session: BTSession) -> int:
    pkt = session.send(CMD_GET_ANC)
    if len(pkt.payload) < 1:
        raise ValueError("Empty ANC response")
    return pkt.payload[0]

def set_anc(session: BTSession, mode: int) -> None:
    if mode not in ANC_MODES:
        raise ValueError(f"Unknown ANC mode: {mode:#x}")
    session.send(CMD_SET_ANC, payload=bytes([mode]))
```

- [ ] **Step 2: Write tests/test_anc.py**

```python
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
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/test_anc.py -v
```

Expected: 4 passed.

- [ ] **Step 4: Commit**

```bash
git add cmf_control/features/anc.py tests/test_anc.py
git commit -m "feat: ANC get/set feature"
```

---

### Task 7: Feature — EQ

**Files:**
- Create: `cmf_control/features/eq.py`
- Create: `tests/test_eq.py`

- [ ] **Step 1: Write eq.py**

```python
from cmf_control.bt.session import BTSession
from cmf_control.protocol.constants import (
    CMD_GET_EQ, CMD_SET_EQ,
    EQ_BALANCED, EQ_BASS_BOOST, EQ_TREBLE_BOOST, EQ_PODCAST, EQ_GAMING,
)

EQ_PRESETS = {
    EQ_BALANCED:     "Balanced",
    EQ_BASS_BOOST:   "Bass Boost",
    EQ_TREBLE_BOOST: "Treble Boost",
    EQ_PODCAST:      "Podcast",
    EQ_GAMING:       "Gaming",
}

def get_eq(session: BTSession) -> int:
    pkt = session.send(CMD_GET_EQ)
    if len(pkt.payload) < 1:
        raise ValueError("Empty EQ response")
    return pkt.payload[0]

def set_eq(session: BTSession, preset: int) -> None:
    if preset not in EQ_PRESETS:
        raise ValueError(f"Unknown EQ preset: {preset:#x}")
    session.send(CMD_SET_EQ, payload=bytes([preset]))
```

- [ ] **Step 2: Write tests/test_eq.py**

```python
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
    with patch.object(mock_session, "send", return_value=ack) as mock_send:
        set_eq(mock_session, EQ_BASS_BOOST)
        mock_send.assert_called_once_with(CMD_SET_EQ, payload=bytes([EQ_BASS_BOOST]))

def test_set_eq_invalid_raises(mock_session):
    with pytest.raises(ValueError, match="Unknown EQ preset"):
        set_eq(mock_session, 0xFF)
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/test_eq.py -v
```

Expected: 3 passed.

- [ ] **Step 4: Commit**

```bash
git add cmf_control/features/eq.py tests/test_eq.py
git commit -m "feat: EQ preset feature"
```

---

### Task 8: Feature — Gestures

**Files:**
- Create: `cmf_control/features/gestures.py`
- Create: `tests/test_gestures.py`

- [ ] **Step 1: Write gestures.py**

```python
from dataclasses import dataclass
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

# GestureMap: position_byte → action_byte (8 entries, one per position)
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
```

- [ ] **Step 2: Write tests/test_gestures.py**

```python
from unittest.mock import patch
import pytest
from cmf_control.features.gestures import get_gestures, set_gesture, GESTURE_POSITIONS
from cmf_control.protocol.codec import Packet
from cmf_control.protocol.constants import (
    CMD_GET_GESTURE, CMD_SET_GESTURE,
    GESTURE_LEFT_SINGLE, GESTURE_PLAY_PAUSE, GESTURE_RIGHT_DOUBLE, GESTURE_NEXT_TRACK,
)

def _make_gesture_payload():
    # 8 pairs of (position, action), all set to PLAY_PAUSE
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
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/test_gestures.py -v
```

Expected: 4 passed.

- [ ] **Step 4: Commit**

```bash
git add cmf_control/features/gestures.py tests/test_gestures.py
git commit -m "feat: gesture remapping feature"
```

---

### Task 9: Nothing Dark Theme

**Files:**
- Create: `cmf_control/ui/theme.py`

- [ ] **Step 1: Write theme.py**

```python
NOTHING_DARK_QSS = """
QWidget {
    background-color: #0a0a0a;
    color: #ffffff;
    font-family: "Space Mono", "Courier New", monospace;
    font-size: 13px;
}

QMainWindow {
    background-color: #0a0a0a;
}

QLabel {
    color: #ffffff;
}

QLabel#subtitle {
    color: #666666;
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
}

QPushButton {
    background-color: transparent;
    color: #ffffff;
    border: 1px solid #333333;
    border-radius: 14px;
    padding: 6px 16px;
    font-family: "Space Mono", monospace;
    font-size: 11px;
    letter-spacing: 1px;
}

QPushButton:hover {
    border-color: #666666;
}

QPushButton:checked, QPushButton#active {
    background-color: #ffffff;
    color: #000000;
    border-color: #ffffff;
}

QPushButton:disabled {
    color: #333333;
    border-color: #1a1a1a;
}

QComboBox {
    background-color: #111111;
    color: #ffffff;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 4px 8px;
    font-family: "Space Mono", monospace;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #111111;
    color: #ffffff;
    selection-background-color: #222222;
    border: 1px solid #333333;
}

QProgressBar {
    background-color: #111111;
    border: 1px solid #222222;
    border-radius: 3px;
    text-align: center;
    color: #ffffff;
    font-size: 10px;
}

QProgressBar::chunk {
    background-color: #ffffff;
    border-radius: 2px;
}

QFrame#separator {
    background-color: #1a1a1a;
    max-height: 1px;
}

QStatusBar {
    background-color: #050505;
    color: #444444;
    font-size: 10px;
}
"""
```

- [ ] **Step 2: Commit**

```bash
git add cmf_control/ui/theme.py
git commit -m "feat: Nothing dark UI theme stylesheet"
```

---

### Task 10: UI Widgets

**Files:**
- Create: `cmf_control/ui/widgets/battery_bar.py`
- Create: `cmf_control/ui/widgets/anc_toggle.py`
- Create: `cmf_control/ui/widgets/eq_picker.py`
- Create: `cmf_control/ui/widgets/gesture_map.py`

- [ ] **Step 1: Write battery_bar.py**

```python
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt

class BatteryBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(16)

        self._bars = {}
        for label_text, key in [("L", "left"), ("R", "right"), ("CASE", "case")]:
            col = QVBoxLayout()
            lbl = QLabel(label_text)
            lbl.setObjectName("subtitle")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setFixedHeight(4)
            bar.setTextVisible(False)
            pct = QLabel("—%")
            pct.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(lbl)
            col.addWidget(bar)
            col.addWidget(pct)
            layout.addLayout(col)
            self._bars[key] = (bar, pct)

    def update_status(self, left: int, right: int, case: int):
        for key, val in [("left", left), ("right", right), ("case", case)]:
            bar, pct = self._bars[key]
            bar.setValue(val)
            pct.setText(f"{val}%")
```

- [ ] **Step 2: Write anc_toggle.py**

```python
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal
from cmf_control.protocol.constants import ANC_OFF, ANC_TRANSPARENCY, ANC_LIGHT, ANC_MAX
from cmf_control.features.anc import ANC_MODES

class ANCToggle(QWidget):
    mode_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        self._buttons: dict[int, QPushButton] = {}

        for mode, label in ANC_MODES.items():
            btn = QPushButton(label.upper())
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, m=mode: self._on_click(m))
            layout.addWidget(btn)
            self._buttons[mode] = btn

    def _on_click(self, mode: int):
        self.set_mode(mode)
        self.mode_changed.emit(mode)

    def set_mode(self, mode: int):
        for m, btn in self._buttons.items():
            btn.setChecked(m == mode)
```

- [ ] **Step 3: Write eq_picker.py**

```python
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal
from cmf_control.features.eq import EQ_PRESETS

class EQPicker(QWidget):
    preset_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        self._buttons: dict[int, QPushButton] = {}

        for preset, label in EQ_PRESETS.items():
            btn = QPushButton(label.upper())
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, p=preset: self._on_click(p))
            layout.addWidget(btn)
            self._buttons[preset] = btn

    def _on_click(self, preset: int):
        self.set_preset(preset)
        self.preset_changed.emit(preset)

    def set_preset(self, preset: int):
        for p, btn in self._buttons.items():
            btn.setChecked(p == preset)
```

- [ ] **Step 4: Write gesture_map.py**

```python
from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox
from PyQt6.QtCore import pyqtSignal
from cmf_control.features.gestures import GESTURE_ACTIONS, GESTURE_POSITIONS
from cmf_control.protocol.constants import (
    GESTURE_LEFT_SINGLE, GESTURE_LEFT_DOUBLE, GESTURE_LEFT_TRIPLE, GESTURE_LEFT_HOLD,
    GESTURE_RIGHT_SINGLE, GESTURE_RIGHT_DOUBLE, GESTURE_RIGHT_TRIPLE, GESTURE_RIGHT_HOLD,
)

POSITION_LABELS = {
    GESTURE_LEFT_SINGLE:  "L · Single",
    GESTURE_LEFT_DOUBLE:  "L · Double",
    GESTURE_LEFT_TRIPLE:  "L · Triple",
    GESTURE_LEFT_HOLD:    "L · Hold",
    GESTURE_RIGHT_SINGLE: "R · Single",
    GESTURE_RIGHT_DOUBLE: "R · Double",
    GESTURE_RIGHT_TRIPLE: "R · Triple",
    GESTURE_RIGHT_HOLD:   "R · Hold",
}

class GestureMap(QWidget):
    gesture_changed = pyqtSignal(int, int)  # (position, action)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setSpacing(8)
        self._combos: dict[int, QComboBox] = {}
        self._action_keys = list(GESTURE_ACTIONS.keys())

        for row, pos in enumerate(GESTURE_POSITIONS):
            lbl = QLabel(POSITION_LABELS[pos])
            lbl.setObjectName("subtitle")
            combo = QComboBox()
            for action, name in GESTURE_ACTIONS.items():
                combo.addItem(name.upper(), action)
            combo.currentIndexChanged.connect(
                lambda _, p=pos, c=combo: self._on_change(p, c)
            )
            layout.addWidget(lbl, row, 0)
            layout.addWidget(combo, row, 1)
            self._combos[pos] = combo

    def _on_change(self, position: int, combo: QComboBox):
        action = combo.currentData()
        self.gesture_changed.emit(position, action)

    def set_map(self, gmap: dict[int, int]):
        for pos, action in gmap.items():
            if pos in self._combos:
                idx = self._action_keys.index(action) if action in self._action_keys else 0
                self._combos[pos].blockSignals(True)
                self._combos[pos].setCurrentIndex(idx)
                self._combos[pos].blockSignals(False)
```

- [ ] **Step 5: Commit**

```bash
git add cmf_control/ui/widgets/
git commit -m "feat: UI widgets — battery, ANC, EQ, gestures"
```

---

### Task 11: Main Window + App Entry Point

**Files:**
- Create: `cmf_control/ui/app.py`
- Create: `cmf_control/ui/main_window.py`

- [ ] **Step 1: Write main_window.py**

```python
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QStatusBar, QPushButton
)
from PyQt6.QtCore import Qt, QTimer
from cmf_control.ui.widgets.battery_bar import BatteryBar
from cmf_control.ui.widgets.anc_toggle import ANCToggle
from cmf_control.ui.widgets.eq_picker import EQPicker
from cmf_control.ui.widgets.gesture_map import GestureMap
from cmf_control.bt.session import BTSession
from cmf_control.features.battery import get_battery
from cmf_control.features.anc import get_anc, set_anc
from cmf_control.features.eq import get_eq, set_eq
from cmf_control.features.gestures import get_gestures, set_gesture

BATTERY_POLL_MS = 30_000  # 30s

class MainWindow(QMainWindow):
    def __init__(self, session: BTSession):
        super().__init__()
        self._session = session
        self.setWindowTitle("CMF CONTROL")
        self.setMinimumWidth(520)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(20)

        # Header
        title = QLabel("CMF CONTROL")
        title.setStyleSheet("font-size: 18px; letter-spacing: 4px;")
        subtitle = QLabel("BUDS PRO 2")
        subtitle.setObjectName("subtitle")
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(self._separator())

        # Battery
        root.addWidget(QLabel("BATTERY"))
        self._battery = BatteryBar()
        root.addWidget(self._battery)
        root.addWidget(self._separator())

        # ANC
        root.addWidget(QLabel("NOISE CONTROL"))
        self._anc = ANCToggle()
        self._anc.mode_changed.connect(self._on_anc_changed)
        root.addWidget(self._anc)
        root.addWidget(self._separator())

        # EQ
        root.addWidget(QLabel("SOUND PROFILE"))
        self._eq = EQPicker()
        self._eq.preset_changed.connect(self._on_eq_changed)
        root.addWidget(self._eq)
        root.addWidget(self._separator())

        # Gestures
        root.addWidget(QLabel("TOUCH CONTROLS"))
        self._gestures = GestureMap()
        self._gestures.gesture_changed.connect(self._on_gesture_changed)
        root.addWidget(self._gestures)

        root.addStretch()

        self._status = QStatusBar()
        self.setStatusBar(self._status)

        # Battery poll timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_battery)
        self._timer.start(BATTERY_POLL_MS)

        self._load_initial_state()

    def _separator(self) -> QFrame:
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        return sep

    def _load_initial_state(self):
        try:
            status = get_battery(self._session)
            self._battery.update_status(status.left, status.right, status.case)
            anc_mode = get_anc(self._session)
            self._anc.set_mode(anc_mode)
            eq_preset = get_eq(self._session)
            self._eq.set_preset(eq_preset)
            gmap = get_gestures(self._session)
            self._gestures.set_map(gmap)
            self._status.showMessage("Connected")
        except Exception as e:
            self._status.showMessage(f"Load failed: {e}")

    def _poll_battery(self):
        try:
            status = get_battery(self._session)
            self._battery.update_status(status.left, status.right, status.case)
        except Exception:
            pass

    def _on_anc_changed(self, mode: int):
        try:
            set_anc(self._session, mode)
        except Exception as e:
            self._status.showMessage(f"ANC error: {e}")

    def _on_eq_changed(self, preset: int):
        try:
            set_eq(self._session, preset)
        except Exception as e:
            self._status.showMessage(f"EQ error: {e}")

    def _on_gesture_changed(self, position: int, action: int):
        try:
            set_gesture(self._session, position, action)
        except Exception as e:
            self._status.showMessage(f"Gesture error: {e}")
```

- [ ] **Step 2: Write app.py**

```python
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from cmf_control.ui.theme import NOTHING_DARK_QSS
from cmf_control.ui.main_window import MainWindow
from cmf_control.bt.scanner import scan_devices
from cmf_control.bt.session import BTSession

def run() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(NOTHING_DARK_QSS)

    devices = scan_devices()
    if not devices:
        QMessageBox.critical(None, "CMF Control", "No CMF/Nothing devices found.\n\nPair your earbuds first via bluetoothctl.")
        return 1

    # Pick first match (future: show device picker dialog)
    device = devices[0]
    session = BTSession(device.address)

    try:
        session.connect()
    except OSError as e:
        QMessageBox.critical(None, "CMF Control", f"Could not connect to {device.name} ({device.address}):\n{e}")
        return 1

    window = MainWindow(session)
    window.show()

    ret = app.exec()
    session.disconnect()
    return ret
```

- [ ] **Step 3: Run the app (device not required for launch test)**

```bash
python -m cmf_control.main
```

Expected: window opens with Nothing dark UI. If no device paired, shows error dialog cleanly.

- [ ] **Step 4: Commit**

```bash
git add cmf_control/ui/app.py cmf_control/ui/main_window.py
git commit -m "feat: main window and app entry point"
```

---

### Task 12: README and GitHub Setup

**Files:**
- Create: `README.md`
- Create: `LICENSE`

- [ ] **Step 1: Write README.md**

```markdown
# cmf-control

Open-source Linux desktop app to control **CMF Buds Pro 2** earbuds.

Control ANC modes, battery status, EQ presets, and touch gestures — without the official Android app.

> ⚠️ Protocol bytes are community reverse-engineered and may need calibration for your firmware version.
> Use `tools/sniff.py` to verify against your device and submit corrections via PR.

## Features

- 🎛️ ANC — Off / Transparency / Light / Max
- 🔋 Battery — Left, Right, Case
- 🎵 EQ — Balanced, Bass Boost, Treble Boost, Podcast, Gaming
- 👆 Gestures — Remap touch actions per bud

## Requirements

- Linux with BlueZ
- Python 3.11+
- CMF Buds Pro 2 paired via `bluetoothctl`

## Install

```bash
pip install cmf-control
cmf-control
```

Or from source:

```bash
git clone https://github.com/yourusername/cmf-control
cd cmf-control
pip install -e .
cmf-control
```

## Protocol

See [docs/protocol.md](docs/protocol.md). Help verify and extend it via `tools/sniff.py`.

## Contributing

PRs welcome — especially protocol corrections for newer firmware versions.

## License

MIT
```

- [ ] **Step 2: Write LICENSE (MIT)**

```
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 3: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 4: Final commit**

```bash
git add README.md LICENSE
git commit -m "docs: README and MIT license"
```

---

## ⚠️ Post-Build: Protocol Verification

Before the app will actually work on real hardware, verify the protocol bytes:

1. Enable **Bluetooth HCI snoop log** in Android developer options
2. Connect CMF Buds Pro 2 to Android, use official app (change ANC, EQ, etc.)
3. `adb pull /data/misc/bluetooth/logs/btsnoop_hci.log snoop.log`
4. `python tools/sniff.py snoop.log`
5. Compare output CMD bytes to `cmf_control/protocol/constants.py`
6. Update any mismatches and update `docs/protocol.md`
