"""Main in-match view. Owns the GameState and drives per-turn input.

Layer order in on_draw (strict):
    terrain (fog-tinted) -> buildings -> move/attack range overlay -> unit sprites
    -> selection ring -> damage-preview bubble -> HUD -> unit panel -> build menu
    -> victory overlay.
"""
from __future__ import annotations

import arcade

from src.config import COLORS, TILE_SIZE
from src.core.actions import ActivateUltimateAction, BuildAction, EndTurnAction
from src.core.ai import take_turn as ai_take_turn
from src.core.coord import grid_to_pixel, pixel_to_grid
from src.core.fog import recompute_visibility
from src.core.game_rules import IllegalAction, apply_action
from src.core.pathfinding import attackable_from, reachable
from src.engine import renderer
from src.engine.camera import Cameras
from src.engine.input_controller import interpret_click
from src.entities.hero import Hero
from src.ui import damage_preview
from src.ui.build_menu import BuildMenu
from src.ui.hud import HUD, VictoryOverlay
from src.ui.unit_panel import UnitPanel
from src.world.level_loader import LevelLoadError, load_level


class GameView(arcade.View):
    def __init__(self, level_name: str) -> None:
        super().__init__()
        self.level_name = level_name
        self.level = None
        self.state = None
        self.cameras = Cameras()
        self.load_error: str | None = None

        self.selected_unit_id: int | None = None
        self.reachable_tiles: dict[tuple[int, int], int] = {}
        self.attack_tiles: set[tuple[int, int]] = set()
        self.build_menu: BuildMenu | None = None
        self.banner: str | None = None
        self.hover_coord: tuple[int, int] | None = None

        # AI scheduling
        self._ai_pending: bool = False
        self._ai_delay: float = 0.0

        # UI objects (arcade.Text caches live on these)
        self._hud: HUD | None = None
        self._unit_panel: UnitPanel | None = None
        self._victory_overlay: VictoryOverlay | None = None
        self._damage_preview_text: arcade.Text | None = None

    # --- lifecycle ---

    def on_show_view(self) -> None:
        self.window.background_color = COLORS["background"]
        try:
            self.level = load_level(self.level_name)
            self.state = self.level.initial_state
            self.cameras.center_on(self.state.map.width, self.state.map.height)
            recompute_visibility(self.state, self.state.current_player_id)
        except LevelLoadError as e:
            self.load_error = str(e)

        self._hud = HUD(self.window.height)
        self._unit_panel = UnitPanel(self.window.width, self.window.height)
        self._victory_overlay = VictoryOverlay(self.window.width, self.window.height)
        self._damage_preview_text = arcade.Text(
            "", 0, 0, COLORS["hero_accent"], font_size=12, bold=True,
        )
        self._schedule_ai_if_needed()

    # --- drawing ---

    def on_draw(self) -> None:
        self.clear()
        if self.load_error:
            arcade.draw_text(
                f"Failed to load level: {self.load_error}",
                20, 40, COLORS["text"], font_size=14,
            )
            return
        assert self.state is not None
        assert self._hud is not None and self._unit_panel is not None
        assert self._victory_overlay is not None

        view_player_id = self.state.current_player_id
        vis = self.state.players[view_player_id].visibility

        self.cameras.world.use()
        renderer.draw_terrain(self.state, vis)
        renderer.draw_buildings(self.state, vis)
        if self.reachable_tiles:
            renderer.draw_move_range(self.reachable_tiles)
        if self.attack_tiles:
            renderer.draw_attack_range(self.attack_tiles)
        renderer.draw_units(self.state, vis, view_player_id)
        if self.selected_unit_id is not None:
            u = self.state.units.get(self.selected_unit_id)
            if u is not None and u.is_alive:
                renderer.draw_selection(u.coord)

        self._draw_damage_preview()

        self.cameras.ui.use()
        self._hud.draw(self.state, view_player_id, self.banner)

        if self.selected_unit_id is not None:
            u = self.state.units.get(self.selected_unit_id)
            if u is not None and u.is_alive:
                self._unit_panel.draw(u)

        if self.build_menu is not None:
            self.build_menu.draw()

        if self.state.victory is not None:
            self._victory_overlay.draw(self.state)

    def _draw_damage_preview(self) -> None:
        """Shown when a unit is selected and you hover over a targetable enemy."""
        assert self.state is not None
        if self.selected_unit_id is None or self.hover_coord is None:
            return
        attacker = self.state.units.get(self.selected_unit_id)
        if attacker is None or not attacker.is_alive or attacker.has_acted:
            return
        target = self.state.unit_at(self.hover_coord)
        if target is None or not target.is_alive or target.owner_id == attacker.owner_id:
            return
        if self.hover_coord not in self.attack_tiles:
            return
        try:
            result = damage_preview.predict(self.state, attacker.id, target.id)
        except Exception:  # noqa: BLE001 — prediction must never crash rendering
            return

        hx, hy = grid_to_pixel(self.hover_coord, TILE_SIZE)
        # Bubble background
        label = f"~{result.attack.final}"
        if result.counter:
            label += f" / cnt {result.counter.final}"
        bubble_w = 10 + len(label) * 8
        arcade.draw_lbwh_rectangle_filled(
            hx - bubble_w / 2, hy + TILE_SIZE * 0.5, bubble_w, 20, COLORS["ui_panel"]
        )
        arcade.draw_lbwh_rectangle_outline(
            hx - bubble_w / 2, hy + TILE_SIZE * 0.5, bubble_w, 20, COLORS["hero_accent"], 1
        )
        if self._damage_preview_text is not None:
            self._damage_preview_text.text = label
            self._damage_preview_text.x = hx - bubble_w / 2 + 6
            self._damage_preview_text.y = hy + TILE_SIZE * 0.5 + 4
            self._damage_preview_text.draw()

    # --- input ---

    def on_mouse_motion(self, x: int, y: int, _dx: int, _dy: int) -> None:
        if self.state is None:
            return
        wx, wy = self._screen_to_world(x, y)
        coord = pixel_to_grid(wx, wy, TILE_SIZE)
        self.hover_coord = coord if self.state.map.in_bounds(coord) else None

    def on_mouse_press(self, x: int, y: int, button: int, _modifiers: int) -> None:
        if self.state is None or self.state.victory is not None:
            return
        wx, wy = self._screen_to_world(x, y)
        coord = pixel_to_grid(wx, wy, TILE_SIZE)
        if not self.state.map.in_bounds(coord):
            return

        if self.build_menu is not None:
            self.build_menu = None

        b = self.state.building_at(coord)
        if self.selected_unit_id is None and b is not None:
            if b.owner_id == self.state.current_player_id and type(b).produces_kinds:
                self.build_menu = BuildMenu(building=b, gold=self.state.players[b.owner_id].gold)
                return

        click = interpret_click(
            self.state, self.selected_unit_id, coord, self.reachable_tiles or None
        )
        for action in click.actions:
            try:
                events = apply_action(self.state, action)
                self._consume_events(events)
            except IllegalAction as e:
                self.banner = f"Illegal: {e}"
        self._update_selection(click.new_selection)

    def on_key_press(self, symbol: int, _modifiers: int) -> None:
        if self.state is None:
            return

        if self.state.victory is not None:
            if symbol == arcade.key.ESCAPE:
                self._return_to_menu()
            return

        if self.build_menu is not None:
            if symbol == arcade.key.ESCAPE:
                self.build_menu = None
                return
            digit = self._digit_from_key(symbol)
            if digit is not None:
                kind = self.build_menu.kind_at_index(digit - 1)
                if kind:
                    try:
                        events = apply_action(
                            self.state,
                            BuildAction(building_id=self.build_menu.building.id, unit_kind=kind),
                        )
                        self._consume_events(events)
                    except IllegalAction as e:
                        self.banner = f"Illegal: {e}"
                    self.build_menu = None
                return
            return

        if symbol == arcade.key.ESCAPE:
            self._return_to_menu()
        elif symbol == arcade.key.E:
            try:
                events = apply_action(self.state, EndTurnAction())
                self._consume_events(events)
                self._update_selection(None)
                self._schedule_ai_if_needed()
            except IllegalAction as e:
                self.banner = f"Illegal: {e}"
        elif symbol == arcade.key.U:
            if self.selected_unit_id is not None:
                u = self.state.units.get(self.selected_unit_id)
                if isinstance(u, Hero):
                    try:
                        events = apply_action(
                            self.state, ActivateUltimateAction(hero_id=u.id)
                        )
                        self._consume_events(events)
                        self._update_selection(None)
                    except IllegalAction as e:
                        self.banner = f"Illegal: {e}"
        elif symbol == arcade.key.LEFT:
            self.cameras.pan(-self.cameras.pan_step, 0)
        elif symbol == arcade.key.RIGHT:
            self.cameras.pan(self.cameras.pan_step, 0)
        elif symbol == arcade.key.UP:
            self.cameras.pan(0, self.cameras.pan_step)
        elif symbol == arcade.key.DOWN:
            self.cameras.pan(0, -self.cameras.pan_step)

    # --- AI scheduling ---

    def on_update(self, delta_time: float) -> None:
        if self._ai_pending and self.state is not None and self.state.victory is None:
            self._ai_delay -= delta_time
            if self._ai_delay <= 0:
                self._run_ai_turn()

    def _schedule_ai_if_needed(self) -> None:
        if self.state is None:
            return
        p = self.state.players.get(self.state.current_player_id)
        if p and p.is_ai and self.state.victory is None:
            self._ai_pending = True
            self._ai_delay = 0.4

    def _run_ai_turn(self) -> None:
        self._ai_pending = False
        assert self.state is not None
        try:
            events = ai_take_turn(self.state)
            self._consume_events(events)
        except Exception as e:  # noqa: BLE001 — AI failure must not crash the game
            self.banner = f"AI error: {e}"
        self._schedule_ai_if_needed()

    # --- internals ---

    def _digit_from_key(self, symbol: int) -> int | None:
        for n in range(1, 10):
            if symbol == getattr(arcade.key, f"KEY_{n}", -1) or symbol == getattr(arcade.key, f"NUM_{n}", -1):
                return n
        return None

    def _screen_to_world(self, x: int, y: int) -> tuple[float, float]:
        return self.cameras.screen_to_world(x, y)

    def _update_selection(self, unit_id: int | None) -> None:
        assert self.state is not None
        self.selected_unit_id = unit_id
        self.reachable_tiles = {}
        self.attack_tiles = set()
        if unit_id is None:
            return
        u = self.state.units.get(unit_id)
        if u is None or not u.is_alive:
            self.selected_unit_id = None
            return
        if not u.has_moved:
            self.reachable_tiles = reachable(self.state, u)
        if not u.has_acted:
            self.attack_tiles = attackable_from(self.state, u, u.coord)

    def _consume_events(self, events: list[dict]) -> None:
        if not events:
            return
        parts: list[str] = []
        for e in events:
            t = e.get("type")
            if t == "attack":
                r = e["result"]
                parts.append(
                    f"Attack: {r.attack.final} dmg"
                    + (f", counter {r.counter.final}" if r.counter else "")
                )
            elif t == "unit_destroyed":
                parts.append(f"Unit {e['unit_id']} destroyed")
            elif t == "capture_progress":
                parts.append(f"Capture {e['progress']}/{e['threshold']}")
            elif t == "building_captured":
                parts.append(f"Captured building {e['building_id']}")
            elif t == "unit_built":
                parts.append(f"Built {e['kind']} at {e['coord']}")
            elif t == "ultimate":
                parts.append(f"Hero ultimate fired ({len(e['effects'])} effects)")
            elif t == "end_turn":
                parts.append(
                    f"Turn {e['turn_number']}: P{e['current_player']} "
                    f"(+{e['income_awarded']}g)"
                )
            elif t == "victory":
                parts.append(f"Victory: P{e['winner_id']} ({e['reason']})")
        self.banner = "   ".join(parts) if parts else None

    def _return_to_menu(self) -> None:
        from src.engine.menu_view import MenuView
        self.window.show_view(MenuView())
