from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class Memory:
    day: int
    minute: int
    summary: str
    importance: float = 0.5
    tag: str = "general"


@dataclass
class Relationship:
    trust: float = 0.5
    affinity: float = 0.5
    tension: float = 0.2


@dataclass
class WorldEvent:
    event_id: str
    title: str
    description: str
    impact_economy: float = 0.0
    impact_culture: float = 0.0
    impact_safety: float = 0.0
    mood_bias: float = 0.0


@dataclass
class Quest:
    quest_id: str
    title: str
    description: str
    kind: str
    target: int
    progress: int = 0
    reward_coins: int = 0
    reward_reputation: float = 0.0
    completed: bool = False
    claimed: bool = False
    issued_day: int = 1


@dataclass
class StoryState:
    chapter: int = 1
    title: str = "第一章：重建起点"
    objective: str = "建设2次、对话6次、生产4次"
    completed: bool = False
    failed: bool = False
    fail_reason: str = ""
    danger_days: int = 0
    history: List[str] = field(default_factory=list)


@dataclass
class NPC:
    npc_id: str
    name: str
    role: str
    x: float
    y: float
    home_zone: str
    work_zone: str
    energy: float = 0.8
    wealth: float = 0.5
    social: float = 0.5
    mood: float = 0.5
    current_goal: str = "wander"
    goal_zone: str = "center"
    target_x: float = 0.0
    target_y: float = 0.0
    decision_cooldown: float = 0.0
    memory_cooldown: float = 0.0
    memories: List[Memory] = field(default_factory=list)
    relationships: Dict[str, Relationship] = field(default_factory=dict)


@dataclass
class PlayerState:
    x: float
    y: float
    coins: int = 100
    reputation: float = 0.5
    influence: float = 0.2
    tax_policy: str = "balanced"
    build_points: int = 0
    inventory: Dict[str, int] = field(
        default_factory=lambda: {
            "food": 2,
            "craft": 0,
            "art": 0,
            "tech": 0,
        }
    )
    daily_actions: Dict[str, int] = field(
        default_factory=lambda: {
            "talk": 0,
            "build": 0,
            "trade": 0,
            "produce": 0,
            "festival": 0,
        }
    )
    total_actions: Dict[str, int] = field(
        default_factory=lambda: {
            "talk": 0,
            "build": 0,
            "trade": 0,
            "produce": 0,
            "festival": 0,
        }
    )
    last_festival_day: int = 0


@dataclass
class TownState:
    day: int = 1
    minute_of_day: int = 8 * 60
    season: str = "spring"
    weather: str = "clear"
    weather_intensity: float = 0.0
    economy: float = 0.55
    culture: float = 0.45
    safety: float = 0.6
    active_events: List[WorldEvent] = field(default_factory=list)
    event_feed: List[str] = field(default_factory=list)
    weekly_theme: str = "growth"
    policy_tax_rate: float = 0.18
    policies: Dict[str, float] = field(
        default_factory=lambda: {
            "culture_subsidy": 0.3,
            "business_subsidy": 0.4,
            "public_safety": 0.3,
        }
    )
    active_quests: List[Quest] = field(default_factory=list)
    market_prices: Dict[str, int] = field(
        default_factory=lambda: {
            "food": 9,
            "craft": 14,
            "art": 21,
            "tech": 26,
        }
    )
    zone_levels: Dict[str, int] = field(
        default_factory=lambda: {
            "center": 1,
            "residential": 1,
            "commercial": 1,
            "cultural": 1,
            "industrial": 1,
        }
    )
    story: StoryState = field(default_factory=StoryState)


ZoneRect = Tuple[int, int, int, int]
