# CLAUDE.md

This file orients future Claude Code sessions working on **Embercrown**. Read it before making changes.

## What this project is

A turn-based tactics game (Advance Wars / Wargroove school) in Python 3.11 using the `arcade` library (3.3). Two-player symmetric skirmishes on a square grid with terrain, fog of war, per-class production, rock-paper-scissors unit matchups, Wargroove-style positional critical hits, and heroes whose ultimates charge up over play.

Theme: **Embercrown** — Emberdyne (red) vs. Frostmoor (blue), fighting for a shattered crown.

The full design plan lives at `C:\Users\klui\.claude\plans\generic-dreaming-wand.md` (approved 2026-05-01). Consult it when adding major features.

## The one architectural rule

**`src/core/`, `src/entities/`, `src/world/` import ZERO arcade.**

Arcade lives only in `src/engine/` and `src/ui/`. `GameState` is a pure Python tree that can be tested, pickled, serialized, or replayed. Sprites in the engine layer *mirror* entities (keyed by `unit.id` / `building.id`) — they are never the source of truth. Breaking this firewall unravels testability.

Verify with:
```bash
grep -rn "import arcade" src/core src/entities src/world
# should return nothing
```

## Where things live

| Concern | Location |
| --- | --- |
| Window/event loop entry | [main.py](main.py) |
| Global constants (tile size, window, palette) | [src/config.py](src/config.py) |
| Coord aliases + enums (UnitClass, VisState) | [src/core/types.py](src/core/types.py) |
| Grid math (neighbors, manhattan, grid↔pixel) | [src/core/coord.py](src/core/coord.py) |
| Pure game state | [src/core/game_state.py](src/core/game_state.py) |
| Action dispatch spine | [src/core/actions.py](src/core/actions.py), [src/core/game_rules.py](src/core/game_rules.py) |
| Combat math (itemised result) | [src/core/combat.py](src/core/combat.py) |
| Fog-of-war recompute | [src/core/fog.py](src/core/fog.py) |
| Pathfinding (Dijkstra) | [src/core/pathfinding.py](src/core/pathfinding.py) |
| Economy (income, purchase gates) | [src/core/economy.py](src/core/economy.py) |
| Turn rotation | [src/core/turn_manager.py](src/core/turn_manager.py) |
| Click → Action translator | [src/engine/input_controller.py](src/engine/input_controller.py) |
| HUD / banner / victory overlay | [src/ui/hud.py](src/ui/hud.py) |
| Build menu popup | [src/ui/build_menu.py](src/ui/build_menu.py) |
| Unit-info panel | [src/ui/unit_panel.py](src/ui/unit_panel.py) |
| Damage preview (non-mutating prediction) | [src/ui/damage_preview.py](src/ui/damage_preview.py) |
| Dumb AI for is_ai players | [src/core/ai.py](src/core/ai.py) |
| Unit base + ClassVar stats | [src/entities/unit.py](src/entities/unit.py) |
| Hero base (ultimate_charge) | [src/entities/hero.py](src/entities/hero.py) |
| Building base + flavours | [src/entities/building.py](src/entities/building.py) |
| Concrete units | [src/entities/units/](src/entities/units/) |
| Concrete heroes | [src/entities/heroes/](src/entities/heroes/) |
| Concrete buildings | [src/entities/buildings/](src/entities/buildings/) |
| Crit predicates | [src/entities/crit_rules.py](src/entities/crit_rules.py) |
| Terrain data + registry | [src/world/terrain.py](src/world/terrain.py), [src/world/terrain_types.py](src/world/terrain_types.py) |
| Map grid | [src/world/map.py](src/world/map.py), [src/world/tile.py](src/world/tile.py) |
| Level loader (JSON → GameState) | [src/world/level_loader.py](src/world/level_loader.py) |
| Level files + schema | [src/data/levels/](src/data/levels/) |
| Arcade entry views | [src/engine/menu_view.py](src/engine/menu_view.py), [src/engine/game_view.py](src/engine/game_view.py) |
| Drawing routines | [src/engine/renderer.py](src/engine/renderer.py) |
| Camera wrappers | [src/engine/camera.py](src/engine/camera.py) |

