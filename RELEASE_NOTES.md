# AI Town 1.0.0

## Highlights

- Full game loop: menu, gameplay, victory/failure ending.
- Three-story chapter campaign with clear objectives.
- Economy gameplay: production, trade, zone upgrades, daily quests.
- World simulation: autonomous NPCs, daily director events, relationship events.
- Save/load, help overlay, settings screen, and release-ready packaging scripts.
- Mouse interaction: click-to-move, click-to-talk, right-click inspect.
- Dynamic seasons and weather with gameplay impact and visual effects.
- Audio control: master/BGM/SFX with procedural built-in chiptune BGM.

## Performance

- Sprite scaling cache added to reduce per-frame transform cost.
- Asset fallback path keeps game playable without optional resources.

## Build

- Windows build script: `scripts/build_windows.ps1`
- SteamPipe templates: `steam/*.vdf`

## 1.0.1 Playability Patch

- Fixed packaged build asset path resolution for PyInstaller runtime.
- Save data and settings moved to `%LOCALAPPDATA%\\AITown` for stable write access.
- Added keyboard-first menu flow: `W/S` `Up/Down` navigate, `Enter/Space` confirm.
- Added gameplay pause (`P`), directional key movement, and `Shift` sprint.
- Settings screen now returns to the previous scene instead of always jumping to menu.
- Added interaction context prompt and stronger HUD/menu readability.

## 1.1.0 Pixel Farm Upgrade

- Added chapter completion assist gates to prevent hard lock in long runs.
- Added emergency rescue before hard failure in mid/late game.
- Added live chapter tracker with visual progress bars in gameplay HUD.
- Upgraded world rendering style toward pixel-farm look:
  - checker grass base, road markings, zone level badges, water stripe details.
  - pixelated world-layer upscale pass for retro visual identity.
- Upgraded UI polish:
  - richer story tracker bar, improved settings palette, clearer log bullets.
- Added tests for campaign assist and progress ratio stability.

## 1.1.1 Asset Compliance Guard

- Downloaded and reviewed two external reference repositories:
  - `Huu-Yuu/StardewValley-Assets`
  - `Huu-Yuu/PixelSRPG-Forge`
- Added release-time license guard to block risky asset names from shipping folders.
- Integrated guard into both:
  - `scripts/release_check.py`
  - `scripts/build_windows.ps1`
- Added tests for guard behavior and added evaluation note document.
