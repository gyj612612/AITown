from __future__ import annotations

import random
from typing import List

from .models import NPC, Memory, PlayerState, TownState
from .world import TownMap


def create_initial_town(seed: int = 2026) -> tuple[TownState, PlayerState, List[NPC], TownMap]:
    rng = random.Random(seed)
    world = TownMap()
    town = TownState()
    player = PlayerState(x=world.bounds.centerx, y=world.bounds.centery + 120)

    names = [
        "Lin",
        "Mika",
        "Ava",
        "Noah",
        "Sora",
        "Iris",
        "Kai",
        "Zoe",
        "Evan",
        "Luna",
        "Milo",
        "Nia",
        "Rin",
        "Leo",
        "June",
        "Maya",
        "Owen",
        "Ruby",
        "Theo",
        "Nora",
        "Ivy",
        "Aiden",
        "Cora",
        "Finn",
        "Jade",
        "Luca",
        "Aria",
        "Mira",
        "Kian",
        "Elsa",
    ]
    roles = ["Maker", "Barista", "Teacher", "Artist", "Engineer", "Trader", "Chef", "Planner"]
    home_pool = ["residential", "residential", "residential", "center"]
    work_pool = ["commercial", "cultural", "industrial", "center"]

    npcs: List[NPC] = []
    for i, name in enumerate(names):
        home_zone = rng.choice(home_pool)
        work_zone = rng.choice(work_pool)
        x, y = world.random_point_in_zone(home_zone)
        npc = NPC(
            npc_id=f"npc_{i:02d}",
            name=name,
            role=rng.choice(roles),
            x=x,
            y=y,
            home_zone=home_zone,
            work_zone=work_zone,
            energy=rng.uniform(0.45, 0.95),
            wealth=rng.uniform(0.35, 0.9),
            social=rng.uniform(0.3, 0.9),
            mood=rng.uniform(0.35, 0.85),
            current_goal="wander",
            goal_zone="center",
            target_x=x,
            target_y=y,
        )
        npc.memories.append(
            Memory(
                day=1,
                minute=8 * 60,
                summary=f"准备开始新的一天，计划去{work_zone}处理工作。",
                importance=0.4,
                tag="startup",
            )
        )
        npcs.append(npc)

    # 预置一点城镇装饰，增强画面完成度。
    for _ in range(26):
        dx = rng.randint(40, world.bounds.width - 40)
        dy = rng.randint(40, world.bounds.height - 40)
        deco = rng.choice(["tree", "bench", "lamp"])
        world.add_decoration(dx, dy, deco)

    return town, player, npcs, world

