from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aitown.game import AITownGame  # noqa: E402


def main() -> int:
    game = AITownGame()
    game.scene = "play"
    for _ in range(120):
        game._update(1 / 60)  # noqa: SLF001 - smoke test for runtime stability
        game._render_play()  # noqa: SLF001 - smoke test for runtime stability
    pygame.quit()
    print("Smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
