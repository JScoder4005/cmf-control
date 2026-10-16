# macOS Transport Backend — Design

Date: 2026-10-16
Status: Approved by project owner, ready for implementation planning.

## Context

cmf-control is a reverse-engineered companion app for CMF Buds Pro 2, currently
Linux-only. All platform-specific Bluetooth code is isolated in `cmf_control/bt/`:

- `bt/scanner.py` — shells out to `bluetoothctl devices`, filters by name regex.
- `bt/session.py` — `BTSession` class: registers a BlueZ `Profile1` D-Bus object,
  calls `ProfileManager1.RegisterProfile` + `Device1.ConnectProfile`, receives a
  raw RFCOMM fd via `NewConnection`, then does `os.read`/`os.write`/`select` on
  that fd directly. A background thread runs a GLib `MainLoop` to service D-Bus
  callbacks; a `concurrent.futures.Future` bridges the async `NewConnection`
  callback back to a synchronous `connect()` call.

Everything else — `protocol/codec.py`, `features/*`, `ui/*` (PyQt6) — only calls
`BTSession.connect/disconnect/send/send_nowait` and is platform-agnostic.

macOS has no BlueZ/D-Bus. Classic Bluetooth RFCOMM is only reachable via the
IOBluetooth framework (Objective-C), bridged into Python via
`pyobjc-framework-IOBluetooth`. IOBluetooth is delegate/callback-driven and
requires an active run loop, with no raw POSIX fd exposed.

## Scope

Personal use only (one user, one known device). No packaging, no installer
polish, no defensive handling for hardware this user doesn't own. Pairing is
to be triggered by the app itself, not pre-done via System Settings.

## Goal

Add a macOS transport backend that implements the exact same interface as the
Linux `BTSession` / `scan_devices`, so `features/*` and `ui/*` need zero
changes. Platform selection happens once, at the top (`main.py`).

## Architecture

### 1. Platform dispatch

In `main.py` (or a small factory function it calls), branch on `sys.platform`:

```python
if sys.platform == "darwin":
    from cmf_control.bt.session_macos import BTSession
    from cmf_control.bt.scanner_macos import scan_devices
else:
    from cmf_control.bt.session import BTSession
    from cmf_control.bt.scanner import scan_devices
```

Both modules export a `BTSession` class and `scan_devices(timeout)` function
with identical signatures/behavior contracts to the Linux originals. No other
file branches on platform.

### 2. `bt/scanner_macos.py`

Use `IOBluetooth.IOBluetoothDeviceInquiry` for classic-Bluetooth discovery
(the mac equivalent of `bluetoothctl devices`):

- Create an inquiry, set a delegate, start it, spin `CFRunLoopRunInMode` for
  up to `timeout` seconds (inquiry delegate callbacks populate a list as
  devices are found).
- For each discovered `IOBluetoothDevice`, filter `.getName()` (or `.name`)
  against the existing `CMF_NAME_PATTERN` regex.
- Return `list[BTDevice]` using the same `BTDevice` dataclass already defined
  in `bt/scanner.py` (import it, don't redefine).

### 3. `bt/session_macos.py`

Public interface — must match Linux `BTSession` exactly:

```python
class BTSession:
    def __init__(self, address: str = CLASSIC_MAC): ...
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def send(self, cmd: int, payload: bytes = b"") -> Message: ...
    def send_nowait(self, cmd: int, payload: bytes = b"") -> None: ...
    def __enter__(self): ...
    def __exit__(self, *_): ...
```

Internals:

- **Availability guard**: mirror `_DBUS_AVAILABLE` with `_IOBT_AVAILABLE`,
  guarding the `import IOBluetooth` (via pyobjc). `connect()` raises
  `RuntimeError` with an install hint if unavailable.
- **Run loop thread**: background thread running `NSRunLoop.currentRunLoop().run()`
  (or an equivalent repeating `CFRunLoopRun`), analogous to today's
  `_glib_thread`. All IOBluetooth delegate callbacks fire on this thread.
- **Pairing**: `IOBluetoothDevice.deviceWithAddressString_(address)`. If
  `.isPaired()` is false, call `.openConnection_(delegate)` with a pairing
  delegate implementing `IOBluetoothDevicePairDelegate` methods
  (`requestPINCode`, `userConfirmationRequest`, `connectionComplete`, etc).
  Bridge completion back to the calling thread via a `concurrent.futures.Future`
  (same pattern as the existing `_fd_future`), so `connect()` blocks
  synchronously until pairing succeeds or times out.
- **RFCOMM open**: once paired, call
  `device.openRFCOMMChannelAsync_withChannelID_delegate_(uuid_or_channel_id, delegate)`.
  A second `Future` resolves when the channel delegate's
  `rfcommChannelOpenComplete_status_` fires; `connect()` blocks on it with the
  existing `CONNECT_TIMEOUT`.
- **Read path**: channel delegate's `rfcommChannelData_data_` callback appends
  incoming bytes to a thread-safe buffer (`deque` + `threading.Condition`).
  `_recv_response` waits on the condition (with the existing `RECV_TIMEOUT`
  deadline) instead of `select()` on an fd, then runs the same
  `Message.decode` / bit-15 matching loop already in the Linux version.
- **Write path**: `channel.writeSync_length_(data, len(data))` — synchronous,
  no bridging needed.
- **Disconnect**: close the RFCOMM channel (`channel.closeChannel()`), stop the
  run loop.
- Exceptions raised (`ConnectionError`, `TimeoutError`) must match the Linux
  module's types/messages closely enough that `features/*` error handling
  (none of which currently branches on platform) keeps working unchanged.

### 4. Testing

- Existing `tests/test_*.py` (codec, anc, battery, eq, gestures) are untouched
  — they only exercise `protocol/` and `features/`, never transport.
- No pytest coverage for `session_macos.py` / `scanner_macos.py`: IOBluetooth
  is an Objective-C bridge talking to real hardware and the OS Bluetooth
  daemon: mocking it isn't worth it for a personal-use scope, and the
  existing Linux `bt/session.py` has the same gap today.
- Add `tools/sniff_macos.py` (or extend `tools/sniff.py` with a platform
  branch) as a manual smoke-test entry point: connect, log raw inbound bytes.
  Verification is manual, against the real buds.

### 5. Dependencies

Add `pyobjc-framework-IOBluetooth` to mac install steps. Unlike Linux (which
requires system Python + apt-installed `python3-dbus`/`python3-gi`), pyobjc
installs normally via pip into a regular venv — no system-Python constraint
needed on mac.

## Out of scope (explicitly deferred)

- UI visual improvements — separate track, to be brainstormed independently.
- Packaging/distribution for other mac users.
- Support for any device other than the one CMF Buds Pro 2 this user owns.
