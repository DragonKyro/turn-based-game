"""Tests for the level JSON loader."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.config import LEVELS_DIR
from src.world.level_loader import LevelLoadError, load_level


def test_sample_level_loads_cleanly():
    level = load_level("01_first_clash")
    state = level.initial_state
    m = state.map

    assert m.width == 18
    assert m.height == 12
    # Every tile must be populated.
    assert len(m.tiles) == 18 * 12

    # Two players, each with a hero_id wired.
    assert set(state.players.keys()) == {1, 2}
    for p in state.players.values():
        assert p.hero_id is not None
        assert state.units[p.hero_id].owner_id == p.id

    # Stronghold and production buildings placed.
    kinds = {type(b).__name__.lower(): b for b in state.buildings.values()}
    assert "stronghold" in kinds


def test_missing_file_raises(tmp_path: Path):
    with pytest.raises(LevelLoadError):
        load_level("nonexistent", levels_dir=tmp_path)


def test_unknown_terrain_glyph_raises(tmp_path: Path):
    bad = {
        "name": "bad",
        "width": 2,
        "height": 2,
        "terrain": ["Q.", ".."],
        "terrain_legend": {".": "plains"},  # Q undefined on purpose
        "players": [
            {"id": 1, "name": "P", "faction": "F", "hero": "emberlord", "start_gold": 0, "is_ai": False}
        ],
        "units": [{"kind": "emberlord", "coord": [0, 0], "owner": 1}],
        "victory": {"type": "rout"},
    }
    (tmp_path / "bad.json").write_text(json.dumps(bad))
    with pytest.raises(LevelLoadError, match="unknown terrain glyph"):
        load_level("bad", levels_dir=tmp_path)


def test_out_of_bounds_coord_raises(tmp_path: Path):
    bad = {
        "name": "oob",
        "width": 2,
        "height": 2,
        "terrain": ["..", ".."],
        "terrain_legend": {".": "plains"},
        "players": [
            {"id": 1, "name": "P", "faction": "F", "hero": "emberlord", "start_gold": 0, "is_ai": False}
        ],
        "units": [{"kind": "emberlord", "coord": [5, 5], "owner": 1}],
        "victory": {"type": "rout"},
    }
    (tmp_path / "oob.json").write_text(json.dumps(bad))
    with pytest.raises(LevelLoadError, match="out-of-bounds"):
        load_level("oob", levels_dir=tmp_path)


def test_missing_hero_placement_raises(tmp_path: Path):
    # Player declares a hero but the matching unit isn't placed.
    bad = {
        "name": "nohero",
        "width": 2,
        "height": 2,
        "terrain": ["..", ".."],
        "terrain_legend": {".": "plains"},
        "players": [
            {"id": 1, "name": "P", "faction": "F", "hero": "emberlord", "start_gold": 0, "is_ai": False}
        ],
        "units": [],
        "victory": {"type": "rout"},
    }
    (tmp_path / "nohero.json").write_text(json.dumps(bad))
    with pytest.raises(LevelLoadError, match="no such unit"):
        load_level("nohero", levels_dir=tmp_path)


def test_levels_dir_exists():
    assert LEVELS_DIR.exists(), f"LEVELS_DIR should exist: {LEVELS_DIR}"
