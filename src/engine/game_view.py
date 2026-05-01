"""Main in-match view. Owns the GameState and drives per-turn input.

Layer order in on_draw (strict):
    terrain (fog-tinted) -> buildings -> move/attack range overlay -> unit sprites
    -> selection ring -> damage-preview bubble -> HUD -> unit panel -> build menu
    -> victory overlay.
"""
from __future__ import annotations

import arcade

from src.config import COLORS, PROJECT_ROOT, TILE_SIZE
from src.core.actions import ActivateUltimateAction, BuildAction, EndTurnAction
from src.core.ai import take_turn as ai_take_turn
from src.core.coord import grid_to_pixel, pixel_to_grid
from src.core.fog import recompute_visibility
from src.core.game_rules import IllegalAction, apply_action, valid_spawn_tiles
from src.core.pathfinding import attackable_from, reachable
from src.core.options import Options
from src.core.persistence import SaveLoadError, load_from_path, save_to_path
from src.core.types import VisState
from src.engine import renderer
from src.engine.audio import Audio
from src.engine.camera import Cameras
from src.engine.input_controller import interpret_click
from src.engine.moving_unit import MovingUnit
from src.entities.hero import Hero
from src.ui import damage_preview
from src.ui.build_menu import BuildMenu
from src.ui.fight_scene import FightScene
from src.ui.hud import HUD, VictoryOverlay
from src.ui.terrain_info import TerrainInfo
from src.ui.unit_panel import UnitPanel
from src.world.level_loader import LevelLoadError, load_level


