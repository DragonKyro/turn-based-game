# Level JSON format

Each level file is a JSON object with the following top-level keys.

## `name` (string, required)
Display name.

## `width`, `height` (int, required)
Map dimensions in tiles. The game uses a **bottom-left origin** internally — coord `(col=0, row=0)` is the bottom-left tile — but the `terrain` array in this file is written **top-row-first** for readability. The loader flips it.

## `terrain` (array of strings, required)
Exactly `height` strings, each exactly `width` characters. The first string is the top visual row. Each character is a glyph looked up in `terrain_legend`.

## `terrain_legend` (object, required)
Map from one-character glyph → terrain name. Terrain names must exist in `src/world/terrain_types.TERRAIN_REGISTRY` (currently: `plains`, `forest`, `mountain`, `road`, `sea`). Pick whichever glyphs read clearly — each level may choose its own.

## `players` (array, required, length 2 for v1)
```json
{ "id": 1, "name": "Ember", "faction": "Emberdyne", "hero": "emberlord", "start_gold": 1000, "is_ai": false }
```
`hero` must be a key in `src/entities/heroes.HERO_REGISTRY`. The corresponding hero unit must be placed under `units` with matching `owner`.

## `buildings` (array, optional)
```json
{ "kind": "stronghold", "coord": [col, row], "owner": 1 }
```
`owner` may be `null` for neutral/capturable buildings. `kind` must be a key in `BUILDING_REGISTRY`.

## `units` (array, optional)
```json
{ "kind": "infantry", "coord": [col, row], "owner": 1 }
```
Heroes are specified as units too (`kind: "emberlord"`). The loader links them back to `player.hero_id`. Unit `kind` must be in `UNIT_REGISTRY` or `HERO_REGISTRY`.

## `victory` (object, required)
```json
{ "type": "capture_strongholds" }
```
v1 supports `"capture_strongholds"` (win by capturing all enemy HQs) and `"rout"` (win by eliminating all enemy units).

## Coordinate reminder
All `coord` arrays in this file are `[col, row]` with row=0 meaning the bottom visual row. When reading the `terrain` strings you'll see row=0 at the *bottom* — the loader handles the visual→grid flip.
