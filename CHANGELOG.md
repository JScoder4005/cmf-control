# Changelog

## v0.2.0 — 2026-10-29

### Added
- macOS support via IOBluetooth transport backend
- Menu bar battery display and ANC quick-toggle
- Rich tray menu with battery, ANC and EQ controls
- Firmware version, RSSI signal strength and 24h battery history graph
- Sleep timer that pauses all MPRIS players
- MPRIS now-playing widget with artwork
- 3-band custom EQ (bass / mid / treble, ±6 dB) with dot-matrix faders
- Device badge, ANC icons and battery color coding
- Product photo header badge and system tray icon
- `.deb` packaging and tag-triggered GitHub release workflow

### Changed
- Linux cold-start cut from ~25s to ~0.3s; RFCOMM lifecycle stabilized
- README rewritten with screenshots, macOS docs and dev workflow

### Fixed
- Permanent UI freeze on macOS from nested NSRunLoop spins inside Qt's loop
- Connect now fails fast instead of hanging
- UI resets correctly on disconnect
- CI: install libEGL for pytest-qt on ubuntu-latest

## v0.1.0 — 2026-10-16

- Initial release: battery, ANC, sound profiles, game mode, spatial audio, in-ear detection, bass enhance, touch controls, tray, auto-connect/reconnect, autostart
