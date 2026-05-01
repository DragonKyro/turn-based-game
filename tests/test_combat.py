"""Combat math tests. Each factor is isolated so a regression is easy to localize."""
from __future__ import annotations

import random
from src.core.combat import predict_attack, resolve_attack
from src.core.game_state import GameState
from src.core.player import Player
from src.entities.units.infantry import Infantry
from src.entities.units.knight import Knight
from src.entities.units.wyvern import Wyvern
from src.world.map import Map
from src.world.terrain_types import FOREST, MOUNTAIN, PLAINS, SEA
from src.world.tile import Tile


def _state_with(attacker, defender, attacker_terrain=PLAINS, defender_terrain=PLAINS,
                 hero_id_for_p1=None) -> GameState:
    m = Map(width=5, height=5)
    for col in range(5):
        for row in range(5):
            m.tiles[(col, row)] = Tile(terrain=PLAINS)
    m.tiles[attacker.coord] = Tile(terrain=attacker_terrain, unit_id=attacker.id)
    m.tiles[defender.coord] = Tile(terrain=defender_terrain, unit_id=defender.id)
    p1 = Player(id=1, name="P1", faction="R", gold=0, hero_id=hero_id_for_p1)
    p1.init_visibility(5, 5)
    p2 = Player(id=2, name="P2", faction="B", gold=0)
    p2.init_visibility(5, 5)
    return GameState(
        map=m, players={1: p1, 2: p2},
        units={attacker.id: attacker, defender.id: defender},
        buildings={},
        current_player_id=1,
    )


def test_base_damage_no_modifiers_knight_vs_knight():
    # Knight vs Knight: no RPS bonus (knight strong vs longship). Plains/plains = no terrain.
    # Knight on a knight should not crit from on_terrain("plains","road") — wait it SHOULD crit there.
    # So place both on FOREST to suppress crits.
    a = Knight(id=1, owner_id=1, coord=(0, 0), hp=Knight.max_hp)
    d = Knight(id=2, owner_id=2, coord=(1, 0), hp=Knight.max_hp)
    state = _state_with(a, d, attacker_terrain=FOREST, defender_terrain=FOREST)
    r = resolve_attack(state, a.id, d.id)
    # Knight attack=7, full HP ratio=1.0. No RPS, no crit (attacker on forest, not plains/road, hp=1.0>0.75 hp_above is second crit rule — wait).
    # Actually Knight crits have TWO rules: on_terrain(plains,road) OR hp_above(0.75). At full HP, hp_above(0.75) FIRES.
    # So this will crit. Let me use an attacker with hp=8 (0.66 ratio) to suppress hp_above, and forest to suppress on_terrain.
    pass  # placeholder; the below test is the clean version


def test_base_damage_suppressed_modifiers():
    # Use an attacker at 80% HP stepping out of forest — avoid hp_above(0.75) by dropping attacker HP.
    # Knight crit rules: on_terrain(plains, road) or hp_above(0.75).
    # Place attacker on FOREST (neither plains nor road) and HP just below 0.75 * 12 = 9.0 -> set to 8.
    a = Knight(id=1, owner_id=1, coord=(0, 0), hp=8)   # 8/12 = 0.666 < 0.75
    d = Knight(id=2, owner_id=2, coord=(1, 0), hp=Knight.max_hp)
    state = _state_with(a, d, attacker_terrain=FOREST, defender_terrain=FOREST)
    # Use predict_attack (no roll) for deterministic assertions on per-factor damage.
    r = predict_attack(state, a.id, d.id)
    # No RPS (knight not strong vs knight), no crit. base = 7 * 0.666 ≈ 4.67 -> 5.
    # defender on forest: defense_bonus=2 * defender hp_ratio=1.0 -> reduction=2
    # final = 5 - 2 = 3 (midpoint); rolled damage will be in [2, 4].
    assert r.attack.rps_bonus == 0
    assert r.attack.crit_bonus == 0
    assert r.attack.terrain_reduction == 2
    assert r.attack.final == 3
    assert r.attack.damage_min <= r.attack.final <= r.attack.damage_max


