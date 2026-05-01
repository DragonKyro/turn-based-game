# Embercrown

A turn-based tactics game in the spirit of **Advance Wars** and **Wargroove**. Two rival dynasties — Emberdyne vs. Frostmoor — fight over a shattered crown across square-grid battlefields with terrain, fog of war, Land/Vehicle/Air/Water units, Wargroove-style positional critical hits, and heroes whose ultimates charge up over play.

Written in Python 3.11 on [`arcade`](https://api.arcade.academy/) 3.3.

> **Status (early scaffold).** The window opens, the menu shows, pressing **Enter** loads the sample level, and terrain + unit + building placements render. Pathfinding, combat, turns, and AI are scheduled next (see the plan in `C:\Users\klui\.claude\plans\generic-dreaming-wand.md`).

---

## Quick start

```bash
# From the project root:
pip install -e ".[dev]"   # arcade + pytest + ruff
python main.py            # open the game; Enter to load level 1; Esc to return / quit
pytest                    # all pure-logic tests (no arcade needed)
```

Arrow keys pan the camera while a level is loaded.

## Project layout

```
main.py                           # arcade.Window entry, loads MenuView
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

All pure-logic modules (coord, map, terrain, level loader, entities) are covered. Arcade rendering is exercised by running `main.py`.

## Roadmap

See `C:\Users\klui\.claude\plans\generic-dreaming-wand.md` for the full plan. Current progress:

- [x] Project scaffold, asset/test directories, `.gitignore`, `pyproject.toml`
- [x] Coord / Terrain / Map foundations
- [x] Level JSON loader + sample level + validator
- [x] Terrain, unit, and building rendering
- [x] Unit / Hero / Building registries with ClassVar-based stats
- [ ] Pathfinding + reachable-range overlay
- [ ] Action spine + Move / Attack / Build / Capture / EndTurn / ActivateUltimate
- [ ] Turn manager + economy (gold awarded from Mines and Strongholds)
- [ ] Fog of war (per-player VisState grids)
- [ ] Hero ultimates wired
- [ ] Dumb AI for player 2
- [ ] HUD, unit panel, action menu popup
