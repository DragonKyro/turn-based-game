# Embercrown

A turn-based tactics game in the spirit of **Advance Wars** and **Wargroove**. Two rival dynasties — Emberdyne vs. Frostmoor — fight over a shattered crown across square-grid battlefields with terrain, fog of war, Land/Vehicle/Air/Water units, Wargroove-style positional critical hits, and heroes whose ultimates charge up over play.

Written in Python 3.11 on [`arcade`](https://api.arcade.academy/) 3.3.

> **Status.** v1 single-player-complete. Select a unit → move-range highlight → click to move → attack-range highlight after moving → click enemy → itemised combat. Hover over an enemy in range to preview damage. Build from your own production buildings (digit keys). Fog of war per active player. Hero ultimates fire on `U` when charged. Capture an enemy HQ to win. Player 2 is driven by a minimal AI that moves toward the nearest enemy, attacks if in range, and produces cheap units with its gold.

---

## Quick start

```bash
# From the project root:
pip install -e ".[dev]"   # arcade + pytest + ruff
python embercrown.py      # open the game; Enter to load level 1; Esc to return / quit
pytest                    # all pure-logic tests (no arcade needed)
```

### Controls

| Key / mouse | Action |
| --- | --- |
| Left-click a unit | Select it (shows move range in blue, attack range in red) |
| Left-click a reachable tile | Move the selected unit there |
| Left-click an enemy in attack range | Attack (shows itemised damage) |
| Left-click your own building with no selection | Open build menu |
| `1`-`9` in build menu | Produce that unit (if you can afford it) |
| Left-click your selected unit on an enemy building | Capture (infantry only, over multiple turns) |
| `E` | End turn |
| `U` | Activate selected hero's ultimate (when fully charged) |
| Arrow keys | Pan camera |
| `Esc` | Back to menu |

### Extending the game

**New level:** drop a JSON file into [src/data/levels/](src/data/levels/) following the schema in [src/data/levels/schema.md](src/data/levels/schema.md). Change `DEFAULT_LEVEL` in [src/config.py](src/config.py) to point to it (or wire a level-select menu later).

**New unit kind:** add a subclass in `src/entities/units/` following the pattern in [src/entities/units/infantry.py](src/entities/units/infantry.py). Register it in [src/entities/units/__init__.py](src/entities/units/__init__.py). Attach positional crit rules from [src/entities/crit_rules.py](src/entities/crit_rules.py) (or write your own predicate).

**New building kind:** add a subclass in `src/entities/buildings/` and register it. Production buildings set `produces_class` and `produces_kinds`; currency buildings set `gold_per_turn`.

**New hero:** subclass [src/entities/hero.py](src/entities/hero.py), implement `activate_ultimate(state) -> list[dict]`, register in `src/entities/heroes/__init__.py`.

All of the above work through the existing action spine ([src/core/game_rules.py](src/core/game_rules.py)) with no engine changes needed.

## Project layout

```
embercrown.py                     # arcade.Window entry, loads MenuView
src/
  config.py                       # window size, tile size, colors, paths
  core/                           # PURE LOGIC — no arcade imports
    types.py                      # Coord alias, UnitClass / VisState enums
    coord.py                      # grid<->pixel, neighbors, manhattan, within_range
    player.py                     # Player (gold, visibility grid, hero_id)
    game_state.py                 # GameState (map + units + buildings + players + turn)
  entities/                       # unit / hero / building classes + concrete subclasses
    unit.py  hero.py  building.py crit_rules.py
    units/     infantry.py knight.py wyvern.py longship.py + UNIT_REGISTRY
    heroes/    emberlord.py frostqueen.py                   + HERO_REGISTRY
    buildings/ stronghold.py barracks.py stable.py aerie.py harbor.py mine.py + BUILDING_REGISTRY
  world/                          # map, terrain, tile, level JSON loader
    terrain.py  terrain_types.py  tile.py  map.py  level.py  level_loader.py
  engine/                         # arcade glue — the ONLY place arcade is imported
    menu_view.py  game_view.py  camera.py  renderer.py
  ui/                             # HUD / panels / popups (scheduled)
  data/levels/
    01_first_clash.json           # sample 16×12 level
    schema.md                     # human-readable level-file format
assets/sprites/{units,buildings,terrain,heroes,ui}/   # placeholders; art is flat rects + letters for now
tests/                            # pytest: coord, map, terrain, level loader, entities
```

## Architecture in one paragraph

`GameState` owns everything and lives in pure Python with no arcade imports. The engine layer (`src/engine/`) reads state and renders; it never lets arcade types leak into core logic. Actions (move, attack, build, capture, end-turn, activate-ultimate) are reified as plain dataclasses applied through a single `apply_action(state, action)` entry point, so the UI, the AI, and tests all drive the game through the same spine. Unit and building stats live in code as `ClassVar`s on typed subclasses; levels live in JSON under `src/data/levels/` and are validated on load.

## Theme

**Embercrown.** Two rival royal houses: fiery **Emberdyne** (red-orange) and icy **Frostmoor** (blue). Each commands a shared roster — infantry, knights (vehicle), wyverns (air), longships (water) — built out of a Stronghold, Barracks, Stable, Aerie, and Harbor. Mines produce gold. Heroes differ: the **Emberlord** unleashes a 2-tile burn, while the **Frostqueen** heals allies to full.

## Level authoring

A level is a JSON file describing the map grid, terrain legend, players, buildings, and starting units. See `src/data/levels/schema.md`. Drop a new file into `src/data/levels/` and load it by bare name (no extension).

## Running tests

```bash
pytest                 # whole suite
pytest tests/test_combat.py -v   # one module
```

All pure-logic modules (coord, map, terrain, level loader, entities) are covered. Arcade rendering is exercised by running `embercrown.py`.

## Roadmap

See `C:\Users\klui\.claude\plans\generic-dreaming-wand.md` for the full plan. Current progress:

- [x] Project scaffold, asset/test directories, `.gitignore`, `pyproject.toml`
- [x] Coord / Terrain / Map foundations
- [x] Level JSON loader + sample level + validator
- [x] Terrain, unit, and building rendering
- [x] Unit / Hero / Building registries with ClassVar-based stats
- [x] Pathfinding + reachable-range overlay
- [x] Action spine + Move / Attack / Build / Capture / EndTurn / ActivateUltimate
- [x] Turn manager + economy (gold awarded from Mines and Strongholds)
- [x] Fog of war (per-player VisState grids)
- [x] Hero ultimates wired (Emberlord AoE dmg, Frostqueen AoE heal)
- [x] Minimal HUD + build menu popup
- [x] Capture → victory
- [x] Dumb AI for player 2 (moves toward nearest enemy, attacks, spends gold on cheapest unit)
- [x] UX polish: cached HUD `arcade.Text`, unit-info panel, damage preview on enemy hover
