from __future__ import annotations

from aitown.bootstrap import create_initial_town
from aitown.campaign import CampaignSystem


def test_campaign_assist_can_unlock_chapter_one() -> None:
    town, player, _npcs, _world = create_initial_town(seed=88)
    campaign = CampaignSystem(seed=88)
    campaign.ensure_story(town)
    town.day = 9
    msg = campaign.apply_completion_assist(town, player)
    assert msg is not None
    progress = campaign.evaluate_progress(player, town)
    assert progress is not None
    assert town.story.chapter == 2


def test_campaign_progress_ratio_is_valid() -> None:
    town, player, _npcs, _world = create_initial_town(seed=91)
    campaign = CampaignSystem(seed=91)
    campaign.ensure_story(town)
    overall, rows = campaign.chapter_progress(town, player)
    assert 0.0 <= overall <= 1.0
    assert rows
