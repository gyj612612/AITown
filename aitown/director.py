from __future__ import annotations

import random
from typing import List

from .models import NPC, TownState, WorldEvent


class WorldDirector:
    THEMES = ("growth", "culture", "pressure", "innovation")
    SEASONS = ("spring", "summer", "autumn", "winter")

    def __init__(self, seed: int = 7) -> None:
        self.random = random.Random(seed)
        self._last_day = 1

    def advance_time(self, town: TownState, delta_minutes: float) -> bool:
        previous_day = town.day
        town.minute_of_day += int(delta_minutes)
        while town.minute_of_day >= 24 * 60:
            town.minute_of_day -= 24 * 60
            town.day += 1
        return town.day != previous_day

    def run_daily_settlement(self, town: TownState, npcs: List[NPC]) -> List[WorldEvent]:
        town.season = self.season_for_day(town.day)
        town.weather, town.weather_intensity = self._pick_weather(town.season)
        town.weekly_theme = self._pick_theme(town.day)
        events = self._generate_events(town)
        self._apply_event_impacts(town, events, npcs)
        self._apply_weather_impacts(town, npcs)
        town.active_events = events
        for event in events:
            town.event_feed.append(f"Day {town.day}: {event.title} - {event.description}")
        town.event_feed.append(
            f"Day {town.day}: 季节 {town.season} / 天气 {town.weather} ({town.weather_intensity:.2f})"
        )
        town.event_feed = town.event_feed[-18:]
        self._nudge_baseline(town)
        self._last_day = town.day
        return events

    def season_for_day(self, day: int) -> str:
        # 每10天切换季节，形成40天一轮回。
        idx = ((day - 1) // 10) % len(self.SEASONS)
        return self.SEASONS[idx]

    def _pick_theme(self, day: int) -> str:
        # 每7天一个主题，但允许轻微随机偏移，避免死板重复。
        base_index = ((day - 1) // 7) % len(self.THEMES)
        if self.random.random() < 0.2:
            base_index = self.random.randint(0, len(self.THEMES) - 1)
        return self.THEMES[base_index]

    def _generate_events(self, town: TownState) -> List[WorldEvent]:
        templates = {
            "growth": [
                ("startup_fair", "创业市集", "新摊位增加，商业活力提升。", 0.05, 0.01, 0.0, 0.03),
                ("job_wave", "招聘潮", "多家店铺扩张，岗位数量上升。", 0.06, 0.0, 0.01, 0.02),
                ("supply_cost", "原料涨价", "成本抬升，商家利润被压缩。", -0.04, 0.0, 0.0, -0.02),
            ],
            "culture": [
                ("night_festival", "夜光节", "居民夜间活动热情高涨。", 0.02, 0.08, 0.0, 0.06),
                ("street_show", "街头演出周", "文化区人流提升，社交频率上升。", 0.01, 0.07, 0.0, 0.04),
                ("noise_complaint", "噪音投诉", "部分居民对夜间活动不满。", -0.01, -0.03, -0.01, -0.03),
            ],
            "pressure": [
                ("rainstorm", "暴雨预警", "外出减少，通勤受阻。", -0.03, -0.02, -0.02, -0.04),
                ("rumor_spread", "谣言扩散", "关系紧张上升，社交信任下降。", -0.02, -0.01, -0.04, -0.05),
                ("security_patrol", "联合巡逻", "治安加强，夜间安全感上升。", -0.01, 0.0, 0.05, 0.02),
            ],
            "innovation": [
                ("maker_day", "创客开放日", "工坊产能与创作热度提升。", 0.04, 0.05, 0.01, 0.05),
                ("ai_salon", "AI交流会", "跨职业合作增多。", 0.03, 0.04, 0.0, 0.05),
                ("tool_failure", "设备故障", "部分生产活动被迫中断。", -0.04, -0.01, 0.0, -0.03),
            ],
        }

        picks = templates.get(town.weekly_theme, templates["growth"])
        chosen = self.random.sample(picks, k=2)
        events: List[WorldEvent] = []
        for idx, raw in enumerate(chosen, start=1):
            event = WorldEvent(
                event_id=f"d{town.day}-{idx}-{raw[0]}",
                title=raw[1],
                description=raw[2],
                impact_economy=raw[3],
                impact_culture=raw[4],
                impact_safety=raw[5],
                mood_bias=raw[6],
            )
            events.append(event)
        return events

    def _apply_event_impacts(self, town: TownState, events: List[WorldEvent], npcs: List[NPC]) -> None:
        econ_delta = sum(e.impact_economy for e in events)
        cul_delta = sum(e.impact_culture for e in events)
        saf_delta = sum(e.impact_safety for e in events)
        mood_delta = sum(e.mood_bias for e in events)

        town.economy = self._clamp(town.economy + econ_delta)
        town.culture = self._clamp(town.culture + cul_delta)
        town.safety = self._clamp(town.safety + saf_delta)

        for npc in npcs:
            npc.mood = self._clamp(npc.mood + mood_delta)
            npc.social = self._clamp(npc.social + cul_delta * 0.4)
            npc.wealth = self._clamp(npc.wealth + econ_delta * 0.25)

    def _nudge_baseline(self, town: TownState) -> None:
        # 让系统慢慢回归中位，避免单向漂移。
        town.economy += (0.55 - town.economy) * 0.08
        town.culture += (0.5 - town.culture) * 0.08
        town.safety += (0.58 - town.safety) * 0.08

    def _pick_weather(self, season: str) -> tuple[str, float]:
        table = {
            "spring": [("clear", 0.55), ("rain", 0.28), ("fog", 0.12), ("storm", 0.05)],
            "summer": [("clear", 0.65), ("rain", 0.20), ("storm", 0.12), ("fog", 0.03)],
            "autumn": [("clear", 0.45), ("rain", 0.30), ("fog", 0.20), ("storm", 0.05)],
            "winter": [("clear", 0.35), ("snow", 0.45), ("fog", 0.15), ("storm", 0.05)],
        }
        picks = table.get(season, table["spring"])
        roll = self.random.random()
        running = 0.0
        weather = "clear"
        for name, probability in picks:
            running += probability
            if roll <= running:
                weather = name
                break
        intensity = round(self.random.uniform(0.25, 0.95), 2)
        if weather == "clear":
            intensity = round(self.random.uniform(0.05, 0.25), 2)
        return weather, intensity

    def _apply_weather_impacts(self, town: TownState, npcs: List[NPC]) -> None:
        weather = town.weather
        intensity = town.weather_intensity
        if weather == "rain":
            town.economy = self._clamp(town.economy - 0.02 * intensity)
            town.culture = self._clamp(town.culture + 0.01 * intensity)
        elif weather == "storm":
            town.economy = self._clamp(town.economy - 0.04 * intensity)
            town.safety = self._clamp(town.safety - 0.03 * intensity)
        elif weather == "fog":
            town.safety = self._clamp(town.safety - 0.01 * intensity)
        elif weather == "snow":
            town.culture = self._clamp(town.culture + 0.02 * intensity)
            town.economy = self._clamp(town.economy - 0.01 * intensity)

        mood_shift = 0.0
        if weather in {"rain", "snow"}:
            mood_shift = 0.01 * intensity
        elif weather == "storm":
            mood_shift = -0.03 * intensity
        for npc in npcs:
            npc.mood = self._clamp(npc.mood + mood_shift)

    @staticmethod
    def _clamp(v: float) -> float:
        return max(0.0, min(1.0, v))