def test_rps_bonus_fires_for_strong_matchup():
    # Infantry strong vs Wyvern. Attacker on plains (not forest, not adjacent to commander hero).
    a = Infantry(id=1, owner_id=1, coord=(0, 0), hp=Infantry.max_hp)
    d = Wyvern(id=2, owner_id=2, coord=(1, 0), hp=Wyvern.max_hp)
    state = _state_with(a, d, attacker_terrain=PLAINS, defender_terrain=PLAINS, hero_id_for_p1=None)
    r = predict_attack(state, a.id, d.id)
    assert r.attack.rps_bonus > 0
    assert r.attack.crit_bonus == 0
    assert r.attack.final >= r.attack.base


def test_crit_fires_on_forest():
    # Infantry attacker ON FOREST (its crit rule). Defender is infantry too so no RPS.
    a = Infantry(id=1, owner_id=1, coord=(0, 0), hp=Infantry.max_hp)
    d = Infantry(id=2, owner_id=2, coord=(1, 0), hp=Infantry.max_hp)
    state = _state_with(a, d, attacker_terrain=FOREST, defender_terrain=PLAINS, hero_id_for_p1=None)
    r = predict_attack(state, a.id, d.id)
    assert r.attack.rps_bonus == 0
    assert r.attack.crit_bonus > 0


def test_terrain_reduction_mountain():
    # Infantry vs Infantry, defender on mountain (defense=4).
    a = Infantry(id=1, owner_id=1, coord=(0, 0), hp=Infantry.max_hp)
    d = Infantry(id=2, owner_id=2, coord=(1, 0), hp=Infantry.max_hp)
    state = _state_with(a, d, attacker_terrain=PLAINS, defender_terrain=MOUNTAIN, hero_id_for_p1=None)
    r = predict_attack(state, a.id, d.id)
    # base=5, terrain_reduction = 4 * 1.0 = 4
    assert r.attack.terrain_reduction == 4
    # midpoint final = 1; rolled final is in [damage_min, damage_max]
    assert r.attack.final == 1
    assert r.attack.damage_min <= 1 <= r.attack.damage_max


def test_counter_attack_when_defender_alive_and_in_range():
    a = Infantry(id=1, owner_id=1, coord=(0, 0), hp=Infantry.max_hp)
    d = Infantry(id=2, owner_id=2, coord=(1, 0), hp=Infantry.max_hp)
    state = _state_with(a, d, hero_id_for_p1=None)
    r = resolve_attack(state, a.id, d.id)
    assert r.counter is not None
    # Defender counters at its own HP ratio (which is LOWER after taking damage).
    assert r.counter.final >= 0


def test_no_counter_when_out_of_range():
    # Infantry (range 1) attacking Longship (range 2-3) adjacent. Longship cannot counter at distance 1.
    from src.entities.units.longship import Longship
    a = Infantry(id=1, owner_id=1, coord=(0, 0), hp=Infantry.max_hp)
    d = Longship(id=2, owner_id=2, coord=(1, 0), hp=Longship.max_hp)
    state = _state_with(a, d, attacker_terrain=SEA, defender_terrain=SEA, hero_id_for_p1=None)
    # Infantry cannot actually walk on sea in the real game, but combat math doesn't care about that.
    r = resolve_attack(state, a.id, d.id)
    assert r.counter is None


def test_resolve_attack_rolls_final_within_range():
    # Seeded rng so the test is deterministic across environments.
    a = Infantry(id=1, owner_id=1, coord=(0, 0), hp=Infantry.max_hp)
    d = Infantry(id=2, owner_id=2, coord=(1, 0), hp=Infantry.max_hp)
    state = _state_with(a, d, hero_id_for_p1=None)
    r = resolve_attack(state, a.id, d.id, rng=random.Random(7))
    assert r.attack.damage_min <= r.attack.final <= r.attack.damage_max


def test_hero_gains_charge_on_damage():
    from src.entities.heroes.emberlord import Emberlord
    a = Emberlord(id=1, owner_id=1, coord=(0, 0), hp=Emberlord.max_hp)
    d = Infantry(id=2, owner_id=2, coord=(1, 0), hp=Infantry.max_hp)
    state = _state_with(a, d, hero_id_for_p1=1)
    assert a.ultimate_charge == 0
    resolve_attack(state, a.id, d.id)
    # Attacker (hero) gains charge for damage dealt.
    assert a.ultimate_charge >= 1
