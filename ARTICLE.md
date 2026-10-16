# How I Reverse Engineered CMF Buds Pro 2 Bluetooth Protocol to Build a Linux Companion App

*Or: how BLE betrayed me, RFCOMM saved me, and Nothing's protocol turned out to be surprisingly hackable.*

---

## The Problem

I use Linux. I own CMF Buds Pro 2.

Nothing ships companion apps for Windows, Mac, and Android. Linux? Nothing. (Yes, the pun is intended and it never gets old.)

Every time I sat down to work, my ANC was stuck at whatever mode I'd last set from my phone. My EQ was frozen. My gestures were whatever Windows had last configured. I had to pick up my phone just to change ANC mode on my earbuds while sitting at my Linux machine.

That's unacceptable. So I fixed it.

---

## First Attempt: BLE GATT

CMF Buds Pro 2 advertises a BLE service. Logical first move — connect via BLE and read characteristics.

I wrote a brute-force prober using `bleak` (Python BLE library) that iterated over every characteristic and read/notified everything it could find.

Results: 16 bytes of random garbage. Every single characteristic. Every single read.

Everything was encrypted. No pairing key, no documentation, no way in. BLE was a dead end.

---

## The Breakthrough: RFCOMM

While digging through existing tools, I found **BudsLink** — a GNOME Shell extension for Nothing earbuds by maniacx. It was doing something completely different: connecting via **classic Bluetooth RFCOMM** using BlueZ's D-Bus ProfileManager1.

Classic Bluetooth. Not BLE. The old protocol that smartphones used before everything went BLE.

I wired up a quick test:

```python
import dbus
import dbus.mainloop.glib
from gi.repository import GLib

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()
mgr = dbus.Interface(bus.get_object("org.bluez", "/org/bluez"), "org.bluez.ProfileManager1")
mgr.RegisterProfile("/org/test/profile0", "aeac4a03-dff5-498f-843a-34487cf133eb", {})
```

I got an RFCOMM file descriptor back. I read from it. The first bytes: `0x55 0x60 0x01 ...`

`0x55` — that's the SOF (Start of Frame) byte I'd seen in BudsLink's source. **We were in.**

---

## Decoding the Protocol

From BudsLink's JavaScript and APK decompilation (looking at `Message.java`), I pieced together the wire format:

```
[0x55] [ctrl: 2B LE] [cmd: 2B LE] [len: 2B LE] [fsn: 1B] [payload: nB] [CRC: 2B]
```

- `ctrl` = `0x0160` — `CTRL_MULTIFRAME (0x40) | CTRL_CRC (0x20)` in low byte, device type `0x01` in high byte
- `cmd` = command code (different for GET vs SET — more on this below)
- `len` = payload byte count
- `fsn` = frame sequence number (0-255, wraps)
- `CRC` = present but device uses an unconfirmed variant — we skip validation (BudsLink does too)

### The GET vs SET Trap

This one burned us for hours. We assumed GET and SET commands shared the same command code (just with different payloads). Wrong.

They're completely different codes:

| Feature | GET | SET |
|---------|-----|-----|
| ANC | `0xC01E` | `0xF00F` |
| EQ | `0xC01F` | `0xF01D`* |
| Game Mode | `0xC041` | `0xF040` |
| Spatial Audio | `0xC04F` | `0xF052` |
| In-Ear | `0xC00E` | `0xF004` |

*CMF Buds Pro 2 uses `LISTENING_MODE_SET` (`0xF01D`) for EQ, not the generic `EQ_SET` (`0xF010`). Found this in BudsLink's device config: `eqListeningModeType: true`.

Response commands have **bit 15 cleared**: `0xC007` (battery request) → `0x4007` (battery response). Match with `cmd & 0x7FFF`.

### ANC Modes

The ANC payload is a series of 3-byte tuples: `(type, value, padding)`. Type `1` = noise reduction mode.

Values from BudsLink's CMFBudsPro2.js:
```python
ANC_VAL_OFF          = 0x05
ANC_VAL_PASS_THROUGH = 0x07  # transparency
ANC_VAL_STRONG       = 0x01  # max ANC
ANC_VAL_MEDIUM       = 0x02
ANC_VAL_WEAK         = 0x03  # light ANC
ANC_VAL_ADAPTIVE     = 0x04
```

### Battery Payload

Battery is a count-prefixed key-value SparseArray:
```
[count] [key] [val] [key] [val] ...
```
Keys: `2=left`, `3=right`, `4=case`. Value's lower 7 bits = percentage, bit 7 = charging flag.

---

## Building the App

With the protocol cracked, the app came together fast.

**Stack:**
- Python 3 (system Python — pyenv doesn't have `gi`/`dbus-python`)
- PyQt6 for UI
- `dbus-python` + `PyGObject` for BlueZ
- Direct `os.read/write` on the RFCOMM file descriptor

**Architecture:**
- `BTSession` — handles BlueZ D-Bus profile registration, RFCOMM connection, send/receive
- Feature modules (`battery.py`, `anc.py`, `eq.py`, etc.) — thin wrappers over `session.send()`
- PyQt6 UI with `QThread` for connection, background threads for all device I/O
- `QTimer.singleShot` to marshal device responses back to the main UI thread

**Key implementation detail:** SET commands don't always get responses from the device. Using `send_nowait()` (fire and forget) for all SET operations, `send()` (wait for response) only for GETs.

**The UUID registration problem:** BlueZ tracks RFCOMM profiles by D-Bus connection, not just path. If the app crashes without unregistering, BlueZ holds the ghost registration. The fix: always `UnregisterProfile` before `RegisterProfile` in `connect()`, and auto-restart `bluetoothd` via passwordless sudo if that fails.

---

## The UI

Nothing's design language is distinct: pure black, dot matrix grid, monospace fonts, minimal chrome. I tried to match it.

Built with PyQt6:
- Custom `DotMatrixBackground` widget paints a `16px` dot grid across the entire window
- Animated red `●` dot in the header pulses while searching, turns solid Nothing-red `#FF1744` on connect
- Pill toggle switches with `QPropertyAnimation` for smooth transitions
- Segmented control buttons for ANC and EQ (joined borders, rounded only at ends)
- System tray icon — app lives in background, connects automatically

---

## What Works

✅ Battery levels (L/R/Case) with live polling  
✅ ANC control (5 modes)  
✅ EQ presets (6 presets)  
✅ Game mode (low latency)  
✅ Spatial audio toggle  
✅ In-ear detection toggle  
✅ Bass enhance with level slider  
✅ Touch gesture remapping (commands verified, format from BudsLink)  
✅ System tray + autostart  
✅ Auto-reconnect when buds come in range  

---

## What's Next

- Verify gesture remapping on more devices
- "Find My Buds" ring feature
- Firmware version display
- Package as `.deb` for easy install
- Submit to Nothing Archive community apps

---

## Try It

**GitHub:** https://github.com/JScoder4005/cmf-control

```bash
sudo apt install python3-dbus python3-gi python3-pyqt6
git clone https://github.com/JScoder4005/cmf-control
cd cmf-control
sudo pip3 install -e . --break-system-packages
```

If you own CMF Buds Pro 2 and use Linux — this is for you. If something's broken, open an issue. If you want to help, PRs are open.

---

*Built with Python, stubbornness, and a lot of Wireshark sessions that turned out to be completely useless because BLE was encrypted the whole time.*

---

**Tags:** `linux` `bluetooth` `reverse-engineering` `python` `cmf-buds` `nothing-tech` `pyqt6` `open-source`
