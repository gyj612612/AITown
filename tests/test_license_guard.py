from __future__ import annotations

from pathlib import Path

import scripts.license_guard as guard


def test_license_guard_detects_risky_name(tmp_path: Path, monkeypatch) -> None:
    assets_root = tmp_path / "assets"
    assets_root.mkdir(parents=True, exist_ok=True)
    risky = assets_root / "ui_stardew_mock.png"
    risky.write_text("x", encoding="utf-8")

    monkeypatch.setattr(guard, "CHECK_ROOTS", (assets_root,))
    ok, violations = guard.run_guard()
    assert ok is False
    assert violations


def test_license_guard_passes_clean_paths(tmp_path: Path, monkeypatch) -> None:
    assets_root = tmp_path / "assets"
    assets_root.mkdir(parents=True, exist_ok=True)
    clean = assets_root / "tile_grass.png"
    clean.write_text("x", encoding="utf-8")

    monkeypatch.setattr(guard, "CHECK_ROOTS", (assets_root,))
    ok, violations = guard.run_guard()
    assert ok is True
    assert violations == []
