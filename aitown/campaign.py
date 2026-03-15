from __future__ import annotations

import random
from typing import List, Optional, Tuple

from .models import NPC, PlayerState, TownState


class CampaignSystem:
    def __init__(self, seed: int = 211) -> None:
        self.random = random.Random(seed)

    def ensure_story(self, town: TownState) -> None:
        _chapter, title, objective = self._chapter_meta(town.story.chapter)
        town.story.title = title
        town.story.objective = objective
        if not town.story.history:
            town.story.history.append(f"Day {town.day}: {title} 开始")

    def evaluate_progress(self, player: PlayerState, town: TownState) -> Optional[str]:
        if town.story.completed or town.story.failed:
            return None

        chapter = town.story.chapter
        actions = player.total_actions
        targets = self._chapter_targets(chapter)

        if chapter == 1:
            passed = (
                actions["build"] >= targets["build"]
                and actions["talk"] >= targets["talk"]
                and actions["produce"] >= targets["produce"]
            )
            if passed:
                return self._advance_chapter(town)
        elif chapter == 2:
            passed = (
                town.economy >= targets["economy"]
                and actions["trade"] >= targets["trade"]
                and player.coins >= targets["coins"]
                and town.zone_levels.get("commercial", 1) >= targets["commercial_level"]
            )
            if passed:
                return self._advance_chapter(town)
        elif chapter == 3:
            level3_count = sum(1 for level in town.zone_levels.values() if level >= 3)
            passed = (
                town.culture >= targets["culture"]
                and town.safety >= targets["safety"]
                and player.reputation >= targets["reputation"]
                and actions["festival"] >= targets["festival"]
                and level3_count >= targets["level3_zones"]
            )
            if passed:
                town.story.completed = True
                town.story.title = "终章完成：AI小镇新纪元"
                town.story.objective = "通关成功"
                town.story.history.append(f"Day {town.day}: 小镇达到繁荣稳定，故事完结")
                return "主线完成：你已将AI小镇建设成高活力社区。"
        return None

    def evaluate_failure(self, town: TownState, player: PlayerState) -> Optional[str]:
        if town.story.completed or town.story.failed:
            return None

        if town.economy < 0.20 or town.safety < 0.20 or player.coins < -40:
            town.story.danger_days += 1
        else:
            town.story.danger_days = max(0, town.story.danger_days - 1)

        if town.story.danger_days < 3:
            return None

        rescue_tag = f"[rescue-c{town.story.chapter}]"
        if rescue_tag not in town.story.history and town.day >= 6:
            town.story.history.append(rescue_tag)
            town.story.danger_days = 0
            town.economy = self._clamp(max(town.economy, 0.36))
            town.safety = self._clamp(max(town.safety, 0.36))
            player.coins = max(player.coins, 80)
            player.reputation = self._clamp(max(player.reputation, 0.45))
            return "紧急托底触发：财政援助与治安干预已生效。"

        town.story.failed = True
        reason = "经济或治安连续崩盘，小镇进入停摆。"
        town.story.fail_reason = reason
        town.story.history.append(f"Day {town.day}: {reason}")
        return f"失败：{reason}"

    def apply_completion_assist(self, town: TownState, player: PlayerState) -> Optional[str]:
        if town.story.completed or town.story.failed:
            return None

        chapter = town.story.chapter
        day_gate = {1: 8, 2: 22, 3: 36}.get(chapter, 9999)
        if town.day < day_gate:
            return None

        assist_tag = f"[assist-c{chapter}]"
        if assist_tag in town.story.history:
            return None

        targets = self._chapter_targets(chapter)
        if chapter == 1:
            player.total_actions["build"] = max(player.total_actions["build"], targets["build"])
            player.total_actions["talk"] = max(player.total_actions["talk"], targets["talk"])
            player.total_actions["produce"] = max(player.total_actions["produce"], targets["produce"])
            msg = "新手托底：已补齐第一章基础行动要求。"
        elif chapter == 2:
            town.economy = self._clamp(max(town.economy, targets["economy"]))
            player.total_actions["trade"] = max(player.total_actions["trade"], targets["trade"])
            player.coins = max(player.coins, int(targets["coins"]))
            if town.zone_levels.get("commercial", 1) < targets["commercial_level"]:
                town.zone_levels["commercial"] = int(targets["commercial_level"])
            msg = "发展托底：已补齐第二章关键经营条件。"
        else:
            town.culture = self._clamp(max(town.culture, targets["culture"]))
            town.safety = self._clamp(max(town.safety, targets["safety"]))
            player.reputation = self._clamp(max(player.reputation, targets["reputation"]))
            player.total_actions["festival"] = max(player.total_actions["festival"], targets["festival"])
            upgraded = 0
            for zone in ("center", "commercial", "cultural", "residential", "industrial"):
                if town.zone_levels.get(zone, 1) < 3 and upgraded < targets["level3_zones"]:
                    town.zone_levels[zone] = 3
                    upgraded += 1
            msg = "终章托底：已补齐第三章达成阈值。"

        town.story.history.append(assist_tag)
        return msg

    def chapter_progress(self, town: TownState, player: PlayerState) -> tuple[float, list[tuple[str, float]]]:
        chapter = town.story.chapter
        targets = self._chapter_targets(chapter)
        actions = player.total_actions
        rows: list[tuple[str, float]] = []

        if chapter == 1:
            rows.append((f"建设 {actions['build']}/{int(targets['build'])}", self._ratio(actions["build"], targets["build"])))
            rows.append((f"对话 {actions['talk']}/{int(targets['talk'])}", self._ratio(actions["talk"], targets["talk"])))
            rows.append((f"生产 {actions['produce']}/{int(targets['produce'])}", self._ratio(actions["produce"], targets["produce"])))
        elif chapter == 2:
            rows.append((f"经济 {town.economy:.2f}/{targets['economy']:.2f}", self._ratio(town.economy, targets["economy"])))
            rows.append((f"交易 {actions['trade']}/{int(targets['trade'])}", self._ratio(actions["trade"], targets["trade"])))
            rows.append((f"金币 {player.coins}/{int(targets['coins'])}", self._ratio(player.coins, targets["coins"])))
            rows.append(
                (
                    f"商业区 Lv{town.zone_levels.get('commercial', 1)}/{int(targets['commercial_level'])}",
                    self._ratio(town.zone_levels.get("commercial", 1), targets["commercial_level"]),
                )
            )
        else:
            level3_count = sum(1 for level in town.zone_levels.values() if level >= 3)
            rows.append((f"文化 {town.culture:.2f}/{targets['culture']:.2f}", self._ratio(town.culture, targets["culture"])))
            rows.append((f"治安 {town.safety:.2f}/{targets['safety']:.2f}", self._ratio(town.safety, targets["safety"])))
            rows.append((f"声望 {player.reputation:.2f}/{targets['reputation']:.2f}", self._ratio(player.reputation, targets["reputation"])))
            rows.append((f"节庆 {actions['festival']}/{int(targets['festival'])}", self._ratio(actions["festival"], targets["festival"])))
            rows.append((f"Lv3区域 {level3_count}/{int(targets['level3_zones'])}", self._ratio(level3_count, targets["level3_zones"])))

        overall = 1.0 if not rows else sum(v for _label, v in rows) / len(rows)
        return overall, rows

    def attempt_zone_upgrade(self, town: TownState, player: PlayerState, zone_name: Optional[str]) -> Tuple[bool, str]:
        if zone_name is None or zone_name not in town.zone_levels:
            return False, "升级失败：请站在可升级区域内。"
        level = town.zone_levels[zone_name]
        if level >= 4:
            return False, f"{zone_name} 区域已达最高等级。"
        cost = self.upgrade_cost(level)
        if player.coins < cost:
            return False, f"升级失败：需要{cost}金币。"

        player.coins -= cost
        town.zone_levels[zone_name] = level + 1
        self._apply_upgrade_bonus(town, player, zone_name, level + 1)
        return True, f"{zone_name} 升级到 Lv{level + 1}，花费{cost}金币。"

    def apply_zone_effects(self, town: TownState, player: PlayerState, delta_minutes: float) -> None:
        factor = delta_minutes / 60.0
        levels = town.zone_levels
        town.economy = self._clamp(
            town.economy
            + (levels["commercial"] - 1) * 0.0018 * factor
            + (levels["industrial"] - 1) * 0.0015 * factor
        )
        town.culture = self._clamp(
            town.culture
            + (levels["cultural"] - 1) * 0.0019 * factor
            + (levels["center"] - 1) * 0.0012 * factor
        )
        town.safety = self._clamp(
            town.safety
            + (levels["residential"] - 1) * 0.0014 * factor
            + (levels["center"] - 1) * 0.0010 * factor
        )
        player.reputation = self._clamp(player.reputation + (levels["center"] - 1) * 0.0005 * factor)

    def generate_relationship_event(self, town: TownState, npcs: List[NPC], player: PlayerState) -> Optional[str]:
        if len(npcs) < 2:
            return None
        a, b = self.random.sample(npcs, k=2)
        r = self.random.random()
        if r < 0.35:
            a.mood = self._clamp(a.mood + 0.04)
            b.mood = self._clamp(b.mood + 0.04)
            a.social = self._clamp(a.social + 0.05)
            b.social = self._clamp(b.social + 0.05)
            town.culture = self._clamp(town.culture + 0.01)
            return f"[关系] {a.name} 与 {b.name} 达成合作，文化活力提升。"
        if r < 0.65:
            a.mood = self._clamp(a.mood - 0.05)
            b.mood = self._clamp(b.mood - 0.04)
            town.safety = self._clamp(town.safety - 0.008)
            return f"[关系] {a.name} 与 {b.name} 发生争执，社区紧张度上升。"
        if r < 0.82:
            a.wealth = self._clamp(a.wealth + 0.06)
            b.wealth = self._clamp(b.wealth + 0.03)
            town.economy = self._clamp(town.economy + 0.012)
            return f"[关系] {a.name} 与 {b.name} 启动小型创业项目。"

        player.reputation = self._clamp(player.reputation + 0.015)
        town.culture = self._clamp(town.culture + 0.006)
        return "[关系] 居民公开感谢你的治理策略，城镇口碑上升。"

    @staticmethod
    def upgrade_cost(level: int) -> int:
        return 35 + level * 22

    def _apply_upgrade_bonus(self, town: TownState, player: PlayerState, zone_name: str, new_level: int) -> None:
        if zone_name == "commercial":
            town.economy = self._clamp(town.economy + 0.04)
            player.coins += 5 * (new_level - 1)
        elif zone_name == "industrial":
            town.economy = self._clamp(town.economy + 0.03)
            town.safety = self._clamp(town.safety - 0.01)
        elif zone_name == "cultural":
            town.culture = self._clamp(town.culture + 0.05)
            player.reputation = self._clamp(player.reputation + 0.015)
        elif zone_name == "residential":
            town.safety = self._clamp(town.safety + 0.04)
            town.culture = self._clamp(town.culture + 0.01)
        elif zone_name == "center":
            town.economy = self._clamp(town.economy + 0.02)
            town.culture = self._clamp(town.culture + 0.02)
            town.safety = self._clamp(town.safety + 0.02)

    def _advance_chapter(self, town: TownState) -> str:
        previous_title = town.story.title
        town.story.history.append(f"Day {town.day}: {previous_title} 达成")
        town.story.chapter += 1
        _chapter, title, objective = self._chapter_meta(town.story.chapter)
        town.story.title = title
        town.story.objective = objective
        town.story.history.append(f"Day {town.day}: {title} 开始")
        return f"主线推进：{previous_title} 已完成，进入 {title}"

    @staticmethod
    def _chapter_meta(chapter: int) -> Tuple[int, str, str]:
        if chapter <= 1:
            return 1, "第一章：重建起点", "建设2次、对话6次、生产4次"
        if chapter == 2:
            return 2, "第二章：产业繁荣", "经济>=0.62、交易6次、金币>=130、商业区Lv2"
        if chapter == 3:
            return 3, "第三章：社会共生", "文化>=0.70、治安>=0.66、声望>=0.70、节庆2次、2个区域Lv3"
        return 4, "终章完成：AI小镇新纪元", "通关成功"

    @staticmethod
    def _chapter_targets(chapter: int) -> dict[str, float]:
        if chapter <= 1:
            return {"build": 2.0, "talk": 6.0, "produce": 4.0}
        if chapter == 2:
            return {"economy": 0.62, "trade": 6.0, "coins": 130.0, "commercial_level": 2.0}
        return {"culture": 0.70, "safety": 0.66, "reputation": 0.70, "festival": 2.0, "level3_zones": 2.0}

    @staticmethod
    def _ratio(current: float, target: float) -> float:
        if target <= 0:
            return 1.0
        return max(0.0, min(1.0, current / target))

    @staticmethod
    def _clamp(v: float) -> float:
        return max(0.0, min(1.0, v))