class GameView(arcade.View):
    def __init__(self, level_name: str,
                 player_factions: dict[int, str] | None = None) -> None:
        super().__init__()
        self.level_name = level_name
        # Optional {player_id: faction_key} overrides applied after level load.
        self._faction_overrides: dict[int, str] = dict(player_factions or {})
        self.level = None
        self.state = None
        self.cameras = Cameras()
        self.load_error: str | None = None

        self.selected_unit_id: int | None = None
        self.reachable_tiles: dict[tuple[int, int], int] = {}
        self.attack_tiles: set[tuple[int, int]] = set()
        self.build_menu: BuildMenu | None = None
        self.pending_build: tuple[int, str, list[tuple[int, int]]] | None = None
        """None = no pending spawn; else (building_id, unit_kind, valid_spawn_tiles)."""
        self.banner: str | None = None
        self.hover_coord: tuple[int, int] | None = None
        self.view_player_id: int = 1   # real value set in on_show_view

        # AI scheduling
        self._ai_pending: bool = False
        self._ai_delay: float = 0.0
        self._anim_time: float = 0.0  # accumulated seconds since load; drives idle animations
        self._fight_scene: FightScene | None = None
        self._moving_unit: MovingUnit | None = None
        self._event_queue: list[dict] = []
        self._options: Options = Options.load()

        # UI objects (arcade.Text caches live on these)
        self._hud: HUD | None = None
        self._unit_panel: UnitPanel | None = None
        self._victory_overlay: VictoryOverlay | None = None
        self._terrain_info: TerrainInfo | None = None
        self._damage_preview_text: arcade.Text | None = None
        self._load_error_text: arcade.Text | None = None

    # --- lifecycle ---

    def on_show_view(self) -> None:
        self.window.background_color = COLORS["background"]
        if self._options.music_enabled:
            Audio.get().play_music("battle")
        try:
            self.level = load_level(self.level_name)
            self.state = self.level.initial_state
            # Apply faction-select overrides if any.
            for pid, key in self._faction_overrides.items():
                if pid in self.state.players:
                    self.state.players[pid].faction = key
            self.cameras.center_on(self.state.map.width, self.state.map.height)
            # View always belongs to the first non-AI player. Even during the AI's
            # turn we render their perspective, so enemy movement outside the
            # human's fog of war stays hidden.
            self.view_player_id = next(
                (p.id for p in self.state.players.values() if not p.is_ai),
                self.state.current_player_id,
            )
            recompute_visibility(self.state, self.view_player_id)
        except LevelLoadError as e:
            self.load_error = str(e)

        self._hud = HUD(self.window.height)
        self._unit_panel = UnitPanel(self.window.width, self.window.height)
        self._victory_overlay = VictoryOverlay(self.window.width, self.window.height)
        self._terrain_info = TerrainInfo(self.window.height)
        self._damage_preview_text = arcade.Text(
            "", 0, 0, COLORS["hero_accent"], font_size=12, bold=True,
        )
        self._schedule_ai_if_needed()

    # --- drawing ---

    def on_draw(self) -> None:
        self.clear()
        if self.load_error:
            if self._load_error_text is None:
                self._load_error_text = arcade.Text(
                    f"Failed to load level: {self.load_error}",
                    20, 40, COLORS["text"], font_size=14,
                )
            self._load_error_text.draw()
            return
        assert self.state is not None
        assert self._hud is not None and self._unit_panel is not None
        assert self._victory_overlay is not None

        view_player_id = self.view_player_id
        vis = self.state.players[view_player_id].visibility

        self.cameras.world.use()
        renderer.draw_terrain(self.state, vis)
        renderer.draw_buildings(self.state, vis, view_player_id)
        if self.reachable_tiles:
            renderer.draw_move_range(self.reachable_tiles)
        if self.attack_tiles:
            renderer.draw_attack_range(self.attack_tiles)
        if self.pending_build is not None:
            import math
            _bid, _k, tiles = self.pending_build
            pulse = 0.5 + 0.5 * math.sin(self._anim_time * 4.0)
            renderer.draw_spawn_ghosts(tiles, pulse)
        # Hover ring (below selection so selection wins when they coincide).
        if self.hover_coord is not None and self.state.map.in_bounds(self.hover_coord):
            if vis is None or vis[self.hover_coord[0]][self.hover_coord[1]] != VisState.HIDDEN:
                renderer.draw_hover(self.hover_coord)
        skip_unit_id = self._moving_unit.unit_id if self._moving_unit else None
        renderer.draw_units(self.state, vis, view_player_id, self._anim_time,
                            skip_unit_id=skip_unit_id)
        # If a unit is mid-animation, draw it at the interpolated pixel position —
        # but only if that position is currently VISIBLE to the human. Enemy units
        # moving through fog must stay hidden; they appear as they cross into
        # our sight and disappear when they cross back out.
        if self._moving_unit is not None:
            moving = self.state.units.get(self._moving_unit.unit_id)
            if moving is not None:
                cur_tile = self._moving_unit.current_tile()
                tile_vis = (vis[cur_tile[0]][cur_tile[1]]
                            if self.state.map.in_bounds(cur_tile) else VisState.HIDDEN)
                visible = (moving.owner_id == view_player_id
                           or tile_vis == VisState.VISIBLE)
                if visible:
                    mx, my = self._moving_unit.current_pixel()
                    renderer.draw_unit_at(self.state, self._moving_unit.unit_id,
                                          mx, my, self._anim_time)
        if self.selected_unit_id is not None:
            u = self.state.units.get(self.selected_unit_id)
            if u is not None and u.is_alive:
                renderer.draw_selection(u.coord)

        self._draw_damage_preview()

        self.cameras.ui.use()
        # HUD shows whose turn it is (current player); fog/units use view_player_id.
        self._hud.draw(self.state, self.state.current_player_id, self.banner)

        # Terrain-info panel for the hovered tile (only when it is in the human's
        # currently-visible fog set, so we don't leak info about unseen terrain).
        if (
            self.hover_coord is not None
            and self.state.map.in_bounds(self.hover_coord)
            and self._terrain_info is not None
        ):
            hc = self.hover_coord
            vs = vis[hc[0]][hc[1]] if vis is not None else None
            if vs != VisState.HIDDEN:
                terrain = self.state.map.tile(hc).terrain
                self._terrain_info.draw(terrain)

        if self.selected_unit_id is not None:
            u = self.state.units.get(self.selected_unit_id)
            if u is not None and u.is_alive:
                self._unit_panel.draw(u)

        if self.build_menu is not None:
            self.build_menu.draw()

        if self.state.victory is not None:
            self._victory_overlay.draw(self.state)

        # Fight-scene overlay on top of everything else.
        if self._fight_scene is not None:
            self._fight_scene.draw()

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
        # Bubble background — show a RANGE now, not a point estimate.
        label = damage_preview.format_range(result)
        bubble_w = 12 + len(label) * 7
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
        # Build menu owns its own hover (screen-space), bypassing world logic.
        if self.build_menu is not None:
            self.build_menu.on_mouse_motion(x, y)
            # Still update hover_coord for damage preview etc.
        wx, wy = self._screen_to_world(x, y)
        coord = pixel_to_grid(wx, wy, TILE_SIZE)
        self.hover_coord = coord if self.state.map.in_bounds(coord) else None

    def on_mouse_press(self, x: int, y: int, button: int, _modifiers: int) -> None:
        if self.state is None or self.state.victory is not None:
            return
        # Any click skips the fight scene.
        if self._fight_scene is not None:
            self._fight_scene = None
            self._advance_queue()
            return
        # Ignore clicks while a movement animation is playing.
        if self._moving_unit is not None:
            return

        # If a build menu is open, route the click into it first.
        if self.build_menu is not None:
            if self.build_menu.contains_point(x, y):
                kind = self.build_menu.on_mouse_press(x, y)
                if kind is not None:
                    self._try_build(kind)
                return
            # Click outside the menu: close and fall through to normal click handling.
            self.build_menu = None

        wx, wy = self._screen_to_world(x, y)
        coord = pixel_to_grid(wx, wy, TILE_SIZE)
        if not self.state.map.in_bounds(coord):
            return

        # Pending build: clicking a ghost spawn tile commits the build; any other click cancels.
        if self.pending_build is not None:
            building_id, unit_kind, tiles = self.pending_build
            if coord in tiles:
                self._commit_build(building_id, unit_kind, coord)
            else:
                self.pending_build = None
                self.banner = "Build cancelled"
            return

        # If the human clicks their own production building with no selection AND no unit
        # is on that tile, open the build menu. A unit standing on the building always wins
        # the click so it can be selected — otherwise a freshly-built or repositioned unit
        # sitting on its base would be unreachable behind the menu trigger.
        b = self.state.building_at(coord)
        u_here = self.state.unit_at(coord)
        if (self.selected_unit_id is None
                and b is not None
                and u_here is None
                and b.owner_id == self.state.current_player_id
                and type(b).produces_kinds
                and not self.state.players[self.state.current_player_id].is_ai):
            if b.has_produced:
                self.banner = f"{type(b).__name__} already produced this turn"
            else:
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

    def _try_build(self, unit_kind: str) -> None:
        """Stage a pending build — show spawn-tile ghosts; player clicks one to confirm."""
        from src.entities.units import UNIT_REGISTRY
        assert self.state is not None and self.build_menu is not None
        unit_cls = UNIT_REGISTRY.get(unit_kind)
        building = self.build_menu.building
        if unit_cls is None:
            self.banner = f"Unknown unit kind {unit_kind!r}"
            self.build_menu = None
            return
        # Pre-check gold + not-yet-produced so we don't open the ghosts if we can't finish.
        gold = self.state.players[building.owner_id].gold
        if gold < unit_cls.cost:
            self.banner = f"Not enough gold for {unit_kind} (need {unit_cls.cost})"
            self.build_menu = None
            return
        if building.has_produced:
            self.banner = f"{type(building).__name__} already produced this turn"
            self.build_menu = None
            return
        tiles = valid_spawn_tiles(self.state, building.coord, unit_cls.unit_class)
        if not tiles:
            self.banner = f"No open adjacent tile for {unit_kind} to deploy"
            self.build_menu = None
            return
        # If there's only one option, commit immediately — no need to ask which side.
        if len(tiles) == 1:
            self.build_menu = None
            self._commit_build(building.id, unit_kind, tiles[0])
            return
        # Otherwise stage the pending build so the renderer shows ghost markers.
        self.pending_build = (building.id, unit_kind, tiles)
        self.build_menu = None

    def _commit_build(self, building_id: int, unit_kind: str,
                       spawn_coord: tuple[int, int]) -> None:
        assert self.state is not None
        try:
            events = apply_action(
                self.state,
                BuildAction(building_id=building_id, unit_kind=unit_kind,
                             spawn_coord=spawn_coord),
            )
            self._consume_events(events)
        except IllegalAction as e:
            self.banner = f"Illegal: {e}"
        self.pending_build = None

    def on_key_press(self, symbol: int, _modifiers: int) -> None:
        if self.state is None:
            return
        # Space (or any key) cuts the fight scene short.
        if self._fight_scene is not None:
            if symbol in (arcade.key.SPACE, arcade.key.ENTER, arcade.key.ESCAPE):
                self._fight_scene = None
                self._advance_queue()
            return
        # While a unit is mid-step, ignore gameplay keys (Esc still goes to menu).
        if self._moving_unit is not None:
            if symbol == arcade.key.ESCAPE:
                self._return_to_menu()
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
                    self._try_build(kind)
                return
            return

        if symbol == arcade.key.ESCAPE:
            if self.pending_build is not None:
                self.pending_build = None
                self.banner = "Build cancelled"
                return
            self._return_to_menu()
        elif symbol == arcade.key.F5:
            self._quicksave()
        elif symbol == arcade.key.F9:
            self._quickload()
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
        self._anim_time += delta_time
        # Advance movement animation.
        if self._moving_unit is not None:
            self._moving_unit.tick(delta_time)
            if self._moving_unit.done:
                self._moving_unit = None
                self._advance_queue()
        # Tick the fight-scene overlay if one is showing.
        if self._fight_scene is not None:
            self._fight_scene.tick(delta_time)
            if self._fight_scene.done:
                self._fight_scene = None
                self._advance_queue()
        # Pause AI while any animation is playing.
        if self._fight_scene is not None or self._moving_unit is not None:
            return
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
        # Recompute the *human* player's fog after the AI acted: if an AI unit
        # moved into our sight we need to show it; ones that left go back to EXPLORED.
        recompute_visibility(self.state, self.view_player_id)
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
        # Range overlays only make sense for your own actable units.
        if u.owner_id != self.state.current_player_id:
            return
        if not u.has_moved:
            self.reachable_tiles = reachable(self.state, u)
        if not u.has_acted:
            self.attack_tiles = attackable_from(self.state, u, u.coord)

    def _consume_events(self, events: list[dict]) -> None:
        """Enqueue events from one action. The queue is drained as animations finish so
        a Move followed by an Attack animates sequentially (walk first, then fight)."""
        if not events:
            return
        self._event_queue.extend(events)
        self._advance_queue()

    def _advance_queue(self) -> None:
        """Pop and handle queued events until one starts an animation (move or fight)
        or the queue is empty. Animations resume the drain in on_update when they finish."""
        while (
            self._event_queue
            and self._moving_unit is None
            and self._fight_scene is None
        ):
            e = self._event_queue.pop(0)
            self._handle_event(e)

    def _handle_event(self, e: dict) -> None:
        t = e.get("type")
        audio = Audio.get() if self._options.sfx_enabled else None
        if t == "move":
            path = e.get("path") or []
            if len(path) > 1:
                self._moving_unit = MovingUnit(unit_id=e["unit_id"], path=path)
                if audio:
                    audio.play_sfx("move")
            self._set_banner(f"Move to {e['to']}")
        elif t == "attack":
            r = e["result"]
            dmg_note = (
                f"Attack: {r.attack.final} dmg"
                + (f", counter {r.counter.final}" if r.counter else "")
            )
            self._set_banner(dmg_note)
            if audio:
                audio.play_sfx("attack")
            if self._options.show_fight_scene:
                self._trigger_fight_scene(r)
        elif t == "unit_destroyed":
            self._set_banner(f"Unit {e['unit_id']} destroyed")
        elif t == "capture_progress":
            self._set_banner(f"Capture {e['progress']}/{e['threshold']}")
        elif t == "building_captured":
            self._set_banner(f"Captured building {e['building_id']}")
        elif t == "unit_built":
            self._set_banner(f"Built {e['kind']} at {e['coord']}")
            if audio:
                audio.play_sfx("build")
        elif t == "ultimate":
            self._set_banner(f"Hero ultimate fired ({len(e['effects'])} effects)")
        elif t == "end_turn":
            self._set_banner(
                f"Turn {e['turn_number']}: P{e['current_player']} "
                f"(+{e['income_awarded']}g)"
            )
            if audio:
                audio.play_sfx("turn_end")
        elif t == "victory":
            self._set_banner(f"Victory: P{e['winner_id']} ({e['reason']})")
            if audio:
                audio.play_sfx("victory")

    def _set_banner(self, text: str) -> None:
        self.banner = text

    def _trigger_fight_scene(self, result) -> None:
        """Create a one-shot fight-scene overlay from a CombatResult.

        The state has already been mutated by the time this fires, so we read the
        POST-combat HP directly and reconstruct the pre-combat HP by adding back the
        damage that each side took. This lets the scene animate the bar depleting."""
        assert self.state is not None
        a_id = result.attack.attacker_id
        d_id = result.attack.defender_id
        attacker = self.state.units.get(a_id)
        defender = self.state.units.get(d_id)
        if attacker is None or defender is None:
            return
        counter_final = result.counter.final if result.counter else 0
        self._fight_scene = FightScene(
            attacker_kind=attacker.kind,
            attacker_faction=self.state.players[attacker.owner_id].faction,
            attacker_owner=attacker.owner_id,
            attacker_hp_before=attacker.hp + counter_final,
            attacker_hp_after=attacker.hp,
            attacker_hp_max=attacker.max_hp,
            defender_kind=defender.kind,
            defender_faction=self.state.players[defender.owner_id].faction,
            defender_owner=defender.owner_id,
            defender_hp_before=defender.hp + result.attack.final,
            defender_hp_after=defender.hp,
            defender_hp_max=defender.max_hp,
            result=result,
            duration=self._options.fight_scene_duration,
        )

    def _return_to_menu(self) -> None:
        from src.engine.menu_view import MenuView
        self.window.show_view(MenuView())

    # --- save / load ---

    def _quicksave_path(self):
        return PROJECT_ROOT / "saves" / "quicksave.json"

    def _quicksave(self) -> None:
        if self.state is None or self.state.victory is not None:
            return
        try:
            save_to_path(self.state, self._quicksave_path())
            self.banner = f"Quicksaved ({self._quicksave_path().name})"
        except (OSError, SaveLoadError) as e:
            self.banner = f"Save failed: {e}"

    def _quickload(self) -> None:
        path = self._quicksave_path()
        if not path.exists():
            self.banner = "No quicksave to load"
            return
        try:
            new_state = load_from_path(path)
        except SaveLoadError as e:
            self.banner = f"Load failed: {e}"
            return
        self.state = new_state
        # view_player_id stays pinned to the human; refresh their fog for the loaded state.
        recompute_visibility(self.state, self.view_player_id)
        self._update_selection(None)
        self.build_menu = None
        self.banner = f"Loaded quicksave ({path.name})"
        # If the loaded file left an AI on the clock, schedule them.
        self._schedule_ai_if_needed()
