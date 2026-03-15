from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from .paths import user_data_file


@dataclass
class GameSettings:
    graphics_quality: str = "high"  # low / medium / high
    texture_detail: int = 2  # 0..2
    effect_level: int = 2  # 0..2
    weather_effects: bool = True
    master_volume: float = 0.8  # 0..1
    bgm_volume: float = 0.65  # 0..1
    sfx_volume: float = 0.8  # 0..1
    mouse_interaction: bool = True
    move_speed_multiplier: float = 1.0
    time_flow_multiplier: float = 1.0
    show_fps: bool = False
    fullscreen: bool = False


class SettingsManager:
    def __init__(self, path: Optional[str] = None) -> None:
        self.path = Path(path) if path else user_data_file("settings.json")

    def load(self) -> GameSettings:
        if not self.path.exists():
            return GameSettings()
        try:
            raw = self.path.read_text(encoding="utf-8")
            payload = json.loads(raw)
        except (OSError, ValueError):
            return GameSettings()
        base = GameSettings()
        quality = str(payload.get("graphics_quality", base.graphics_quality))
        if quality not in {"low", "medium", "high"}:
            quality = base.graphics_quality
        return GameSettings(
            graphics_quality=quality,
            texture_detail=self._clamp_int(payload.get("texture_detail", base.texture_detail), 0, 2),
            effect_level=self._clamp_int(payload.get("effect_level", base.effect_level), 0, 2),
            weather_effects=bool(payload.get("weather_effects", base.weather_effects)),
            master_volume=self._clamp_float(payload.get("master_volume", base.master_volume), 0.0, 1.0),
            bgm_volume=self._clamp_float(payload.get("bgm_volume", base.bgm_volume), 0.0, 1.0),
            sfx_volume=self._clamp_float(payload.get("sfx_volume", base.sfx_volume), 0.0, 1.0),
            mouse_interaction=bool(payload.get("mouse_interaction", base.mouse_interaction)),
            move_speed_multiplier=self._clamp_float(
                payload.get("move_speed_multiplier", base.move_speed_multiplier),
                0.6,
                1.8,
            ),
            time_flow_multiplier=self._clamp_float(
                payload.get("time_flow_multiplier", base.time_flow_multiplier),
                0.3,
                2.0,
            ),
            show_fps=bool(payload.get("show_fps", base.show_fps)),
            fullscreen=bool(payload.get("fullscreen", base.fullscreen)),
        )

    def save(self, settings: GameSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _clamp_float(value: object, minimum: float, maximum: float) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            parsed = minimum
        return max(minimum, min(maximum, parsed))

    @staticmethod
    def _clamp_int(value: object, minimum: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = minimum
        return max(minimum, min(maximum, parsed))
