# AITown

`AITown` is a compact single-player simulation game prototype built with Python and `pygame`.

This public repository is curated for portfolio use. It focuses on game architecture, progression systems, release tooling, and test coverage without including local build outputs or external scratch assets.

## Highlights

- complete gameplay loop with menu, simulation, progression, and ending states
- autonomous NPC behavior and event-driven world updates
- economy, production, trade, and district upgrade systems
- save/load support and configurable settings
- Windows packaging helpers and Steam upload templates
- smoke checks and gameplay regression tests

## Repository Layout

```text
.
|-- README.md
|-- PROJECT_STRUCTURE.md
|-- pyproject.toml
|-- requirements.txt
|-- requirements-dev.txt
|-- RELEASE_NOTES.md
|-- THIRD_PARTY_LICENSES.md
|-- main.py
|-- aitown/
|-- assets/
|-- docs/
|-- scripts/
|-- steam/
`-- tests/
```

## Quick Start

```bash
python -m pip install -r requirements.txt
python main.py
```

## Development

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
python scripts/smoke_test.py
```

## Controls

- `Enter` or `Space`: confirm menu actions
- `W/A/S/D` or arrow keys: move
- left mouse: move or interact
- right mouse: inspect a nearby NPC
- `E`: talk
- `Q`: inspect NPC status
- `B`: build decoration
- `U`: upgrade current zone
- `R`: produce goods
- `T`: trade
- `F`: trigger festival
- `K`: claim completed quest rewards
- `G`: toggle tax policy
- `H`: toggle help overlay
- `O`: open settings
- `Tab`: toggle information panel
- `F5` / `F9`: save / load
- `P`: pause
- `Esc`: back / exit current screen

## Build and Release

Windows packaging helper:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1 -Version 1.0.0 -SteamAppId <APP_ID>
```

Steam upload templates are provided in `steam/`.

## Public Snapshot Policy

This public version excludes:

- local virtual environments
- build outputs
- release bundles
- temporary caches
- unverified external asset dumps

The goal is to present a clean portfolio-grade codebase rather than a machine backup.
