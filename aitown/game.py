from __future__ import annotations

import math
from pathlib import Path
from typing import List, Optional

import pygame

from .agent import AgentSystem, nearest_npc
from .assets import AssetPack
from .audio import AudioManager
from .bootstrap import create_initial_town
from .campaign import CampaignSystem
from .config import COLORS, SCREEN, SIM
from .director import WorldDirector
from .persistence import load_game, save_game
from .progression import EconomySystem, QuestSystem
from .settings import SettingsManager


class AITownGame:
    def __init__(self) -> None:
        pygame.init()
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load()
        self._apply_graphics_preset(self.settings.graphics_quality)
        self._apply_display_mode()
        pygame.display.set_caption("AI Town - Complete Edition")
        self.clock = pygame.time.Clock()

        self.asset_pack = AssetPack()
        self.asset_pack.load_default_pack()
        self.font = self.asset_pack.get_font(18)
        self.font_small = self.asset_pack.get_font(15)
        self.font_big = self.asset_pack.get_font(34)

        self.audio = AudioManager()
        self.audio.set_volumes(
            self.settings.master_volume,
            self.settings.bgm_volume,
            self.settings.sfx_volume,
        )

        self.scene = "menu"
        self.previous_scene = "menu"
        self.end_message = ""
        self.running = True
        self.show_info_panel = True
        self.show_help = False
        self.paused = False
        self.speed_level = 1
        self.speed_table = [1, 2, 4]
        self.feed: List[str] = []
        self.mouse_move_target: Optional[tuple[float, float]] = None
        self.settings_index = 0
        self.menu_index = 0
        self.menu_hover_label: Optional[str] = None
        self.world_surface = pygame.Surface((SCREEN.width, SCREEN.height))

        self._reset_world()

    def _apply_display_mode(self) -> None:
        flags = pygame.FULLSCREEN if self.settings.fullscreen else 0
        self.screen = pygame.display.set_mode((SCREEN.width, SCREEN.height), flags)

    def _reset_world(self) -> None:
        self.town, self.player, self.npcs, self.world = create_initial_town()
        self.director = WorldDirector(seed=19)
        self.agents = AgentSystem(seed=29)
        self.quest_system = QuestSystem(seed=41)
        self.economy_system = EconomySystem(seed=53)
        self.campaign = CampaignSystem(seed=67)

        self.town.season = self.director.season_for_day(self.town.day)
        self.town.weather = "clear"
        self.town.weather_intensity = 0.1

        self.economy_system.refresh_market_prices(self.town)
        self.quest_system.generate_daily_quests(self.town)
        self.campaign.ensure_story(self.town)

        self.feed = [
            "欢迎来到AI小镇：Enter开始，O打开设置。",
            "支持：画质/特效/音量设置、鼠标交互、季节天气。",
        ]
        self.end_message = ""
        self.mouse_move_target = None
        self.paused = False

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(SCREEN.fps) / 1000.0
            self._handle_events()
            if self.scene == "play":
                self.audio.play_bgm()
                self._update(dt)
                self._render_play()
            elif self.scene == "menu":
                self.audio.play_bgm()
                self._render_menu()
            elif self.scene == "settings":
                self.audio.play_bgm()
                self._render_settings()
            else:
                self._render_end()
            pygame.display.flip()
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.scene == "menu":
                    self._handle_menu_keys(event.key)
                elif self.scene == "play":
                    self._handle_play_keys(event.key)
                elif self.scene == "settings":
                    self._handle_settings_keys(event.key)
                else:
                    self._handle_end_keys(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.scene == "menu":
                    self._handle_menu_mouse(event.pos, event.button)
                elif self.scene == "play":
                    self._handle_play_mouse(event.pos, event.button)
                elif self.scene == "settings":
                    self._handle_settings_mouse(event.pos, event.button)
            elif event.type == pygame.MOUSEMOTION and self.scene == "menu":
                self._handle_menu_hover(event.pos)

    def _handle_menu_keys(self, key: int) -> None:
        labels = [label for label, _rect in self._menu_buttons()]
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key in (pygame.K_UP, pygame.K_w, pygame.K_LEFT, pygame.K_a):
            self.menu_index = (self.menu_index - 1) % len(labels)
            self.audio.play_sfx("click")
        elif key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d):
            self.menu_index = (self.menu_index + 1) % len(labels)
            self.audio.play_sfx("click")
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
            self._activate_menu_label(labels[self.menu_index])
        elif key == pygame.K_l:
            self._activate_menu_label("load")
        elif key == pygame.K_o:
            self._activate_menu_label("settings")

    def _handle_play_keys(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.scene = "menu"
        elif key == pygame.K_TAB:
            self.show_info_panel = not self.show_info_panel
        elif key == pygame.K_h:
            self.show_help = not self.show_help
        elif key == pygame.K_o:
            self.previous_scene = "play"
            self.scene = "settings"
            self.audio.play_sfx("click")
        elif key == pygame.K_p:
            self.paused = not self.paused
            self._push_feed("游戏已暂停，按P继续。" if self.paused else "游戏继续。")
            self.audio.play_sfx("click")
        elif key == pygame.K_SPACE:
            self.speed_level = (self.speed_level + 1) % len(self.speed_table)
        elif key == pygame.K_e:
            self._talk_action()
        elif key == pygame.K_q:
            self._inspect_action()
        elif key == pygame.K_b:
            self._build_action()
        elif key == pygame.K_u:
            self._upgrade_zone_action()
        elif key == pygame.K_g:
            self._toggle_tax_policy()
        elif key == pygame.K_r:
            self._produce_action()
        elif key == pygame.K_t:
            self._trade_action()
        elif key == pygame.K_f:
            self._festival_action()
        elif key == pygame.K_k:
            self._claim_quest_rewards()
        elif key == pygame.K_F5:
            self._save_action()
        elif key == pygame.K_F9:
            self._load_action(silent=False)

    def _handle_settings_keys(self, key: int) -> None:
        max_idx = len(self._settings_rows()) - 1
        if key == pygame.K_ESCAPE:
            self._close_settings()
            return
        if key in (pygame.K_UP, pygame.K_w):
            self.settings_index = max(0, self.settings_index - 1)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.settings_index = min(max_idx, self.settings_index + 1)
        elif key in (pygame.K_LEFT, pygame.K_a):
            self._adjust_setting(self.settings_index, -1)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self._adjust_setting(self.settings_index, 1)
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
            self._adjust_setting(self.settings_index, 1, toggle=True)

    def _handle_end_keys(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d):
            self.scene = "menu"

    def _activate_menu_label(self, label: str) -> None:
        if label == "start":
            self._reset_world()
            self.scene = "play"
            self.audio.play_sfx("confirm")
        elif label == "load":
            if self._load_action(silent=True):
                self.scene = "play"
                self.audio.play_sfx("confirm")
            else:
                self.audio.play_sfx("error")
        elif label == "settings":
            self.previous_scene = "menu"
            self.scene = "settings"
            self.audio.play_sfx("click")
        elif label == "quit":
            self.running = False

    def _handle_menu_hover(self, pos: tuple[int, int]) -> None:
        self.menu_hover_label = None
        for idx, (label, rect) in enumerate(self._menu_buttons()):
            if rect.collidepoint(pos):
                self.menu_hover_label = label
                self.menu_index = idx
                return

    def _handle_menu_mouse(self, pos: tuple[int, int], button: int) -> None:
        if button != 1:
            return
        for label, rect in self._menu_buttons():
            if rect.collidepoint(pos):
                self._activate_menu_label(label)
                return

    def _handle_play_mouse(self, pos: tuple[int, int], button: int) -> None:
        if not self.settings.mouse_interaction:
            return
        mx, my = pos
        if button == 1:
            npc = self._npc_at_position(mx, my)
            if npc is not None:
                if self._distance(self.player.x, self.player.y, npc.x, npc.y) <= SIM.interaction_radius + 10:
                    self._talk_with_npc(npc)
                else:
                    self.mouse_move_target = (npc.x, npc.y)
                self.audio.play_sfx("click")
                return
            self.mouse_move_target = self.world.clamp_position(float(mx), float(my))
            self.audio.play_sfx("click")
        elif button == 3:
            npc = self._npc_at_position(mx, my, radius=24)
            if npc is not None:
                self._push_feed(f"[鼠标洞察] {self.agents.inspect_npc(npc)}")
                self.audio.play_sfx("click")

    def _handle_settings_mouse(self, pos: tuple[int, int], button: int) -> None:
        if button != 1:
            return
        panel = pygame.Rect(SCREEN.width // 2 - 360, 110, 720, 520)
        if not panel.collidepoint(pos):
            return
        row_top = 170
        row_h = 32
        for idx, _ in enumerate(self._settings_rows()):
            row = pygame.Rect(panel.x + 24, row_top + idx * row_h, panel.width - 48, row_h - 2)
            if row.collidepoint(pos):
                self.settings_index = idx
                self._adjust_setting(idx, -1 if pos[0] < row.centerx else 1)
                return
        close_rect = pygame.Rect(panel.centerx - 80, panel.bottom - 54, 160, 36)
        if close_rect.collidepoint(pos):
            self._close_settings()

    def _close_settings(self) -> None:
        self.settings_manager.save(self.settings)
        self.scene = self.previous_scene if self.previous_scene in {"menu", "play"} else "menu"
        self.previous_scene = "menu"
        self.audio.play_sfx("confirm")

    def _update(self, dt: float) -> None:
        if self.paused:
            return
        self._update_player(dt)
        sim_mul = self.speed_table[self.speed_level] * self.settings.time_flow_multiplier
        delta_minutes = dt * SIM.minutes_per_second * sim_mul

        if self.director.advance_time(self.town, delta_minutes):
            self._on_new_day()

        self._policy_drift(delta_minutes)
        self.campaign.apply_zone_effects(self.town, self.player, delta_minutes)
        self.agents.update_all(self.npcs, self.world, self.town, self.player, delta_minutes)
        self._check_story_state()

    def _on_new_day(self) -> None:
        events = self.director.run_daily_settlement(self.town, self.npcs)
        self.quest_system.reset_daily_actions(self.player)
        quests = self.quest_system.generate_daily_quests(self.town)
        self.economy_system.refresh_market_prices(self.town)
        relation_msg = self.campaign.generate_relationship_event(self.town, self.npcs, self.player)
        assist_msg = self.campaign.apply_completion_assist(self.town, self.player)

        self._push_feed(
            f"Day {self.town.day} 开始，季节:{self.town.season} 天气:{self.town.weather} 主题:{self.town.weekly_theme}"
        )
        for event in events:
            self._push_feed(f"[事件] {event.title}: {event.description}")
        if relation_msg:
            self._push_feed(relation_msg)
        if assist_msg:
            self._push_feed(f"[托底] {assist_msg}")
        self._push_feed(f"[任务] 今日发布 {len(quests)} 个任务，可按K领取完成奖励。")
        self.player.coins += 20
        self._check_story_state()
    def _update_player(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        dx = 0.0
        dy = 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1.0

        sprint_mul = 1.45 if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) else 1.0
        speed = SIM.player_speed * self.settings.move_speed_multiplier * sprint_mul
        if dx != 0.0 or dy != 0.0:
            mag = math.hypot(dx, dy)
            dx /= mag
            dy /= mag
            self.player.x += dx * speed * dt
            self.player.y += dy * speed * dt
            self.player.x, self.player.y = self.world.clamp_position(self.player.x, self.player.y)
            self.mouse_move_target = None
            return

        if self.mouse_move_target is not None:
            tx, ty = self.mouse_move_target
            vx = tx - self.player.x
            vy = ty - self.player.y
            dist = math.hypot(vx, vy)
            if dist <= 3:
                self.mouse_move_target = None
                return
            step = speed * dt
            if dist <= step:
                self.player.x, self.player.y = tx, ty
                self.mouse_move_target = None
            else:
                self.player.x += vx / dist * step
                self.player.y += vy / dist * step
            self.player.x, self.player.y = self.world.clamp_position(self.player.x, self.player.y)

    def _talk_action(self) -> None:
        npc = nearest_npc(self.npcs, self.player.x, self.player.y, SIM.interaction_radius)
        if npc is None:
            self._push_feed("附近没有可以对话的人。")
            self.audio.play_sfx("error")
            return
        self._talk_with_npc(npc)

    def _talk_with_npc(self, npc) -> None:
        line = self.agents.talk_to_npc(npc, self.player, self.town)
        self.player.coins += 1
        self._push_feed(line)
        self._record_action("talk")
        self.audio.play_sfx("confirm")

    def _inspect_action(self) -> None:
        npc = nearest_npc(self.npcs, self.player.x, self.player.y, SIM.interaction_radius + 15)
        if npc is None:
            self._push_feed("没有可查看的NPC。")
            self.audio.play_sfx("error")
            return
        self._push_feed(f"[洞察] {self.agents.inspect_npc(npc)}")
        self.audio.play_sfx("click")

    def _build_action(self) -> None:
        cost = 15
        if self.player.coins < cost:
            self._push_feed("建设失败：金币不足（需要15）。")
            self.audio.play_sfx("error")
            return
        self.player.coins -= cost
        self.player.build_points += 1
        item = ("tree", "bench", "lamp")[self.player.build_points % 3]
        self.world.add_decoration(int(self.player.x), int(self.player.y), item)
        self.town.culture = self._clamp(self.town.culture + 0.02)
        self.player.reputation = self._clamp(self.player.reputation + 0.02)
        self._push_feed(f"建设成功：新增{item}，文化值提升。")
        self._record_action("build")
        self.audio.play_sfx("success")

    def _upgrade_zone_action(self) -> None:
        zone = self.world.zone_at(self.player.x, self.player.y)
        ok, msg = self.campaign.attempt_zone_upgrade(self.town, self.player, zone.name if zone else None)
        self._push_feed(msg)
        self.audio.play_sfx("success" if ok else "error")
        if ok:
            self._check_story_state()

    def _toggle_tax_policy(self) -> None:
        if self.player.tax_policy == "low":
            self.player.tax_policy = "balanced"
            self.town.policy_tax_rate = 0.18
        elif self.player.tax_policy == "balanced":
            self.player.tax_policy = "high"
            self.town.policy_tax_rate = 0.28
        else:
            self.player.tax_policy = "low"
            self.town.policy_tax_rate = 0.12
        self._push_feed(f"税率政策切换为：{self.player.tax_policy} ({self.town.policy_tax_rate:.2f})")
        self.audio.play_sfx("click")

    def _produce_action(self) -> None:
        zone = self.world.zone_at(self.player.x, self.player.y)
        item = self.economy_system.produce(self.player, zone.name if zone else None, self.town)
        if item is None:
            self._push_feed("生产失败：请进入功能区后再尝试。")
            self.audio.play_sfx("error")
            return
        self._push_feed(f"生产完成：获得 {item} x1")
        self._record_action("produce")
        self.audio.play_sfx("confirm")

    def _trade_action(self) -> None:
        npc = nearest_npc(self.npcs, self.player.x, self.player.y, SIM.interaction_radius + 12)
        if npc is None:
            self._push_feed("交易失败：附近没有NPC。")
            self.audio.play_sfx("error")
            return
        result = self.economy_system.trade_with_npc(self.player, npc, self.town)
        if result is None:
            self._push_feed("交易失败：库存为空且金币不足购买。")
            self.audio.play_sfx("error")
            return
        self._push_feed(f"[交易] {result}")
        self._record_action("trade")
        self.audio.play_sfx("confirm")

    def _festival_action(self) -> None:
        cost = 35
        if self.player.last_festival_day == self.town.day:
            self._push_feed("今日已经举办过活动，请明天再试。")
            self.audio.play_sfx("error")
            return
        if self.player.coins < cost:
            self._push_feed("活动失败：金币不足（需要35）。")
            self.audio.play_sfx("error")
            return
        self.player.coins -= cost
        self.player.last_festival_day = self.town.day
        self.town.culture = self._clamp(self.town.culture + 0.07)
        self.town.safety = self._clamp(self.town.safety + 0.03)
        self.player.reputation = self._clamp(self.player.reputation + 0.03)
        for npc in self.npcs:
            npc.mood = self._clamp(npc.mood + 0.04)
            npc.social = self._clamp(npc.social + 0.03)
        self._push_feed("活动成功：夜市节庆吸引大量居民参与，文化与口碑提升。")
        self._record_action("festival")
        self.audio.play_sfx("success")

    def _claim_quest_rewards(self) -> None:
        rewards = self.quest_system.claim_completed(self.player, self.town)
        if not rewards:
            self._push_feed("当前没有可领取的任务奖励。")
            self.audio.play_sfx("error")
            return
        for quest in rewards:
            self._push_feed(f"[任务奖励] {quest.title} +{quest.reward_coins}金币 声望+{quest.reward_reputation:.2f}")
        self._check_story_state()
        self.audio.play_sfx("success")

    def _save_action(self) -> None:
        save_path = Path(SIM.autosave_file)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_game(str(save_path), self.town, self.player, self.npcs, self.world.decorations)
        self.settings_manager.save(self.settings)
        self._push_feed(f"存档完成：{save_path}")
        self.audio.play_sfx("confirm")

    def _load_action(self, silent: bool) -> bool:
        save_path = Path(SIM.autosave_file)
        legacy_path = Path("savegame.json")
        if not save_path.exists() and legacy_path.exists():
            save_path = legacy_path
        if not save_path.exists():
            if not silent:
                self._push_feed("读档失败：未找到存档文件。")
            self.audio.play_sfx("error")
            return False
        self.town, self.player, self.npcs, decorations = load_game(str(save_path))
        self.world.decorations = list(decorations)
        if not self.town.active_quests:
            self.quest_system.generate_daily_quests(self.town)
        self.campaign.ensure_story(self.town)
        if not silent:
            self._push_feed(f"读档完成：{save_path} | Day {self.town.day} {self._clock_text()}")
        self.audio.play_sfx("confirm")
        return True

    def _record_action(self, kind: str) -> None:
        completed = self.quest_system.record_action(self.player, self.town, kind, amount=1)
        for quest in completed:
            self._push_feed(f"[任务完成] {quest.title}，按K领取奖励。")
        self._check_story_state()

    def _check_story_state(self) -> None:
        assist_msg = self.campaign.apply_completion_assist(self.town, self.player)
        if assist_msg:
            self._push_feed(f"[托底] {assist_msg}")
        progress_msg = self.campaign.evaluate_progress(self.player, self.town)
        if progress_msg:
            self._push_feed(progress_msg)
        fail_msg = self.campaign.evaluate_failure(self.town, self.player)
        if fail_msg:
            self._push_feed(fail_msg)
        if self.town.story.completed:
            self.end_message = "你完成了三章主线，AI小镇进入繁荣纪元。"
            self.scene = "end"
            self.audio.play_sfx("success")
        elif self.town.story.failed:
            self.end_message = self.town.story.fail_reason
            self.scene = "end"
            self.audio.play_sfx("error")

    def _policy_drift(self, delta_minutes: float) -> None:
        factor = delta_minutes / 60.0
        tax = self.town.policy_tax_rate
        self.town.economy = self._clamp(self.town.economy + (0.22 - tax) * 0.007 * factor)
        self.town.safety = self._clamp(self.town.safety + (tax - 0.14) * 0.005 * factor)
        self.town.culture = self._clamp(self.town.culture + (self.player.build_points * 0.0003) * factor)
    def _render_play(self) -> None:
        world_surface = self.world_surface
        self.world.draw(
            world_surface,
            self._daylight_ratio(),
            self.font_small,
            self.asset_pack,
            season=self.town.season,
            weather=self.town.weather,
            weather_intensity=self.town.weather_intensity,
            texture_detail=self.settings.texture_detail,
            effect_level=self.settings.effect_level,
            weather_effects=self.settings.weather_effects,
            zone_levels=self.town.zone_levels,
        )
        self._draw_npcs(world_surface)
        self._draw_player(world_surface)
        self.screen.blit(self._pixelate_surface(world_surface, self._world_pixel_factor()), (0, 0))
        self._draw_top_hud()
        self._draw_story_tracker()
        self._draw_feed_panel()
        if self.show_info_panel:
            self._draw_info_panel()
        self._draw_context_prompt()
        self._draw_hints()
        if self.show_help:
            self._draw_help_overlay()
        if self.paused:
            self._draw_pause_overlay()

    def _render_menu(self) -> None:
        top = (16, 28, 48)
        bottom = (7, 14, 26)
        for y in range(SCREEN.height):
            t = y / max(1, SCREEN.height - 1)
            color = (
                int(top[0] + (bottom[0] - top[0]) * t),
                int(top[1] + (bottom[1] - top[1]) * t),
                int(top[2] + (bottom[2] - top[2]) * t),
            )
            pygame.draw.line(self.screen, color, (0, y), (SCREEN.width, y))
        glow = pygame.Surface((SCREEN.width, SCREEN.height), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (77, 117, 176, 60), pygame.Rect(SCREEN.width // 2 - 360, 40, 720, 260))
        self.screen.blit(glow, (0, 0))
        ground = pygame.Rect(0, SCREEN.height - 170, SCREEN.width, 170)
        pygame.draw.rect(self.screen, (74, 112, 66), ground)
        for x in range(0, SCREEN.width, 48):
            pygame.draw.rect(self.screen, (90, 132, 80), pygame.Rect(x, SCREEN.height - 170, 24, 170))
        for hx in (210, 460, 960, 1180):
            pygame.draw.rect(self.screen, (148, 102, 74), pygame.Rect(hx, SCREEN.height - 224, 72, 54))
            pygame.draw.polygon(
                self.screen,
                (176, 93, 76),
                [(hx - 8, SCREEN.height - 224), (hx + 36, SCREEN.height - 256), (hx + 80, SCREEN.height - 224)],
            )

        title = self.font_big.render("AI 小镇 Complete Edition", True, (238, 243, 251))
        self.screen.blit(title, (SCREEN.width // 2 - title.get_width() // 2, 120))

        lines = [
            "目标：完成三章主线，建设并维持高繁荣/文化/治安。",
            "键盘与鼠标全支持：方向键/WASD、点击交互、设置可调。",
        ]
        y = 200
        for line in lines:
            txt = self.font.render(line, True, (182, 193, 210))
            self.screen.blit(txt, (SCREEN.width // 2 - txt.get_width() // 2, y))
            y += 34

        label_map = {
            "start": "开始新游戏",
            "load": "读取存档",
            "settings": "游戏设置",
            "quit": "退出游戏",
        }
        selected_label = None
        buttons = self._menu_buttons()
        if 0 <= self.menu_index < len(buttons):
            selected_label = buttons[self.menu_index][0]
        if self.menu_hover_label is not None:
            selected_label = self.menu_hover_label
        for label, rect in buttons:
            selected = label == selected_label
            fill = (42, 68, 102) if selected else (24, 39, 62)
            border = (153, 196, 255) if selected else (88, 113, 161)
            pygame.draw.rect(self.screen, (8, 14, 24), rect.move(0, 3), border_radius=8)
            pygame.draw.rect(self.screen, fill, rect, border_radius=8)
            pygame.draw.rect(self.screen, border, rect, width=2, border_radius=8)
            text = self.font.render(label_map[label], True, COLORS["text"])
            self.screen.blit(text, (rect.centerx - text.get_width() // 2, rect.y + 10))
            if selected:
                marker = self.font_small.render(">", True, (207, 228, 255))
                self.screen.blit(marker, (rect.x + 10, rect.y + 12))

        tip = "WASD/方向键切换，Enter/空格/E确认，鼠标点击也可操作。"
        tip_text = self.font_small.render(tip, True, (182, 197, 219))
        self.screen.blit(tip_text, (SCREEN.width // 2 - tip_text.get_width() // 2, 560))

    def _render_settings(self) -> None:
        self.screen.fill((22, 30, 46))
        panel = pygame.Rect(SCREEN.width // 2 - 360, 110, 720, 520)
        pygame.draw.rect(self.screen, (12, 18, 30), panel.inflate(6, 6), border_radius=12)
        pygame.draw.rect(self.screen, (31, 44, 66), panel, border_radius=12)
        pygame.draw.rect(self.screen, (112, 145, 201), panel, width=2, border_radius=12)

        title = self.font_big.render("游戏设置", True, COLORS["text"])
        self.screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 18))

        hint = "W/S上下选择，A/D左右调整，Esc保存并返回上一界面。"
        hint_text = self.font_small.render(hint, True, COLORS["text_dim"])
        self.screen.blit(hint_text, (panel.centerx - hint_text.get_width() // 2, panel.y + 74))

        row_top = 170
        row_h = 32
        for idx, (name, value) in enumerate(self._settings_rows()):
            rect = pygame.Rect(panel.x + 24, row_top + idx * row_h, panel.width - 48, row_h - 2)
            fill = (62, 89, 132) if idx == self.settings_index else (38, 54, 82)
            pygame.draw.rect(self.screen, fill, rect, border_radius=5)
            pygame.draw.rect(self.screen, (122, 156, 214), rect, width=1, border_radius=5)
            left = self.font_small.render(name, True, COLORS["text"])
            right = self.font_small.render(value, True, COLORS["text_dim"])
            self.screen.blit(left, (rect.x + 10, rect.y + 7))
            self.screen.blit(right, (rect.right - right.get_width() - 10, rect.y + 7))

        close_rect = pygame.Rect(panel.centerx - 80, panel.bottom - 54, 160, 36)
        pygame.draw.rect(self.screen, (35, 57, 88), close_rect, border_radius=8)
        pygame.draw.rect(self.screen, (118, 148, 201), close_rect, width=2, border_radius=8)
        close_text = self.font.render("保存并返回", True, COLORS["text"])
        self.screen.blit(close_text, (close_rect.centerx - close_text.get_width() // 2, close_rect.y + 7))

    def _render_end(self) -> None:
        self.screen.fill((15, 20, 33))
        win = self.town.story.completed
        title_text = "通关成功" if win else "治理失败"
        title_color = (83, 216, 131) if win else (236, 113, 113)
        title = self.font_big.render(title_text, True, title_color)
        self.screen.blit(title, (SCREEN.width // 2 - title.get_width() // 2, 140))

        msg = self.font.render(self.end_message, True, (220, 227, 240))
        self.screen.blit(msg, (SCREEN.width // 2 - msg.get_width() // 2, 220))

        stats = [
            f"Day {self.town.day} | 季节 {self.town.season} | 天气 {self.town.weather}",
            f"经济 {self.town.economy:.2f} / 文化 {self.town.culture:.2f} / 治安 {self.town.safety:.2f}",
            f"金币 {self.player.coins} / 声望 {self.player.reputation:.2f}",
            "WASD/Enter/空格: 回到主菜单    Esc: 退出",
        ]
        y = 280
        for line in stats:
            text = self.font.render(line, True, (182, 193, 210))
            self.screen.blit(text, (SCREEN.width // 2 - text.get_width() // 2, y))
            y += 40

    def _draw_npcs(self, surface: Optional[pygame.Surface] = None) -> None:
        target = surface if surface is not None else self.screen
        npc_sprite = self.asset_pack.get_scaled_image("crate", 20, 20)
        sign_sprite = self.asset_pack.get_scaled_image("sign", 14, 14)
        for npc in self.npcs:
            pygame.draw.ellipse(target, (20, 28, 42), pygame.Rect(int(npc.x) - 10, int(npc.y) + 8, 20, 8))
            if npc_sprite is not None:
                rect = npc_sprite.get_rect(center=(int(npc.x), int(npc.y)))
                target.blit(npc_sprite, rect.topleft)
                if npc.current_goal == "socialize" and sign_sprite is not None:
                    target.blit(sign_sprite, (rect.centerx - 7, rect.top - 12))
            else:
                color = COLORS["npc_talk"] if npc.current_goal == "socialize" else COLORS["npc"]
                pygame.draw.circle(target, color, (int(npc.x), int(npc.y)), 9)
                pygame.draw.circle(target, (255, 255, 255), (int(npc.x), int(npc.y)), 9, width=1)

    def _draw_player(self, surface: Optional[pygame.Surface] = None) -> None:
        target = surface if surface is not None else self.screen
        x, y = int(self.player.x), int(self.player.y)
        player_sprite = self.asset_pack.get_scaled_image("player", 28, 34)
        coin_sprite = self.asset_pack.get_scaled_image("coin", 12, 12)
        pygame.draw.ellipse(target, (16, 22, 36), pygame.Rect(x - 14, y + 9, 28, 10))
        if player_sprite is not None:
            rect = player_sprite.get_rect(center=(x, y))
            target.blit(player_sprite, rect.topleft)
        else:
            pygame.draw.circle(target, COLORS["player"], (x, y), 11)
            pygame.draw.circle(target, (35, 35, 35), (x, y), 11, width=2)
        if coin_sprite is not None:
            target.blit(coin_sprite, (x + 12, y - 22))
        if self.mouse_move_target is not None:
            tx, ty = int(self.mouse_move_target[0]), int(self.mouse_move_target[1])
            pygame.draw.circle(target, (255, 255, 255), (tx, ty), 8, width=1)
            pygame.draw.circle(target, (150, 220, 255), (tx, ty), 3)
            pygame.draw.line(target, (150, 220, 255), (x, y), (tx, ty), 1)

    def _draw_top_hud(self) -> None:
        panel = pygame.Surface((SCREEN.width - 32, 72), pygame.SRCALPHA)
        panel.fill(COLORS["panel_alpha"])
        pygame.draw.rect(panel, COLORS["panel_line"], panel.get_rect(), width=1, border_radius=8)
        self.screen.blit(panel, (16, 12))

        speed_text = "PAUSE" if self.paused else f"x{self.speed_table[self.speed_level]}"
        left = f"Day {self.town.day} {self._clock_text()} {speed_text} {self.town.season}/{self.town.weather}"
        mid = f"经济 {self.town.economy:.2f} 文化 {self.town.culture:.2f} 治安 {self.town.safety:.2f}"
        inv = self.player.inventory
        right = f"金币 {self.player.coins} 声望 {self.player.reputation:.2f} F{inv.get('food',0)} C{inv.get('craft',0)} A{inv.get('art',0)} T{inv.get('tech',0)}"

        self.screen.blit(self.font.render(left[:86], True, COLORS["text"]), (30, 16))
        self.screen.blit(self.font.render(mid, True, COLORS["text"]), (30, 42))
        self.screen.blit(self.font.render(right, True, COLORS["text"]), (700, 42))
        if self.settings.show_fps:
            fps_txt = self.font_small.render(f"FPS {self.clock.get_fps():.1f}", True, COLORS["text"])
            self.screen.blit(fps_txt, (SCREEN.width - 98, 18))

    def _draw_story_tracker(self) -> None:
        overall, rows = self.campaign.chapter_progress(self.town, self.player)
        panel = pygame.Surface((SCREEN.width - 32, 74), pygame.SRCALPHA)
        panel.fill((13, 20, 32, 188))
        pygame.draw.rect(panel, COLORS["panel_line"], panel.get_rect(), width=1, border_radius=8)
        title = f"主线进度 第{self.town.story.chapter}章 {int(overall * 100)}%"
        panel.blit(self.font_small.render(title, True, COLORS["text"]), (12, 8))
        bar_bg = pygame.Rect(180, 10, 300, 12)
        pygame.draw.rect(panel, (34, 44, 61), bar_bg, border_radius=3)
        pygame.draw.rect(panel, (98, 184, 130), pygame.Rect(bar_bg.x, bar_bg.y, int(bar_bg.width * overall), 12), border_radius=3)
        x = 12
        y = 30
        for label, ratio in rows[:4]:
            block = pygame.Rect(x, y, 320, 18)
            pygame.draw.rect(panel, (26, 36, 54), block, border_radius=3)
            fill = pygame.Rect(x, y, max(2, int(320 * ratio)), 18)
            pygame.draw.rect(panel, (76, 134, 214), fill, border_radius=3)
            panel.blit(self.font_small.render(label[:46], True, (233, 241, 250)), (x + 6, y + 1))
            x += 335
            if x + 320 > panel.get_width():
                x = 12
                y += 22
        self.screen.blit(panel, (16, 88))

    def _draw_feed_panel(self) -> None:
        w, h = 740, 200
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((18, 25, 37, 210))
        pygame.draw.rect(panel, COLORS["panel_line"], panel.get_rect(), width=1, border_radius=8)
        panel.blit(self.font.render("动态日志", True, COLORS["text"]), (12, 8))
        y = 34
        for item in self.feed[-7:]:
            text = self.font_small.render(item[:103], True, COLORS["text_dim"])
            panel.blit(text, (16, y))
            pygame.draw.circle(panel, (128, 178, 114), (10, y + 7), 2)
            y += 24
        self.screen.blit(panel, (16, SCREEN.height - h - 16))

    def _draw_info_panel(self) -> None:
        w, h = 520, 432
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill(COLORS["panel_alpha"])
        pygame.draw.rect(panel, COLORS["panel_line"], panel.get_rect(), width=1, border_radius=8)
        panel.blit(self.font.render("情报面板 (Tab开关)", True, COLORS["text"]), (12, 10))
        y = 40
        panel.blit(self.font_small.render(f"季节: {self.town.season}", True, COLORS["text_dim"]), (12, y))
        y += 20
        panel.blit(self.font_small.render(f"天气: {self.town.weather} ({self.town.weather_intensity:.2f})", True, COLORS["text_dim"]), (12, y))
        y += 24
        panel.blit(self.font.render("主线章节", True, COLORS["text"]), (12, y))
        y += 24
        panel.blit(self.font_small.render(self.town.story.title, True, COLORS["text_dim"]), (12, y))
        y += 20
        panel.blit(self.font_small.render(self.town.story.objective, True, COLORS["text_dim"]), (12, y))
        y += 24
        overall, rows = self.campaign.chapter_progress(self.town, self.player)
        panel.blit(self.font_small.render(f"章节完成度 {int(overall * 100)}%", True, COLORS["text_dim"]), (12, y))
        y += 20
        for label, ratio in rows[:3]:
            bg = pygame.Rect(12, y, 320, 16)
            pygame.draw.rect(panel, (23, 34, 50), bg, border_radius=3)
            pygame.draw.rect(panel, (89, 164, 110), pygame.Rect(bg.x, bg.y, int(bg.width * ratio), 16), border_radius=3)
            panel.blit(self.font_small.render(label[:40], True, (236, 243, 251)), (18, y))
            y += 20
        y += 4

        panel.blit(self.font.render("今日任务", True, COLORS["text"]), (12, y))
        y += 24
        if not self.town.active_quests:
            panel.blit(self.font_small.render("暂无任务", True, COLORS["text_dim"]), (12, y))
            y += 22
        for quest in self.town.active_quests[:3]:
            mark = "已领" if quest.claimed else ("完成" if quest.completed else "进行中")
            text = f"- {quest.title} [{mark}] {quest.progress}/{quest.target}"
            panel.blit(self.font_small.render(text[:75], True, COLORS["text_dim"]), (12, y))
            y += 21
        self.screen.blit(panel, (SCREEN.width - w - 16, SCREEN.height - h - 16))

    def _draw_hints(self) -> None:
        hints = "WASD/方向键移动 Shift冲刺 左键移动/交互 右键洞察 P暂停 O设置 H帮助 Esc菜单"
        hint_panel = pygame.Surface((860, 26), pygame.SRCALPHA)
        hint_panel.fill((20, 28, 40, 190))
        pygame.draw.rect(hint_panel, (106, 132, 168), hint_panel.get_rect(), width=1, border_radius=6)
        hint_panel.blit(self.font_small.render(hints[:180], True, (220, 230, 246)), (10, 4))
        self.screen.blit(hint_panel, (16, SCREEN.height - 34))

    def _draw_context_prompt(self) -> None:
        zone = self.world.zone_at(self.player.x, self.player.y)
        npc = nearest_npc(self.npcs, self.player.x, self.player.y, SIM.interaction_radius + 10)
        lines: list[str] = []
        if zone is not None:
            level = self.town.zone_levels.get(zone.name, 1)
            lines.append(f"区域: {zone.label} Lv{level}")
        if npc is not None:
            dist = self._distance(self.player.x, self.player.y, npc.x, npc.y)
            lines.append(f"附近居民: {npc.name}({npc.role}) 距离{int(dist)} 按E对话/按T交易")
        if not lines:
            return
        panel = pygame.Surface((440, 54), pygame.SRCALPHA)
        panel.fill((18, 26, 38, 210))
        pygame.draw.rect(panel, (106, 132, 168), panel.get_rect(), width=1, border_radius=6)
        y = 6
        for line in lines[:2]:
            panel.blit(self.font_small.render(line[:58], True, (225, 234, 246)), (10, y))
            y += 22
        self.screen.blit(panel, (16, 172))

    def _draw_pause_overlay(self) -> None:
        overlay = pygame.Surface((SCREEN.width, SCREEN.height), pygame.SRCALPHA)
        overlay.fill((8, 12, 22, 110))
        self.screen.blit(overlay, (0, 0))
        label = self.font_big.render("游戏已暂停", True, (237, 245, 255))
        hint = self.font.render("按 P 继续", True, (201, 215, 236))
        self.screen.blit(label, (SCREEN.width // 2 - label.get_width() // 2, SCREEN.height // 2 - 34))
        self.screen.blit(hint, (SCREEN.width // 2 - hint.get_width() // 2, SCREEN.height // 2 + 10))

    def _draw_help_overlay(self) -> None:
        panel = pygame.Surface((700, 300), pygame.SRCALPHA)
        panel.fill((12, 18, 31, 232))
        pygame.draw.rect(panel, COLORS["panel_line"], panel.get_rect(), width=1, border_radius=10)
        lines = [
            "完整目标：完成三章主线并避免连续3天崩盘",
            "设置支持：画质、纹理细节、特效等级、天气特效、BGM/SFX音量",
            "左键可移动到指定位置或直接与NPC交互，右键可洞察NPC，Shift可冲刺",
            "季节每10天轮换，天气会影响经济/文化/治安",
            "按P暂停，按H关闭帮助",
        ]
        y = 18
        for line in lines:
            panel.blit(self.font_small.render(line, True, (220, 230, 244)), (16, y))
            y += 38
        self.screen.blit(panel, (SCREEN.width // 2 - 350, SCREEN.height // 2 - 150))

    def _settings_rows(self) -> list[tuple[str, str]]:
        return [
            ("画质档位", self.settings.graphics_quality),
            ("纹理细节", str(self.settings.texture_detail)),
            ("特效等级", str(self.settings.effect_level)),
            ("天气特效", "开" if self.settings.weather_effects else "关"),
            ("主音量", f"{int(self.settings.master_volume * 100)}%"),
            ("BGM音量", f"{int(self.settings.bgm_volume * 100)}%"),
            ("SFX音量", f"{int(self.settings.sfx_volume * 100)}%"),
            ("鼠标交互", "开" if self.settings.mouse_interaction else "关"),
            ("移动速度", f"{self.settings.move_speed_multiplier:.2f}x"),
            ("时间流速", f"{self.settings.time_flow_multiplier:.2f}x"),
            ("显示FPS", "开" if self.settings.show_fps else "关"),
            ("全屏模式", "开" if self.settings.fullscreen else "关"),
        ]

    def _adjust_setting(self, index: int, delta: int, toggle: bool = False) -> None:
        q_levels = ["low", "medium", "high"]
        move_levels = [0.8, 1.0, 1.2, 1.4]
        flow_levels = [0.5, 0.75, 1.0, 1.25, 1.5]

        if index == 0:
            if self.settings.graphics_quality not in q_levels:
                self.settings.graphics_quality = "medium"
            cur = q_levels.index(self.settings.graphics_quality)
            self.settings.graphics_quality = q_levels[(cur + delta) % len(q_levels)]
            self._apply_graphics_preset(self.settings.graphics_quality)
        elif index == 1:
            self.settings.texture_detail = max(0, min(2, self.settings.texture_detail + delta))
        elif index == 2:
            self.settings.effect_level = max(0, min(2, self.settings.effect_level + delta))
        elif index == 3:
            self.settings.weather_effects = not self.settings.weather_effects
        elif index == 4:
            self.settings.master_volume = self._step(self.settings.master_volume, delta, 0.05)
        elif index == 5:
            self.settings.bgm_volume = self._step(self.settings.bgm_volume, delta, 0.05)
        elif index == 6:
            self.settings.sfx_volume = self._step(self.settings.sfx_volume, delta, 0.05)
        elif index == 7:
            self.settings.mouse_interaction = not self.settings.mouse_interaction
        elif index == 8:
            self.settings.move_speed_multiplier = self._cycle_value(self.settings.move_speed_multiplier, move_levels, delta)
        elif index == 9:
            self.settings.time_flow_multiplier = self._cycle_value(self.settings.time_flow_multiplier, flow_levels, delta)
        elif index == 10:
            self.settings.show_fps = not self.settings.show_fps
        elif index == 11:
            self.settings.fullscreen = not self.settings.fullscreen
            self._apply_display_mode()

        self.settings_manager.save(self.settings)
        self.audio.set_volumes(self.settings.master_volume, self.settings.bgm_volume, self.settings.sfx_volume)
        self.audio.play_sfx("confirm" if toggle else "click")

    def _menu_buttons(self) -> list[tuple[str, pygame.Rect]]:
        labels = ["start", "load", "settings", "quit"]
        start_y = 300
        spacing = 56
        width = 240
        height = 42
        out: list[tuple[str, pygame.Rect]] = []
        for idx, label in enumerate(labels):
            rect = pygame.Rect(SCREEN.width // 2 - width // 2, start_y + idx * spacing, width, height)
            out.append((label, rect))
        return out

    def _npc_at_position(self, x: int, y: int, radius: int = 20):
        winner = None
        best = float(radius)
        for npc in self.npcs:
            d = self._distance(x, y, npc.x, npc.y)
            if d <= best:
                best = d
                winner = npc
        return winner

    def _world_pixel_factor(self) -> int:
        if self.settings.graphics_quality == "low":
            return 4
        if self.settings.graphics_quality == "medium":
            return 3
        return 2

    def _pixelate_surface(self, source: pygame.Surface, factor: int) -> pygame.Surface:
        if factor <= 1:
            return source
        w = max(1, SCREEN.width // factor)
        h = max(1, SCREEN.height // factor)
        down = pygame.transform.scale(source, (w, h))
        return pygame.transform.scale(down, (SCREEN.width, SCREEN.height))

    def _daylight_ratio(self) -> float:
        minute = self.town.minute_of_day
        ratio = 0.2 + 0.8 * max(0.0, math.sin((minute / (24 * 60)) * math.pi))
        if self.town.weather in {"fog", "storm"}:
            ratio *= max(0.55, 1.0 - self.town.weather_intensity * 0.35)
        return ratio

    def _clock_text(self) -> str:
        h = self.town.minute_of_day // 60
        m = self.town.minute_of_day % 60
        return f"{h:02d}:{m:02d}"

    def _push_feed(self, msg: str) -> None:
        self.feed.append(msg)
        self.feed = self.feed[-SIM.max_feed_items :]

    @staticmethod
    def _step(value: float, delta: int, step: float) -> float:
        v = value + delta * step
        return max(0.0, min(1.0, round(v, 2)))

    @staticmethod
    def _cycle_value(current: float, choices: list[float], delta: int) -> float:
        idx = min(range(len(choices)), key=lambda i: abs(choices[i] - current))
        idx = (idx + delta) % len(choices)
        return choices[idx]

    @staticmethod
    def _distance(x1: float, y1: float, x2: float, y2: float) -> float:
        return math.hypot(x2 - x1, y2 - y1)

    def _apply_graphics_preset(self, preset: str) -> None:
        if preset == "low":
            self.settings.texture_detail = 0
            self.settings.effect_level = 0
            self.settings.weather_effects = False
        elif preset == "medium":
            self.settings.texture_detail = 1
            self.settings.effect_level = 1
            self.settings.weather_effects = True
        else:
            self.settings.texture_detail = 2
            self.settings.effect_level = 2
            self.settings.weather_effects = True

    @staticmethod
    def _clamp(v: float) -> float:
        return max(0.0, min(1.0, v))
