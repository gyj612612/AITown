from __future__ import annotations

import math
import random
from typing import List, Optional, Tuple

from .models import NPC, Memory, PlayerState, Relationship, TownState
from .world import TownMap


class AgentSystem:
    def __init__(self, seed: int = 11) -> None:
        self.random = random.Random(seed)

    def update_all(
        self,
        npcs: List[NPC],
        world: TownMap,
        town: TownState,
        player: PlayerState,
        delta_minutes: float,
    ) -> None:
        for npc in npcs:
            self._decay_needs(npc, delta_minutes)
            npc.decision_cooldown -= delta_minutes
            npc.memory_cooldown -= delta_minutes

            if npc.decision_cooldown <= 0:
                self._decide_next_action(npc, world, town)
                npc.decision_cooldown = self.random.uniform(8.0, 18.0)

            self._move_towards_target(npc, world, delta_minutes)
            self._perform_zone_action(npc, world, town, delta_minutes)

            if npc.memory_cooldown <= 0:
                self._write_periodic_memory(npc, town)
                npc.memory_cooldown = self.random.uniform(45.0, 85.0)

            self._update_player_relation_glance(npc, player)

    def talk_to_npc(self, npc: NPC, player: PlayerState, town: TownState) -> str:
        rel = npc.relationships.setdefault("player", Relationship())
        rel.affinity = self._clamp(rel.affinity + 0.04)
        rel.trust = self._clamp(rel.trust + 0.03)
        rel.tension = self._clamp(rel.tension - 0.02)

        npc.social = self._clamp(npc.social + 0.08)
        npc.mood = self._clamp(npc.mood + 0.05)
        player.reputation = self._clamp(player.reputation + 0.01)
        player.influence = self._clamp(player.influence + 0.005)

        latest_memory = npc.memories[-1].summary if npc.memories else "今天还没发生特别的事"
        mood_label = self._mood_label(npc.mood)
        zone_context = npc.goal_zone
        line = (
            f"{npc.name}（{npc.role}）[{mood_label}]："
            f"我现在主要在{zone_context}忙“{npc.current_goal}”。"
            f" 最近我记得的一件事是：{latest_memory}。"
        )

        npc.memories.append(
            Memory(
                day=town.day,
                minute=town.minute_of_day,
                summary=f"和玩家交谈后心情变好，想继续推进{npc.current_goal}",
                importance=0.6,
                tag="player_talk",
            )
        )
        npc.memories = npc.memories[-14:]
        return line

    def inspect_npc(self, npc: NPC) -> str:
        rel = npc.relationships.get("player", Relationship())
        return (
            f"{npc.name} | 职业:{npc.role} | 目标:{npc.current_goal} | 区域:{npc.goal_zone} | "
            f"能量:{npc.energy:.2f} 社交:{npc.social:.2f} 财富:{npc.wealth:.2f} 心情:{npc.mood:.2f} | "
            f"关系: 信任{rel.trust:.2f}/好感{rel.affinity:.2f}/紧张{rel.tension:.2f}"
        )

    def _decay_needs(self, npc: NPC, delta_minutes: float) -> None:
        factor = delta_minutes / 60.0
        npc.energy = self._clamp(npc.energy - 0.035 * factor)
        npc.social = self._clamp(npc.social - 0.028 * factor)
        npc.wealth = self._clamp(npc.wealth - 0.012 * factor)
        npc.mood = self._clamp(npc.mood - 0.015 * factor)

    def _decide_next_action(self, npc: NPC, world: TownMap, town: TownState) -> None:
        candidates: List[Tuple[str, str, float]] = []

        # util = shortage * weight + world bias + random jitter
        work_utility = (1.0 - npc.wealth) * 0.8 + town.economy * 0.3 + self.random.random() * 0.1
        social_utility = (1.0 - npc.social) * 0.9 + town.culture * 0.2 + self.random.random() * 0.1
        rest_utility = (1.0 - npc.energy) * 1.0 + (0.2 if town.minute_of_day > 21 * 60 else 0.0)
        explore_utility = 0.2 + self.random.random() * 0.2

        candidates.append(("work", npc.work_zone, work_utility))
        candidates.append(("socialize", "center", social_utility))
        candidates.append(("rest", npc.home_zone, rest_utility))
        candidates.append(("explore", self.random.choice(list(world.zones.keys())), explore_utility))

        goal, zone_name, _score = max(candidates, key=lambda item: item[2])
        npc.current_goal = goal
        npc.goal_zone = zone_name
        npc.target_x, npc.target_y = world.random_point_in_zone(zone_name)

    def _move_towards_target(self, npc: NPC, world: TownMap, delta_minutes: float) -> None:
        dx = npc.target_x - npc.x
        dy = npc.target_y - npc.y
        dist = math.hypot(dx, dy)
        if dist < 1.0:
            return
        speed_px_per_min = 55.0
        step = speed_px_per_min * max(0.2, delta_minutes)
        if dist <= step:
            npc.x, npc.y = npc.target_x, npc.target_y
            return
        npc.x += dx / dist * step
        npc.y += dy / dist * step
        npc.x, npc.y = world.clamp_position(npc.x, npc.y)

    def _perform_zone_action(self, npc: NPC, world: TownMap, town: TownState, delta_minutes: float) -> None:
        zone = world.zone_at(npc.x, npc.y)
        if zone is None:
            return
        factor = delta_minutes / 60.0

        if npc.current_goal == "work" and zone.name == npc.work_zone:
            tax_drag = 1.0 - min(0.35, town.policy_tax_rate)
            npc.wealth = self._clamp(npc.wealth + 0.11 * factor * tax_drag)
            npc.energy = self._clamp(npc.energy - 0.07 * factor)
            town.economy = self._clamp(town.economy + 0.005 * factor)
        elif npc.current_goal == "socialize":
            npc.social = self._clamp(npc.social + 0.12 * factor)
            npc.mood = self._clamp(npc.mood + 0.08 * factor)
            town.culture = self._clamp(town.culture + 0.004 * factor)
        elif npc.current_goal == "rest" and zone.name == npc.home_zone:
            npc.energy = self._clamp(npc.energy + 0.16 * factor)
            npc.mood = self._clamp(npc.mood + 0.04 * factor)
        elif npc.current_goal == "explore":
            npc.mood = self._clamp(npc.mood + 0.02 * factor)

    def _write_periodic_memory(self, npc: NPC, town: TownState) -> None:
        mood = self._mood_label(npc.mood)
        summary = f"在{npc.goal_zone}执行{npc.current_goal}，当前心情{mood}"
        npc.memories.append(
            Memory(
                day=town.day,
                minute=town.minute_of_day,
                summary=summary,
                importance=0.35 + self.random.random() * 0.25,
                tag="routine",
            )
        )
        npc.memories = npc.memories[-14:]

    def _update_player_relation_glance(self, npc: NPC, player: PlayerState) -> None:
        rel = npc.relationships.setdefault("player", Relationship())
        reputation_bias = (player.reputation - 0.5) * 0.02
        rel.affinity = self._clamp(rel.affinity + reputation_bias)
        rel.trust = self._clamp(rel.trust + reputation_bias * 0.8)

    @staticmethod
    def _clamp(v: float) -> float:
        return max(0.0, min(1.0, v))

    @staticmethod
    def _mood_label(v: float) -> str:
        if v < 0.25:
            return "低落"
        if v < 0.45:
            return "平稳偏低"
        if v < 0.7:
            return "正常"
        return "积极"


def nearest_npc(npcs: List[NPC], x: float, y: float, max_distance: float) -> Optional[NPC]:
    winner: Optional[NPC] = None
    best = max_distance
    for npc in npcs:
        dist = math.hypot(npc.x - x, npc.y - y)
        if dist < best:
            best = dist
            winner = npc
    return winner

