"""Main in-match view. Owns the GameState and drives per-turn input.

Layer order in on_draw (strict):
    terrain (fog-tinted) -> buildings -> move/attack range overlay -> unit sprites -> selection ring
    -> HUD -> build menu / victory banner overlay.
"""
from __future__ import annotations

import arcade

from src.config import COLORS, TILE_SIZE
from src.core.actions import ActivateUltimateAction, BuildAction, EndTurnAction
from src.core.coord import pixel_to_grid
from src.core.fog import recompute_visibility
from src.core.game_rules import IllegalAction, apply_action
from src.core.pathfinding import attackable_from, reachable
from src.engine import renderer
from src.engine.camera import Cameras
from src.engine.input_controller import interpret_click
from src.entities.hero import Hero
from src.ui import hud
from src.ui.build_menu import BuildMenu
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

    # --- lifecycle ---

    def on_show_view(self) -> None:
        self.window.background_color = COLORS["background"]
        try:
            self.level = load_level(self.level_name)
            self.state = self.level.initial_state
            self.cameras.center_on(self.state.map.width, self.state.map.height)
            # initial fog for player 1 (whoever starts)
            recompute_visibility(self.state, self.state.current_player_id)
        except LevelLoadError as e:
            self.load_error = str(e)

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

        self.cameras.ui.use()
        hud.draw(self.state, view_player_id, self.banner, self.window.height)
        hud.draw_controls(self.window.height)
        if self.build_menu is not None:
            self.build_menu.draw()
        if self.state.victory is not None:
            hud.draw_victory(self.state, self.window.width, self.window.height)

    # --- input ---

    def on_mouse_press(self, x: int, y: int, button: int, _modifiers: int) -> None:
        if self.state is None or self.state.victory is not None:
            return
        # Convert screen -> world
        wx, wy = self._screen_to_world(x, y)
        coord = pixel_to_grid(wx, wy, TILE_SIZE)
        if not self.state.map.in_bounds(coord):
            return

        # Close build menu on any off-menu click.
        if self.build_menu is not None:
            self.build_menu = None

        # If the user clicked a production building they own (and no selection), open the menu instead.
        b = self.state.building_at(coord)
        if self.selected_unit_id is None and b is not None:
            if b.owner_id == self.state.current_player_id and type(b).produces_kinds:
                self.build_menu = BuildMenu(building=b, gold=self.state.players[b.owner_id].gold)
                return

        # Otherwise run the standard click interpreter.
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

        # Build menu key handling.
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

    # --- internals ---

    def _digit_from_key(self, symbol: int) -> int | None:
        for n in range(1, 10):
            if symbol == getattr(arcade.key, f"KEY_{n}", -1) or symbol == getattr(arcade.key, f"NUM_{n}", -1):
                return n
        return None

    def _screen_to_world(self, x: int, y: int) -> tuple[float, float]:
        # arcade 3.x Camera2D: world_x = screen_x + camera_position_x
        cx, cy = self.cameras.world.position
        return (x + cx, y + cy)

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
        """Summarise events into the banner text for the user."""
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
                    f"Turn {e['turn_number']}: player {e['current_player']} "
                    f"(+{e['income_awarded']}g)"
                )
            elif t == "victory":
                parts.append(f"Victory: player {e['winner_id']} ({e['reason']})")
        self.banner = "   ".join(parts) if parts else None

    def _return_to_menu(self) -> None:
        from src.engine.menu_view import MenuView
        self.window.show_view(MenuView())
