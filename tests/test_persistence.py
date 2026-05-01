"""Round-trip test for save/load: serialize a state, reload, verify key invariants."""
from __future__ import annotations

from pathlib import Path

from src.core.persistence import SaveLoadError, load_from_path, save_to_path
from src.world.level_loader import load_level
import pytest


def test_round_trip_preserves_core_state(tmp_path: Path):
    level = load_level("01_first_clash")
    state = level.initial_state
    # Make the state non-default: mutate a unit and give a player extra gold.
    some_unit = next(iter(state.units.values()))
    some_unit.hp = 3
    some_unit.has_moved = True
    state.players[1].gold = 4242
    state.turn_number = 7
    state.buildings[next(iter(state.buildings))].has_produced = True

    save_path = tmp_path / "save.json"
    save_to_path(state, save_path)
    loaded = load_from_path(save_path)

    assert loaded.turn_number == 7
    assert loaded.players[1].gold == 4242
    assert loaded.units[some_unit.id].hp == 3
    assert loaded.units[some_unit.id].has_moved is True
    assert loaded.map.width == state.map.width
    assert loaded.map.height == state.map.height
    # Terrain preserved at every tile
    for coord in state.map.tiles:
        assert loaded.map.tile(coord).terrain.name == state.map.tile(coord).terrain.name
    # Buildings: ownership + has_produced preserved
    for bid, b in state.buildings.items():
        assert loaded.buildings[bid].owner_id == b.owner_id
        assert loaded.buildings[bid].has_produced == b.has_produced


def test_load_missing_file_raises(tmp_path: Path):
    with pytest.raises(SaveLoadError, match="not found"):
        load_from_path(tmp_path / "nope.json")


def test_load_bad_version_raises(tmp_path: Path):
    p = tmp_path / "old.json"
    p.write_text('{"version": 999, "turn_number": 1, "current_player_id": 1,'
                 '"map": {"width":1,"height":1,"terrain":[["plains"]]},'
                 '"players":[],"units":[],"buildings":[],"victory":null,'
                 '"next_entity_id":1000}')
    with pytest.raises(SaveLoadError, match="unsupported save version"):
        load_from_path(p)
