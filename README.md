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
