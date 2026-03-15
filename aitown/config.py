from __future__ import annotations

from dataclasses import dataclass

from .paths import user_data_file


@dataclass(frozen=True)
class ScreenConfig:
    width: int = 1366
    height: int = 768
    fps: int = 60


@dataclass(frozen=True)
class SimConfig:
    minutes_per_second: float = 8.0
    player_speed: float = 220.0
    npc_speed: float = 140.0
    interaction_radius: float = 72.0
    max_feed_items: int = 12
    autosave_file: str = str(user_data_file("savegame.json"))


SCREEN = ScreenConfig()
SIM = SimConfig()


COLORS = {
    "bg_sky": (174, 215, 255),
    "bg_night": (32, 46, 71),
    "road": (170, 150, 122),
    "grass": (109, 160, 83),
    "water": (87, 146, 196),
    "zone_center": (231, 186, 112),
    "zone_residential": (160, 199, 226),
    "zone_commercial": (224, 148, 124),
    "zone_cultural": (173, 142, 216),
    "zone_industrial": (147, 147, 139),
    "panel": (24, 30, 42),
    "panel_alpha": (24, 30, 42, 200),
    "panel_line": (88, 104, 126),
    "text": (244, 247, 240),
    "text_dim": (197, 207, 196),
    "player": (244, 223, 101),
    "npc": (71, 101, 166),
    "npc_talk": (102, 142, 219),
    "event_good": (63, 178, 114),
    "event_warn": (222, 142, 62),
    "event_bad": (220, 96, 96),
}