## Conventions

- **Coordinates.** `Coord = tuple[int, int]` is `(col, row)`, origin **bottom-left** (matches arcade's y-up). The `terrain` array in level JSON is written top-row-first for readability; the loader flips it. Never put pixel `(x, y)` and grid `(col, row)` in the same function signature — use `src.core.coord.grid_to_pixel` / `pixel_to_grid`.
- **Unit/building stats** are `ClassVar`s on subclasses (lowercase, e.g. `Infantry.max_hp`), not instance fields. The base `Unit` dataclass only contains per-instance state: `id, owner_id, coord, hp, has_moved, has_acted`.
- **`kind` is a ClassVar**, not a constructor argument. `Infantry.kind == "infantry"` matches the key in `UNIT_REGISTRY`.
- **Tiles hold IDs, not entities.** `Tile.unit_id` and `Tile.building_id` reference `GameState.units[id]` / `GameState.buildings[id]`. Avoids circular refs and keeps maps trivially serializable.
- **No turn phase state machine.** Units carry `has_moved` / `has_acted` flags; the turn manager just rotates players. Interleaved move/build/attack order is fine.
- **Documentation stays current.** Whenever you add or remove a top-level module, update the "Where things live" table in this file *and* the project-layout tree in [README.md](README.md). Same when the roadmap progresses.
- **Dynamic text rendering.** `arcade.draw_text` is slow for per-frame strings. HUD, unit panel, and victory overlay already use cached `arcade.Text` objects. If you add new per-frame text, follow the same pattern (`arcade.Text` instance on the view, mutate `.text` / `.x` / `.y` per frame). The in-map unit-letter labels remain as `draw_text` calls — at v1 scale this is fine, but if maps grow much larger, cache those per-letter too.
- **Stats in code, levels in JSON.** Do not introduce `units.yaml` / `buildings.yaml` stat tables; keep stats on Python subclasses for IDE / refactor safety. Level data is the only data-driven surface.

## Running

```bash
pip install -e ".[dev]"
python main.py     # open game
pytest             # tests
```

## Roadmap position

See the "Roadmap" section of README.md for the live checklist. v1 is feature-complete for single-player: playable loop, fog, capture → victory, hero ultimates, AI opponent, HUD with damage preview and unit-info panel. Next development effort should be gameplay tuning (unit balance, more levels) or v2 features (animations, sound, multi-level campaign, multiplayer, save/load). Do NOT invent scope — ask the user what they want to build next.

## How actions flow (read before touching input / rules)

1. User clicks a tile (mouse) or presses a hotkey (E / U / digits).
2. [src/engine/game_view.py](src/engine/game_view.py) converts screen coords → world coords → grid coord, and hands the state, current selection, and reachable set to [src/engine/input_controller.py](src/engine/input_controller.py)`interpret_click`.
3. `interpret_click` returns a `ClickResult(actions=[...], new_selection=...)`. Actions are defined in [src/core/actions.py](src/core/actions.py) as plain dataclasses.
4. `GameView._consume_events` passes each action to [src/core/game_rules.py](src/core/game_rules.py)`apply_action(state, action)`, which is the **only** place `GameState` mutates (aside from `turn_manager.end_turn` and `fog.recompute_visibility`).
5. `apply_action` returns a list of events (small dicts). `GameView` turns the list into banner text for the HUD.

Keep this pipe clean when adding features: new actions go in `actions.py`, new rules go in `game_rules.py`, new UI shortcuts go in `game_view.py`. The AI (when added) will construct and submit the same Action instances.

## If you're about to change architecture

Stop and check the plan file at `C:\Users\klui\.claude\plans\generic-dreaming-wand.md` — the section "Top 3 architectural risks" calls out the three decisions that hurt most if changed later (engine/core firewall, stats-in-code, one coord convention). Don't silently undo them.
