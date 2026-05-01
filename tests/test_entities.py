"""Sanity tests that all concrete entity classes instantiate and appear in their registries."""
from __future__ import annotations

from src.entities.buildings import BUILDING_REGISTRY
from src.entities.heroes import HERO_REGISTRY
from src.entities.units import UNIT_REGISTRY


def test_unit_registry_populated():
    assert set(UNIT_REGISTRY) >= {
        "infantry", "archer", "spearman",
        "knight", "scout", "ballista",
        "wyvern", "griffon",
        "longship", "warship",
    }


def test_hero_registry_populated():
    assert set(HERO_REGISTRY) == {"emberlord", "frostqueen"}


def test_building_registry_populated():
    assert set(BUILDING_REGISTRY) == {"stronghold", "barracks", "stable", "aerie", "harbor", "mine"}


def test_unit_kinds_match_registry_keys():
    for key, cls in UNIT_REGISTRY.items():
        assert cls.kind == key, f"{cls.__name__}.kind != registry key {key!r}"
    for key, cls in HERO_REGISTRY.items():
        assert cls.kind == key, f"{cls.__name__}.kind != registry key {key!r}"
    for key, cls in BUILDING_REGISTRY.items():
        assert cls.kind == key, f"{cls.__name__}.kind != registry key {key!r}"


def test_units_instantiate_with_class_stats():
    infantry_cls = UNIT_REGISTRY["infantry"]
    u = infantry_cls(id=1, owner_id=1, coord=(0, 0), hp=infantry_cls.max_hp)
    assert u.hp == infantry_cls.max_hp
    assert u.unit_class.name == "LAND"
    assert u.is_alive


def test_hero_starts_with_zero_charge():
    hero_cls = HERO_REGISTRY["emberlord"]
    h = hero_cls(id=2, owner_id=1, coord=(1, 1), hp=hero_cls.max_hp)
    assert h.ultimate_charge == 0
    assert not h.can_activate_ultimate()


def test_buildings_declare_production_or_gold():
    for cls in BUILDING_REGISTRY.values():
        # A building should produce something, generate gold, or be an HQ (which does both).
        assert cls.produces_kinds or cls.gold_per_turn > 0 or cls.is_hq
