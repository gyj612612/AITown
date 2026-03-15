from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Tuple

from .models import NPC, Memory, PlayerState, Quest, Relationship, StoryState, TownState, WorldEvent


def save_game(
    path: str,
    town: TownState,
    player: PlayerState,
    npcs: List[NPC],
    decorations: List[Tuple[int, int, str]] | None = None,
) -> None:
    payload = {
        "town": _town_to_dict(town),
        "player": asdict(player),
        "npcs": [_npc_to_dict(npc) for npc in npcs],
        "decorations": decorations or [],
    }
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_game(path: str) -> Tuple[TownState, PlayerState, List[NPC], List[Tuple[int, int, str]]]:
    raw = Path(path).read_text(encoding="utf-8")
    payload = json.loads(raw)

    town = _town_from_dict(payload["town"])
    player = _player_from_dict(payload["player"])
    npcs = [_npc_from_dict(item) for item in payload["npcs"]]
    decorations = [tuple(item) for item in payload.get("decorations", [])]
    return town, player, npcs, decorations


def _npc_to_dict(npc: NPC) -> Dict:
    data = asdict(npc)
    return data


def _player_from_dict(data: Dict) -> PlayerState:
    player = PlayerState(
        x=data.get("x", 0.0),
        y=data.get("y", 0.0),
        coins=data.get("coins", 100),
        reputation=data.get("reputation", 0.5),
        influence=data.get("influence", 0.2),
        tax_policy=data.get("tax_policy", "balanced"),
        build_points=data.get("build_points", 0),
        inventory=data.get("inventory", {"food": 2, "craft": 0, "art": 0, "tech": 0}),
        daily_actions=data.get(
            "daily_actions",
            {"talk": 0, "build": 0, "trade": 0, "produce": 0, "festival": 0},
        ),
        total_actions=data.get(
            "total_actions",
            {"talk": 0, "build": 0, "trade": 0, "produce": 0, "festival": 0},
        ),
        last_festival_day=data.get("last_festival_day", 0),
    )
    return player


def _npc_from_dict(data: Dict) -> NPC:
    memories = [Memory(**m) for m in data.get("memories", [])]
    rels = {k: Relationship(**v) for k, v in data.get("relationships", {}).items()}
    npc = NPC(
        npc_id=data["npc_id"],
        name=data["name"],
        role=data["role"],
        x=data["x"],
        y=data["y"],
        home_zone=data["home_zone"],
        work_zone=data["work_zone"],
        energy=data.get("energy", 0.8),
        wealth=data.get("wealth", 0.5),
        social=data.get("social", 0.5),
        mood=data.get("mood", 0.5),
        current_goal=data.get("current_goal", "wander"),
        goal_zone=data.get("goal_zone", "center"),
        target_x=data.get("target_x", data["x"]),
        target_y=data.get("target_y", data["y"]),
        decision_cooldown=data.get("decision_cooldown", 0.0),
        memory_cooldown=data.get("memory_cooldown", 0.0),
        memories=memories,
        relationships=rels,
    )
    return npc


def _town_to_dict(town: TownState) -> Dict:
    data = asdict(town)
    return data


def _town_from_dict(data: Dict) -> TownState:
    events = [WorldEvent(**evt) for evt in data.get("active_events", [])]
    quests = [Quest(**quest) for quest in data.get("active_quests", [])]
    story = _story_from_dict(data.get("story", {}))
    town = TownState(
        day=data.get("day", 1),
        minute_of_day=data.get("minute_of_day", 8 * 60),
        season=data.get("season", "spring"),
        weather=data.get("weather", "clear"),
        weather_intensity=float(data.get("weather_intensity", 0.0)),
        economy=data.get("economy", 0.55),
        culture=data.get("culture", 0.45),
        safety=data.get("safety", 0.6),
        active_events=events,
        event_feed=data.get("event_feed", []),
        weekly_theme=data.get("weekly_theme", "growth"),
        policy_tax_rate=data.get("policy_tax_rate", 0.18),
        policies=data.get(
            "policies",
            {"culture_subsidy": 0.3, "business_subsidy": 0.4, "public_safety": 0.3},
        ),
        active_quests=quests,
        market_prices=data.get("market_prices", {"food": 9, "craft": 14, "art": 21, "tech": 26}),
        zone_levels=data.get(
            "zone_levels",
            {"center": 1, "residential": 1, "commercial": 1, "cultural": 1, "industrial": 1},
        ),
        story=story,
    )
    return town


def _story_from_dict(data: Dict) -> StoryState:
    return StoryState(
        chapter=data.get("chapter", 1),
        title=data.get("title", "第一章：重建起点"),
        objective=data.get("objective", "建设2次、对话6次、生产4次"),
        completed=data.get("completed", False),
        failed=data.get("failed", False),
        fail_reason=data.get("fail_reason", ""),
        danger_days=data.get("danger_days", 0),
        history=data.get("history", []),
    )
