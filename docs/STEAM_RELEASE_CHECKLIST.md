# Steam Release Checklist

## Before Build

- verify current version number
- update `RELEASE_NOTES.md`
- confirm third-party asset and license records are current
- run `python scripts/release_check.py`

## Build

- run `scripts/build_windows.ps1`
- confirm packaged output appears under `release/windows`
- verify startup, save/load, and menu navigation in the packaged build

## Steam Upload

- review `steam/app_build_aitown.vdf`
- review `steam/depot_build_aitown_windows.vdf`
- upload via `steamcmd`

## Final Verification

- launch the uploaded build
- verify asset loading and settings persistence
- confirm no blocked asset names or forbidden release files are present
