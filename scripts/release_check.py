from __future__ import annotations

from pathlib import Path

from license_guard import run_guard

REQUIRED_FILES = [
    "main.py",
    "requirements.txt",
    "README.md",
    "assets/sprites/player.png",
    "assets/sprites/background.png",
    "assets/licenses/platformer_art_complete_pack_LICENSE.txt",
    "assets/licenses/kenney_ui_pack_LICENSE.txt",
    "steam/app_build_aitown.vdf",
    "steam/depot_build_aitown_windows.vdf",
    "scripts/smoke_test.py",
]


def main() -> int:
    missing = [item for item in REQUIRED_FILES if not Path(item).exists()]
    if missing:
        print("Release check failed. Missing files:")
        for item in missing:
            print(f" - {item}")
        return 1

    notes = Path("RELEASE_NOTES.md")
    if not notes.exists():
        print("Release check failed: RELEASE_NOTES.md not found.")
        return 1

    ok, violations = run_guard()
    if not ok:
        print("Release check failed: license guard detected risky files:")
        for item in violations:
            print(f" - {item}")
        return 1

    print("Release check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
