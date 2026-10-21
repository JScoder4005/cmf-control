<div align="center">

```
· · · · · · · · · · · · · · · · · · · · · · · · · · · · · · ·
·                                                           ·
·    █▀▀ █▀▄▀█ █▀▀   █▀▀ █▀█ █▄ █ ▀█▀ █▀█ █▀█ █           ·
·   █▄▄ █ ▀ █ █▀    █▄▄ █▄█ █ ▀█  █  █▀▄ █▄█ █▄▄         ·
·                                                           ·
·                   for CMF Buds Pro 2                      ·
·                      on Linux                             ·
·                                                           ·
· · · · · · · · · · · · · · · · · · · · · · · · · · · · · · ·
```

**Your CMF Buds Pro 2 deserve better than Windows.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-white?style=flat-square&logo=python&logoColor=black&labelColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Linux-black?style=flat-square&logo=linux&logoColor=white)](https://kernel.org)
[![License](https://img.shields.io/badge/License-MIT-white?style=flat-square&labelColor=black)](LICENSE)
[![PyQt6](https://img.shields.io/badge/UI-PyQt6-41CD52?style=flat-square&labelColor=black)](https://pypi.org/project/PyQt6/)
[![Bluetooth](https://img.shields.io/badge/Bluetooth-RFCOMM-0082FC?style=flat-square&labelColor=black)](https://bluez.org)

</div>

---

## Why?

CMF ships a companion app for Windows, Mac, and Android.  
**Linux? Nothing.** *(pun intended)*

ANC stuck on max. EQ locked to default. Gestures frozen since you last used Windows.  
Not anymore.

CMF Control is a fully reverse-engineered Linux companion app for the **CMF Buds Pro 2**. Built by cracking their Bluetooth protocol from scratch — no official API, no docs, no help from Nothing.

---

## Features

```
· BATTERY ···················· Live L / R / Case levels, 30s auto-poll
· BATTERY HISTORY ············ 24h discharge graph for L / R / case
· FIRMWARE VERSION ·········· Read live from device, shown in header
· SIGNAL STRENGTH ············ RSSI bars + dBm, polled every 10s
· NOISE CONTROL ············· Off / Transparency / Light / Medium / Max ANC
· SOUND PROFILE ············· Balanced / Rock / Electronic / Pop / Enhance Vocals / Classical / Custom
· CUSTOM EQ ················· Bass / mid / treble, ±6 dB — stored on the buds, follows them to your phone
· GAME MODE ················· Low-latency toggle
· SPATIAL AUDIO ············· Toggle on/off
· IN-EAR DETECTION ·········· Auto-pause when removed
· BASS ENHANCE ·············· Enable + 5-level slider
· SLEEP TIMER ··············· 10/20/30/45/60m presets, pauses all MPRIS players
· TOUCH CONTROLS ············ Remap double tap / triple tap / hold per earbud
· SYSTEM TRAY ··············· Lives in taskbar, always ready
· AUTO-CONNECT ·············· Detects buds when in range, no manual steps
· AUTO-RECONNECT ··········· Reconnects on its own when buds come back
· AUTOSTART ················· Launches silently on login
```

**Cold-start:** window to full state ~0.3s after launch on a warm BlueZ.

---

## Screenshot

<div align="center">
<img src="assets/screenshot.png" width="420" alt="CMF Control UI"/>

*Nothing-authentic UI — dot matrix background, red dot accent*
</div>

---

## How We Cracked It

CMF Buds Pro 2 has two Bluetooth modes: **BLE GATT** and **classic RFCOMM**.

We tried BLE first. Every response: 16 bytes of random garbage. Fully encrypted, no key, no docs. Dead end.

Then we found **BudsLink** (a GNOME extension for Nothing earbuds) using classic Bluetooth RFCOMM via BlueZ's D-Bus ProfileManager1. Tried it. Got a real `0x55`-prefixed response. The protocol was alive.

**Wire format** (reverse engineered from BudsLink + APK decompilation):
```
0x55 | ctrl(2B LE) | cmd(2B LE) | len(2B LE) | fsn(1B) | payload(nB) | CRC(2B)
```

Key discoveries:
- GET and SET are **different command codes** — ANC GET=`0xC01E`, SET=`0xF00F`
- Response cmd = request cmd with **bit 15 cleared** (`0xC007` → `0x4007`)
- CRC in device responses doesn't match standard CRC-16/ARC — skipped (BudsLink does the same)
- EQ on CMF Buds Pro 2 uses `LISTENING_MODE_SET=0xF01D`, not `EQ_SET=0xF010`
- Custom EQ = listening mode `0x06`; band gains via `0xF041` (set) / `0xC044` (get) as float32 LE, order mid/treble/bass

UUID: `aeac4a03-dff5-498f-843a-34487cf133eb`

---

## Requirements

- Ubuntu / Debian Linux (tested on Ubuntu 24.04)
- System Python `/usr/bin/python3` — **not pyenv, not venv**
- BlueZ (`bluetoothd`)
- `python3-dbus`, `python3-gi`, `python3-pyqt6`

---

## Installation

```bash
# 1. Install system dependencies
sudo apt install python3-dbus python3-gi python3-pyqt6 playerctl

# 2. Clone
git clone https://github.com/JScoder4005/cmf-control
cd cmf-control

# 3. Install
sudo pip3 install -e . --break-system-packages

# 4. Allow app to auto-recover from Bluetooth registration errors
echo "$USER ALL=(ALL) NOPASSWD: /bin/systemctl restart bluetooth" \
  | sudo tee /etc/sudoers.d/cmf-bluetooth && sudo chmod 440 /etc/sudoers.d/cmf-bluetooth

# 5. Pair buds first (if not already paired)
bluetoothctl
> scan on
> pair 2C:BE:EE:F0:00:3C
> trust 2C:BE:EE:F0:00:3C
> exit
```

---

## Running

```bash
/usr/bin/python3 -c "from cmf_control.ui.app import run; import sys; sys.exit(run())"
```

Or search **"CMF Control"** in GNOME Activities — desktop entry is installed automatically.

App opens immediately, connects in background when buds are in range. Close window → stays in system tray. Reopens on login.

---

## macOS

Transport backend swaps BlueZ/D-Bus for IOBluetooth — same `BTSession`/`scan_devices` interface, so `features/*` and `ui/*` are untouched. See `cmf_control/bt/session_macos.py` / `scanner_macos.py`.

```bash
pip install -e ".[dev]"
pip install pyobjc-framework-IOBluetooth
open "macos/CMF Control.app"
```

Pair the buds via System Settings → Bluetooth first (classic RFCOMM needs an active OS-level connection before the app's SDP lookup will succeed). First Bluetooth access shows a system permission dialog — click Allow.

Must launch via the `.app` bundle (`open`), not bare `python -m cmf_control.main` from a terminal — macOS attributes Bluetooth privacy checks to the terminal app otherwise and hard-aborts the process.

---

## Known Limitations

- Gesture remapping commands send successfully but real-device verification is ongoing
- CRC validation on incoming packets skipped (unconfirmed CRC variant)
- Buds must be paired via `bluetoothctl` before first use
- Only tested on **CMF Buds Pro 2** — other CMF/Nothing devices untested

---

## Contributing

Built by one person reverse engineering in spare time. Help wanted:

- Verify gesture remapping on your device
- Test on other Nothing/CMF earbuds
- Add firmware version display
- Add "Find My Buds" ring feature  
- Package as `.deb`

PRs welcome. Open an issue if something's broken.

---

## Acknowledgements

- [BudsLink](https://github.com/maniacx/BudsLink) by maniacx — proved RFCOMM worked, provided protocol reference
- [Nothing Archive](https://nothingarchive.tech) — community hub for the Nothing/CMF ecosystem

---

## License

MIT — do whatever you want with it.

---

<div align="center">

**If this saved your ANC settings, star the repo ⭐**

`· · · · · · · · · · · · · · · · · · · · · · · · ·`

</div>
