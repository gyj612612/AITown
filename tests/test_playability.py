from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from aitown.game import AITownGame


class FakeKeys(dict):
    def __getitem__(self, key: int) -> int:
        return int(key in self)


def _cleanup() -> None:
    pygame.event.clear()
    pygame.quit()


def test_menu_keyboard_can_enter_settings() -> None:
    game = AITownGame()
    try:
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN))
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN))
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        game._handle_events()  # noqa: SLF001
        assert game.scene == "settings"
    finally:
        _cleanup()


def test_settings_returns_to_previous_scene() -> None:
    game = AITownGame()
    try:
        game.scene = "play"
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_o))
        game._handle_events()  # noqa: SLF001
        assert game.scene == "settings"
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        game._handle_events()  # noqa: SLF001
        assert game.scene == "play"
    finally:
        _cleanup()


def test_player_can_move_with_arrow_key(monkeypatch) -> None:
    game = AITownGame()
    try:
        game.scene = "play"
        start_y = game.player.y
        monkeypatch.setattr(pygame.key, "get_pressed", lambda: FakeKeys({pygame.K_UP: 1}))
        game._update_player(0.20)  # noqa: SLF001
        assert game.player.y < start_y
    finally:
        _cleanup()


def test_pause_stops_time_progress() -> None:
    game = AITownGame()
    try:
        game.scene = "play"
        t0 = game.town.minute_of_day
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p))
        game._handle_events()  # noqa: SLF001
        assert game.paused is True
        game._update(1.0)  # noqa: SLF001
        assert game.town.minute_of_day == t0
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p))
        game._handle_events()  # noqa: SLF001
        game._update(1.0)  # noqa: SLF001
        assert game.town.minute_of_day > t0
    finally:
        _cleanup()


def test_menu_wasd_can_navigate_and_confirm() -> None:
    game = AITownGame()
    try:
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d))
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d))
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        game._handle_events()  # noqa: SLF001
        assert game.scene == "settings"
    finally:
        _cleanup()


def test_settings_wasd_adjust_and_close_to_menu() -> None:
    game = AITownGame()
    try:
        game.scene = "settings"
        game.previous_scene = "menu"
        old_idx = game.settings_index
        old_texture = game.settings.texture_detail
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s))
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a))
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        game._handle_events()  # noqa: SLF001
        assert game.settings_index >= old_idx
        assert game.settings.texture_detail <= old_texture
        assert game.scene == "menu"
    finally:
        _cleanup()


def test_end_scene_wasd_returns_menu() -> None:
    game = AITownGame()
    try:
        game.scene = "end"
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_w))
        game._handle_events()  # noqa: SLF001
        assert game.scene == "menu"
    finally:
        _cleanup()
