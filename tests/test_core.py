from __future__ import annotations

from pathlib import Path

from aitown.agent import AgentSystem
from aitown.bootstrap import create_initial_town
from aitown.campaign import CampaignSystem
from aitown.director import WorldDirector
from aitown.persistence import load_game, save_game
from aitown.progression import EconomySystem, QuestSystem
from aitown.settings import GameSettings, SettingsManager


def test_daily_event_generation() -> None:
    town, player, npcs, _world = create_initial_town(seed=42)
    director = WorldDirector(seed=42)
    town.minute_of_day = 23 * 60 + 55
    changed = director.advance_time(town, 10)
    assert changed is True
    events = director.run_daily_settlement(town, npcs)
    assert len(events) == 2
    assert town.day == 2
    assert town.season in {"spring", "summer", "autumn", "winter"}
    assert town.weather in {"clear", "rain", "storm", "fog", "snow"}


def test_agent_update_changes_state() -> None:
    town, player, npcs, world = create_initial_town(seed=9)
    system = AgentSystem(seed=9)
    before = (npcs[0].energy, npcs[0].social, npcs[0].wealth)
    system.update_all(npcs, world, town, player, delta_minutes=30)
    after = (npcs[0].energy, npcs[0].social, npcs[0].wealth)
    assert before != after


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    town, player, npcs, world = create_initial_town(seed=7)
    save_path = tmp_path / "save.json"
    save_game(str(save_path), town, player, npcs, world.decorations)
    loaded_town, loaded_player, loaded_npcs, loaded_decorations = load_game(str(save_path))
    assert loaded_town.day == town.day
    assert loaded_player.coins == player.coins
    assert len(loaded_npcs) == len(npcs)
    assert len(loaded_decorations) == len(world.decorations)


def test_quest_progress_and_claim() -> None:
    town, player, _npcs, _world = create_initial_town(seed=5)
    quest_system = QuestSystem(seed=5)
    quests = quest_system.generate_daily_quests(town)
    assert len(quests) == 3

    talk_quests = [q for q in quests if q.kind == "talk"]
    assert talk_quests, "daily quests should contain at least one talk quest"

    quest_system.record_action(player, town, "talk", amount=3)
    rewards = quest_system.claim_completed(player, town)
    assert any(q.kind == "talk" for q in rewards)


def test_produce_and_trade_flow() -> None:
    town, player, npcs, world = create_initial_town(seed=13)
    econ = EconomySystem(seed=13)
    econ.refresh_market_prices(town)
    player.inventory = {"food": 0, "craft": 0, "art": 0, "tech": 0}
    player.coins = 100

    zone = world.zone_at(npcs[0].x, npcs[0].y)
    produced = econ.produce(player, zone.name if zone else "center", town)
    assert produced is not None
    assert player.inventory[produced] >= 1

    before_coins = player.coins
    result = econ.trade_with_npc(player, npcs[0], town)
    assert result is not None
    assert player.coins != before_coins


def test_campaign_chapter_progress() -> None:
    town, player, _npcs, _world = create_initial_town(seed=23)
    campaign = CampaignSystem(seed=23)
    campaign.ensure_story(town)

    player.total_actions["build"] = 2
    player.total_actions["talk"] = 6
    player.total_actions["produce"] = 4

    message = campaign.evaluate_progress(player, town)
    assert message is not None
    assert town.story.chapter == 2


def test_campaign_upgrade_and_failure() -> None:
    town, player, npcs, _world = create_initial_town(seed=31)
    campaign = CampaignSystem(seed=31)
    campaign.ensure_story(town)

    player.coins = 500
    ok, _msg = campaign.attempt_zone_upgrade(town, player, "commercial")
    assert ok is True
    assert town.zone_levels["commercial"] == 2

    town.economy = 0.1
    town.safety = 0.1
    player.coins = -40
    fail = None
    for _ in range(3):
        fail = campaign.evaluate_failure(town, player)
    assert fail is not None
    assert town.story.failed is True


def test_settings_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    manager = SettingsManager(str(path))
    settings = GameSettings(
        graphics_quality="medium",
        texture_detail=1,
        effect_level=1,
        weather_effects=False,
        master_volume=0.5,
        bgm_volume=0.4,
        sfx_volume=0.6,
        mouse_interaction=False,
        move_speed_multiplier=1.2,
        time_flow_multiplier=1.25,
        show_fps=True,
        fullscreen=True,
    )
    manager.save(settings)
    loaded = manager.load()
    assert loaded.graphics_quality == "medium"
    assert loaded.weather_effects is False
    assert abs(loaded.master_volume - 0.5) < 1e-6
    assert loaded.show_fps is True
