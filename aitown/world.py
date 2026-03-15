from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pygame

from .assets import AssetPack
from .config import COLORS, SCREEN
from .models import ZoneRect


@dataclass(frozen=True)
class Zone:
    name: str
    rect: ZoneRect
    label: str
    color_key: str


class TownMap:
    def __init__(self) -> None:
        self.random = random.Random(2026)
        w, h = SCREEN.width, SCREEN.height
        self.bounds = pygame.Rect(0, 0, w, h)
        self.zones: Dict[str, Zone] = {
            "center": Zone("center", (w // 2 - 170, h // 2 - 120, 340, 240), "Town Hall", "zone_center"),
            "residential": Zone("residential", (70, 120, 320, 260), "Residences", "zone_residential"),
            "commercial": Zone("commercial", (w - 390, 130, 320, 250), "Market", "zone_commercial"),
            "cultural": Zone("cultural", (w - 370, h - 260, 300, 180), "Art District", "zone_cultural"),
            "industrial": Zone("industrial", (70, h - 250, 320, 170), "Workshop", "zone_industrial"),
        }
        self.decorations: List[Tuple[int, int, str]] = []
        self.roads: List[pygame.Rect] = [
            pygame.Rect(w // 2 - 65, 0, 130, h),
            pygame.Rect(0, h // 2 - 45, w, 90),
        ]
        self.pond = pygame.Rect(w // 2 - 280, 40, 180, 110)
        self.texture_points = [(self.random.randint(0, w - 1), self.random.randint(0, h - 1)) for _ in range(180)]
        self.clouds = [
            pygame.Rect(80, 70, 180, 48),
            pygame.Rect(w // 2 - 120, 92, 220, 56),
            pygame.Rect(w - 360, 62, 200, 52),
        ]

    def zone_at(self, x: float, y: float) -> Optional[Zone]:
        point = pygame.Rect(int(x), int(y), 1, 1)
        for zone in self.zones.values():
            if pygame.Rect(zone.rect).colliderect(point):
                return zone
        return None

    def random_point_in_zone(self, zone_name: str) -> Tuple[float, float]:
        zone = self.zones[zone_name]
        x, y, w, h = zone.rect
        return float(self.random.randint(x + 18, x + w - 18)), float(self.random.randint(y + 24, y + h - 24))

    def clamp_position(self, x: float, y: float, pad: int = 16) -> Tuple[float, float]:
        x = max(pad, min(SCREEN.width - pad, x))
        y = max(pad, min(SCREEN.height - pad, y))
        return x, y

    def add_decoration(self, x: int, y: int, deco_type: str) -> None:
        self.decorations.append((x, y, deco_type))

    def draw(
        self,
        surface: pygame.Surface,
        day_ratio: float,
        font: pygame.font.Font,
        assets: Optional[AssetPack] = None,
        *,
        season: str = "spring",
        weather: str = "clear",
        weather_intensity: float = 0.0,
        texture_detail: int = 2,
        effect_level: int = 2,
        weather_effects: bool = True,
        zone_levels: Optional[Dict[str, int]] = None,
    ) -> None:
        self._draw_background(surface, day_ratio, assets, season, texture_detail)
        self._draw_roads(surface)
        self._draw_zones(surface, font, assets, texture_detail, zone_levels)
        self._draw_decorations(surface)
        if weather_effects and effect_level > 0:
            self._draw_weather_effects(surface, weather, weather_intensity, effect_level)

    def _draw_background(
        self,
        surface: pygame.Surface,
        day_ratio: float,
        assets: Optional[AssetPack],
        season: str,
        texture_detail: int,
    ) -> None:
        c_day = COLORS["bg_sky"]
        c_night = COLORS["bg_night"]
        blend = max(0.0, min(1.0, day_ratio))
        bg = (
            int(c_night[0] + (c_day[0] - c_night[0]) * blend),
            int(c_night[1] + (c_day[1] - c_night[1]) * blend),
            int(c_night[2] + (c_day[2] - c_night[2]) * blend),
        )
        surface.fill(bg)
        tile_size = 16
        for x in range(0, SCREEN.width, tile_size):
            for y in range(0, SCREEN.height, tile_size):
                if (x // tile_size + y // tile_size) % 2 == 0:
                    pygame.draw.rect(surface, (126, 173, 109), pygame.Rect(x, y, tile_size, tile_size))
        season_tint = self._season_tint(season)
        tint_surface = pygame.Surface((SCREEN.width, SCREEN.height), pygame.SRCALPHA)
        tint_surface.fill((*season_tint, 34))
        surface.blit(tint_surface, (0, 0))
        if assets:
            bg_img = assets.get_scaled_image("background", SCREEN.width, SCREEN.height)
            if bg_img is not None:
                overlay = bg_img.copy()
                overlay.set_alpha(int(90 + 120 * blend))
                surface.blit(overlay, (0, 0))
        for cloud in self.clouds:
            cloud_surf = pygame.Surface((cloud.width, cloud.height), pygame.SRCALPHA)
            cloud_surf.fill((236, 245, 255, int(30 + 45 * blend)))
            surface.blit(cloud_surf, cloud.topleft)
        pygame.draw.rect(surface, COLORS["water"], self.pond, border_radius=18)
        for i in range(0, self.pond.width, 12):
            pygame.draw.line(
                surface,
                (168, 208, 240),
                (self.pond.x + i, self.pond.y + 8),
                (self.pond.x + i + 8, self.pond.bottom - 8),
                1,
            )
        pygame.draw.rect(surface, COLORS["grass"], pygame.Rect(0, 0, SCREEN.width, SCREEN.height), width=12)
        if texture_detail >= 2:
            for x, y in self.texture_points:
                surface.set_at((x, y), (245, 248, 255))

    def _draw_roads(self, surface: pygame.Surface) -> None:
        for road in self.roads:
            pygame.draw.rect(surface, COLORS["road"], road, border_radius=10)
            pygame.draw.rect(surface, (182, 174, 156), road, width=2, border_radius=10)
            if road.width > road.height:
                for x in range(road.x + 10, road.right - 10, 32):
                    pygame.draw.rect(surface, (236, 226, 184), pygame.Rect(x, road.centery - 2, 16, 4), border_radius=1)
            else:
                for y in range(road.y + 10, road.bottom - 10, 32):
                    pygame.draw.rect(surface, (236, 226, 184), pygame.Rect(road.centerx - 2, y, 4, 16), border_radius=1)

    def _draw_zones(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        assets: Optional[AssetPack],
        texture_detail: int,
        zone_levels: Optional[Dict[str, int]],
    ) -> None:
        grass_tile = assets.get_scaled_image("grass_tile", 30, 30) if assets else None
        for zone in self.zones.values():
            rect = pygame.Rect(zone.rect)
            pygame.draw.rect(surface, COLORS[zone.color_key], rect, border_radius=16)
            pygame.draw.rect(surface, (22, 30, 40), rect, width=3, border_radius=16)
            if texture_detail >= 1 and grass_tile is not None and zone.name in {"residential", "cultural"}:
                tile = grass_tile.copy()
                tile.set_alpha(75)
                for x in range(rect.left + 4, rect.right - 28, 30):
                    for y in range(rect.top + 24, rect.bottom - 28, 30):
                        surface.blit(tile, (x, y))
            elif texture_detail >= 1:
                for x in range(rect.left + 8, rect.right - 8, 12):
                    pygame.draw.line(surface, (236, 236, 236), (x, rect.top + 20), (x, rect.bottom - 8), 1)
            pygame.draw.rect(surface, (255, 255, 255), rect, width=2, border_radius=16)
            label = font.render(zone.label, True, (32, 44, 68))
            surface.blit(label, (rect.x + 12, rect.y + 8))
            level = 1 if zone_levels is None else int(zone_levels.get(zone.name, 1))
            badge = pygame.Rect(rect.right - 70, rect.y + 8, 58, 20)
            pygame.draw.rect(surface, (20, 31, 48), badge, border_radius=4)
            pygame.draw.rect(surface, (110, 146, 206), badge, width=1, border_radius=4)
            lv = font.render(f"Lv{level}", True, (228, 236, 250))
            surface.blit(lv, (badge.centerx - lv.get_width() // 2, badge.y + 1))

    def _draw_decorations(self, surface: pygame.Surface) -> None:
        for x, y, deco_type in self.decorations:
            if deco_type == "tree":
                pygame.draw.circle(surface, (58, 130, 74), (x, y - 9), 14)
                pygame.draw.rect(surface, (110, 83, 58), pygame.Rect(x - 3, y - 2, 6, 12), border_radius=3)
            elif deco_type == "lamp":
                pygame.draw.rect(surface, (94, 105, 112), pygame.Rect(x - 2, y - 12, 4, 16))
                pygame.draw.circle(surface, (255, 234, 149), (x, y - 16), 5)
            elif deco_type == "bench":
                pygame.draw.rect(surface, (136, 87, 59), pygame.Rect(x - 11, y - 4, 22, 8), border_radius=2)

    def _draw_weather_effects(
        self,
        surface: pygame.Surface,
        weather: str,
        intensity: float,
        effect_level: int,
    ) -> None:
        density = int((40 + intensity * 120) * effect_level)
        if weather == "rain" or weather == "storm":
            color = (170, 210, 255) if weather == "rain" else (150, 180, 220)
            for _ in range(density):
                x = self.random.randint(0, SCREEN.width)
                y = self.random.randint(0, SCREEN.height)
                pygame.draw.line(surface, color, (x, y), (x - 3, y + 9), 1)
            if weather == "storm":
                overlay = pygame.Surface((SCREEN.width, SCREEN.height), pygame.SRCALPHA)
                overlay.fill((22, 28, 50, int(25 + intensity * 45)))
                surface.blit(overlay, (0, 0))
        elif weather == "snow":
            for _ in range(density // 2):
                x = self.random.randint(0, SCREEN.width)
                y = self.random.randint(0, SCREEN.height)
                pygame.draw.circle(surface, (242, 247, 255), (x, y), 1 + (effect_level // 2))
        elif weather == "fog":
            overlay = pygame.Surface((SCREEN.width, SCREEN.height), pygame.SRCALPHA)
            overlay.fill((214, 224, 236, int(38 + intensity * 70)))
            surface.blit(overlay, (0, 0))

    @staticmethod
    def _season_tint(season: str) -> tuple[int, int, int]:
        mapping = {
            "spring": (180, 255, 210),
            "summer": (255, 246, 184),
            "autumn": (255, 214, 170),
            "winter": (200, 220, 255),
        }
        return mapping.get(season, (230, 230, 230))
