# CMF Control

> Linux companion app for CMF Buds Pro 2 earbuds

![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Platform](https://img.shields.io/badge/platform-Linux-lightgrey) ![License](https://img.shields.io/badge/license-MIT-green)

![CMF Control](assets/screenshot.png)
*(screenshot coming soon)*

---

## Features

- **Battery** — Live L / R / Case levels with 30s polling
- **Noise Control** — Off / Transparency / Light / Medium / Max ANC
- **Sound Profile** — Balanced / Rock / Electronic / Pop / Enhance Vocals / Classical
- **Game Mode** — Low-latency toggle
- **Spatial Audio** — Toggle on/off
- **In-Ear Detection** — Toggle on/off
- **Bass Enhance** — Enable + 0–5 level slider
- **Touch Controls** — Remap double tap, triple tap, hold per earbud
- **System tray** — Runs in background, click to show/hide
- **Auto-connect** — Detects buds when they come in range, no manual step
- **Launches on login** — Desktop entry + autostart entry installed automatically

---

## Requirements

- Ubuntu / Debian Linux (or any distro with BlueZ + D-Bus)
- Python 3.10+ (**system** `/usr/bin/python3` — not pyenv or virtualenv)
- BlueZ (installed by default on Ubuntu)
- `python3-dbus`, `python3-gi`, `python3-pyqt6`

---

## Installation

```bash
# Install system dependencies
sudo apt install python3-dbus python3-gi python3-pyqt6

# Clone and install
git clone https://github.com/JScoder4005/cmf-control
cd cmf-control
sudo pip3 install -e . --break-system-packages

# One-time: allow app to restart bluetooth on stale UUID error
echo "$USER ALL=(ALL) NOPASSWD: /bin/systemctl restart bluetooth" | sudo tee /etc/sudoers.d/cmf-bluetooth
sudo chmod 440 /etc/sudoers.d/cmf-bluetooth
```

Pair your buds first if you haven't already:

```bash
bluetoothctl
> scan on
> pair 2C:BE:EE:F0:00:3C
> trust 2C:BE:EE:F0:00:3C
> connect 2C:BE:EE:F0:00:3C
```

---

## Running

```bash
/usr/bin/python3 -c "from cmf_control.ui.app import run; import sys; sys.exit(run())"
```

Or search **CMF Control** in GNOME Activities after first run (desktop entry is installed automatically).

---

## How it works

CMF Buds Pro 2 exposes two Bluetooth interfaces:

- **BLE GATT** — encrypted, responses are random-looking 16-byte blobs. Unusable without the encryption key.
- **Classic Bluetooth RFCOMM** — plaintext, full bidirectional protocol. This is what the official Android app uses.

CMF Control connects via BlueZ's D-Bus `ProfileManager1` API using the proprietary RFCOMM UUID:

```
aeac4a03-dff5-498f-843a-34487cf133eb
```

**Wire format** (reverse engineered from APK decompilation + BudsLink source):

```
SOF(0x55) | ctrl(2B LE) | cmd(2B LE) | len(2B LE) | fsn(1B) | payload(nB) | CRC(2B)
```

Key discovery: GET and SET use **different command codes**. Example:

| Operation | Command |
|-----------|---------|
| ANC GET   | `0xC01E` |
| ANC SET   | `0xF00F` |
| EQ GET    | `0xC01F` |
| EQ SET    | `0xF01D` |

Response commands have bit 15 cleared (`0xC01E` → `0x401E`).

---

## Known Limitations

- Touch gesture changes are sent to device but not verified on all firmware versions
- CRC validation skipped on decode — device uses an unconfirmed CRC variant
- Buds must be paired via `bluetoothctl` before first use
- Tested on Ubuntu 24.04 with CMF Buds Pro 2 firmware B172

---

## Acknowledgements

- [BudsLink](https://github.com/maniacx/BudsLink) by maniacx — GNOME extension that confirmed RFCOMM works and provided protocol reference
- [Nothing Archive](https://nothingarchive.tech) — community firmware and device documentation

---

## License

MIT — see [LICENSE](LICENSE)
