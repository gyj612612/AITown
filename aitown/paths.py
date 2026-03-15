from __future__ import annotations

import os
import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resource_root() -> Path:
    # PyInstaller exposes bundled data under _MEIPASS.
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return project_root()


def resolve_resource(*parts: str) -> Path:
    candidates = [
        resource_root(),
        resource_root() / "_internal",
        project_root(),
        Path.cwd(),
    ]
    for base in candidates:
        candidate = base.joinpath(*parts)
        if candidate.exists():
            return candidate
    return resource_root().joinpath(*parts)


def user_data_dir(app_name: str = "AITown") -> Path:
    base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
    if base:
        path = Path(base) / app_name
    else:
        path = Path.home() / f".{app_name.lower()}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def user_data_file(filename: str, app_name: str = "AITown") -> Path:
    return user_data_dir(app_name) / filename
