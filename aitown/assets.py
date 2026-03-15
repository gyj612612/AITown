from __future__ import annotations

from typing import Dict, Optional

import pygame

from .paths import resolve_resource


class AssetPack:
    def __init__(self) -> None:
        self.images: Dict[str, pygame.Surface] = {}
        self.font_cache: Dict[tuple[str, int], pygame.font.Font] = {}
        self.scale_cache: Dict[tuple[str, int, int], pygame.Surface] = {}

    def load_default_pack(self) -> None:
        self.images["background"] = self._load_image("background.png")
        self.images["player"] = self._load_image("player.png")
        self.images["coin"] = self._load_image("coin.png")
        self.images["crate"] = self._load_image("crate.png")
        self.images["grass_tile"] = self._load_image("grass_tile.png")
        self.images["sign"] = self._load_image("sign.png")

    def get_image(self, key: str) -> Optional[pygame.Surface]:
        return self.images.get(key)

    def get_scaled_image(self, key: str, width: int, height: int) -> Optional[pygame.Surface]:
        cache_key = (key, width, height)
        if cache_key in self.scale_cache:
            return self.scale_cache[cache_key]
        base = self.get_image(key)
        if base is None:
            return None
        scaled = pygame.transform.scale(base, (width, height))
        self.scale_cache[cache_key] = scaled
        return scaled

    def get_font(self, size: int, fallback_name: str = "microsoftyaheiui") -> pygame.font.Font:
        ttf_file = resolve_resource("assets", "fonts", "NotoSansSC-Regular.ttf")
        cache_key = (str(ttf_file), size)
        if ttf_file.exists():
            font = self.font_cache.get(cache_key)
            if font is None:
                font = pygame.font.Font(str(ttf_file), size)
                self.font_cache[cache_key] = font
            return font
        return pygame.font.SysFont(fallback_name, size) or pygame.font.Font(None, size)

    def _load_image(self, filename: str) -> Optional[pygame.Surface]:
        path = resolve_resource("assets", "sprites", filename)
        if not path.exists():
            return None
        try:
            image = pygame.image.load(str(path)).convert_alpha()
            return image
        except pygame.error:
            return None
