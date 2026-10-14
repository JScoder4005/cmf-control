# CMF Buds Pro 2 Linux Control App — Design Spec

**Date:** 2026-10-14

## Summary

Open-source Linux desktop app to control CMF Buds Pro 2 earbuds. Replaces the official Android-only app. Styled after Nothing OS dark aesthetic.

## Target

- Device: CMF Buds Pro 2
- Platform: Linux desktop
- Protocol: Bluetooth Classic RFCOMM (SPP profile) — protocol bytes TBD via reverse engineering

## Features

1. **ANC** — toggle off / transparency / light ANC / max ANC
2. **Battery** — left bud, right bud, case percentages (polled)
3. **EQ** — switch between presets (balanced, bass boost, treble boost, etc.)
4. **Gestures** — remap touch actions per bud

## Architecture

- **Language:** Python 3.11+
- **UI:** PyQt6 with custom Nothing-inspired dark stylesheet
- **Bluetooth:** Linux BlueZ via `socket` (AF_BLUETOOTH / BTPROTO_RFCOMM) — no PyBluez dependency
- **Structure:** BT session layer → protocol codec → feature modules → UI

## UI Style

Dark (#0a0a0a bg), white text, monospace/dot-matrix font (Space Mono), pill buttons, minimal chrome. Matches Nothing OS aesthetic.

## Open Source

MIT license. GitHub repo. Includes `tools/sniff.py` for community protocol contributions.
