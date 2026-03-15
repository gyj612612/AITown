from __future__ import annotations

import random
from typing import Dict, List, Optional

from .models import NPC, PlayerState, Quest, TownState


class QuestSystem:
    def __init__(self, seed: int = 101) -> None:
        self.random = random.Random(seed)

    def generate_daily_quests(self, town: TownState) -> List[Quest]:
        templates = [
            {
                "kind": "talk",
                "title": "走访居民",
                "description": "今天和居民交流，了解他们的需求。",
                "target": 3,
                "reward_coins": 18,
                "reward_reputation": 0.03,
            },
            {
                "kind": "build",
                "title": "社区微建设",
                "description": "完成一次公共设施建设。",
                "target": 1,
                "reward_coins": 22,
                "reward_reputation": 0.04,
            },
            {
                "kind": "trade",
                "title": "商贸活跃日",
                "description": "完成两笔交易，提升市场流动。",
                "target": 2,
                "reward_coins": 26,
                "reward_reputation": 0.03,
            },
            {
                "kind": "produce",
                "title": "手作补给",
                "description": "在不同功能区进行两次生产。",
                "target": 2,
                "reward_coins": 20,
                "reward_reputation": 0.02,
            },
            {
                "kind": "festival",
                "title": "城市活动策划",
                "description": "组织一次节庆活动。",
                "target": 1,
                "reward_coins": 36,
                "reward_reputation": 0.06,
            },
        ]

        picked = self.random.sample(templates, k=3)
        # 保底一个易达任务，避免当天任务体验过重。
        easy = next(item for item in templates if item["kind"] == "talk")
        if all(item["kind"] != "talk" for item in picked):
            picked[0] = easy

        quests: List[Quest] = []
        for idx, item in enumerate(picked, start=1):
            quests.append(
                Quest(
                    quest_id=f"d{town.day}-q{idx}-{item['kind']}",
                    title=item["title"],
                    description=item["description"],
                    kind=item["kind"],
                    target=item["target"],
                    reward_coins=item["reward_coins"],
                    reward_reputation=item["reward_reputation"],
                    issued_day=town.day,
                )
            )
        town.active_quests = quests
        return quests

    def record_action(self, player: PlayerState, town: TownState, kind: str, amount: int = 1) -> List[Quest]:
        if kind not in player.daily_actions:
            return []
        player.daily_actions[kind] += amount
        player.total_actions[kind] += amount

        completed_now: List[Quest] = []
        for quest in town.active_quests:
            if quest.claimed or quest.kind != kind:
                continue
            quest.progress = min(quest.target, player.daily_actions[kind])
            if quest.progress >= quest.target and not quest.completed:
                quest.completed = True
                completed_now.append(quest)
        return completed_now

    def claim_completed(self, player: PlayerState, town: TownState) -> List[Quest]:
        rewards: List[Quest] = []
        for quest in town.active_quests:
            if quest.completed and not quest.claimed:
                quest.claimed = True
                player.coins += quest.reward_coins
                player.reputation = min(1.0, player.reputation + quest.reward_reputation)
                rewards.append(quest)
        return rewards

    def reset_daily_actions(self, player: PlayerState) -> None:
        for key in player.daily_actions:
            player.daily_actions[key] = 0


class EconomySystem:
    def __init__(self, seed: int = 131) -> None:
        self.random = random.Random(seed)
        self.zone_output: Dict[str, str] = {
            "residential": "food",
            "commercial": "food",
            "industrial": "craft",
            "cultural": "art",
            "center": "tech",
        }

    def produce(self, player: PlayerState, zone_name: Optional[str], town: TownState) -> Optional[str]:
        if zone_name is None:
            return None
        item = self.zone_output.get(zone_name)
        if item is None:
            return None
        player.inventory[item] = player.inventory.get(item, 0) + 1
        player.coins += 1
        town.culture = min(1.0, town.culture + (0.008 if item == "art" else 0.003))
        town.economy = min(1.0, town.economy + (0.006 if item in ("craft", "tech") else 0.003))
        return item

    def trade_with_npc(self, player: PlayerState, npc: NPC, town: TownState) -> Optional[str]:
        sell_item = self._best_sell_item(player.inventory)
        if sell_item is None:
            buy_item = self._best_buy_item(player, town)
            if buy_item is None:
                return None
            cost = self._buy_price(town, buy_item)
            player.coins -= cost
            player.inventory[buy_item] = player.inventory.get(buy_item, 0) + 1
            npc.wealth = min(1.0, npc.wealth + 0.02)
            return f"向{npc.name}购入 {buy_item} -{cost}金币"

        gain = self._sell_price(town, sell_item)
        player.inventory[sell_item] -= 1
        player.coins += gain
        player.reputation = min(1.0, player.reputation + 0.004)
        npc.wealth = min(1.0, npc.wealth + 0.01)
        npc.social = min(1.0, npc.social + 0.02)
        town.economy = min(1.0, town.economy + 0.004)
        return f"向{npc.name}售出 {sell_item} +{gain}金币"

    def refresh_market_prices(self, town: TownState) -> None:
        base = {"food": 9, "craft": 14, "art": 21, "tech": 26}
        for item, value in base.items():
            swing = self.random.uniform(-0.12, 0.16)
            ratio = 0.88 + town.economy * 0.34 + swing
            town.market_prices[item] = max(4, int(value * ratio))

    def _sell_price(self, town: TownState, item: str) -> int:
        ref = town.market_prices.get(item, 8)
        return max(3, int(ref * 0.9))

    def _buy_price(self, town: TownState, item: str) -> int:
        ref = town.market_prices.get(item, 8)
        return max(4, int(ref * 1.1))

    @staticmethod
    def _best_sell_item(inv: Dict[str, int]) -> Optional[str]:
        priority = ("tech", "art", "craft", "food")
        for item in priority:
            if inv.get(item, 0) > 0:
                return item
        return None

    def _best_buy_item(self, player: PlayerState, town: TownState) -> Optional[str]:
        affordable = []
        for item in ("food", "craft", "art", "tech"):
            cost = self._buy_price(town, item)
            if player.coins >= cost:
                affordable.append((cost, item))
        if not affordable:
            return None
        affordable.sort(key=lambda x: x[0])
        return affordable[0][1]

