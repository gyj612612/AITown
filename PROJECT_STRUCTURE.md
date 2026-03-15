# AITown Structure

## Included in Public Repository

- `README.md`
- `PROJECT_STRUCTURE.md`
- `pyproject.toml`
- `requirements.txt`
- `requirements-dev.txt`
- `.gitignore`
- `main.py`
- `aitown/`
- `assets/`
- `docs/`
- `scripts/`
- `steam/`
- `tests/`
- `RELEASE_NOTES.md`
- `THIRD_PARTY_LICENSES.md`

## Excluded from Public Repository

- `.venv_build/`
- `external/`
- `build/`
- `dist/`
- `release/`
- `steam_build_output/`
- caches such as `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`
- local save files

## Core Areas

### `aitown/`

- game loop
- simulation state
- campaign progression
- NPC and world logic
- persistence and settings
- audio and asset loading

### `tests/`

- core gameplay checks
- campaign assistance checks
- release/license guard checks
- playability checks

### `scripts/`

- smoke test
- release validation
- Windows build helper
- license guard

### `steam/`

- upload templates
- release notes for Steam packaging flow

## Publishing Intent

This public repository is intended to showcase:

- complete single-player application architecture
- gameplay/system design implemented in code
- automated checks and release tooling
- packaging awareness for distribution
