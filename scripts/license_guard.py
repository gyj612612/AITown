from __future__ import annotations

from pathlib import Path

BLOCKED_TOKENS = (
    "stardew",
    "concernedape",
    "pixelsrpg-forge",
    "huu-yuu",
)

CHECK_ROOTS = (
    Path("assets"),
    Path("docs"),
)

IGNORE_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".venv_build",
    "external",
    "release",
    "dist",
    "build",
}


def _contains_blocked_token(path: Path) -> bool:
    lowered = str(path).lower().replace("\\", "/")
    return any(token in lowered for token in BLOCKED_TOKENS)


def run_guard() -> tuple[bool, list[str]]:
    violations: list[str] = []
    for root in CHECK_ROOTS:
        if not root.exists():
            continue
        for item in root.rglob("*"):
            if not item.is_file():
                continue
            if any(part in IGNORE_DIRS for part in item.parts):
                continue
            if _contains_blocked_token(item):
                violations.append(str(item))
    return (len(violations) == 0, violations)


def main() -> int:
    ok, violations = run_guard()
    if ok:
        print("License guard passed.")
        return 0
    print("License guard failed. Potentially risky files detected:")
    for item in violations:
        print(f" - {item}")
    print("Remove/replace these files before release packaging.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
