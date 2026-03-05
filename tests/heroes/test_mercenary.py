# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Mercenary/Commander hero abilities."""

import random
import pytest

from droll import struct
from droll.ability import commander_ability, mercenary_ability
from droll.heroes.mercenary import Commander, Mercenary, _mercenary_roll_party
from droll.struct import Action, Dungeon, Party, make_dungeon, make_party

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


def test_mercenary_roll_party_adds_bonus_scroll():
    """Mercenary roll adds one bonus scroll with regroup discard."""
    randrange = random.Random(4).randrange
    party, regroup = _mercenary_roll_party(7, randrange)
    assert sum(party.values()) == 8
    assert regroup.discard[Party.SCROLL] == 1


def test_mercenary_ability_defeats_two_monsters():
    """Mercenary ability defeats 2 different monsters."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=1, skeleton=1),
        party=make_party(fighter=2),
    )
    result = mercenary_ability(world, _UNUSED, Action.ABILITY, (Dungeon.GOBLIN, Dungeon.SKELETON))
    assert result.dungeon[Dungeon.GOBLIN] == 0
    assert result.dungeon[Dungeon.SKELETON] == 0
    assert result.party[Party.FIGHTER] == 2
    assert not result.ability


def test_mercenary_ability_defeats_one_when_only_one():
    """Mercenary ability defeats 1 monster when only 1 exists."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=1),
        party=make_party(fighter=2),
    )
    result = mercenary_ability(world, _UNUSED, Action.ABILITY, (Dungeon.GOBLIN,))
    assert result.dungeon[Dungeon.GOBLIN] == 0
    assert not result.ability


def test_mercenary_ability_requires_target():
    """Mercenary ability requires at least one target."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=1),
        party=make_party(fighter=2),
    )
    with pytest.raises(struct.DrollError):
        mercenary_ability(world, _UNUSED, Action.ABILITY)


def test_commander_ability_rerolls_dungeon_dice():
    """Commander ability rerolls dungeon dice."""
    randrange = random.Random(7).randrange
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=2, skeleton=1),
        party=make_party(fighter=2),
    )
    result = commander_ability(world, randrange, Action.ABILITY, (Dungeon.GOBLIN, Dungeon.GOBLIN))
    assert not result.ability
    assert result.party[Party.FIGHTER] == 2


def test_commander_ability_rerolls_dragon():
    """Commander ability can reroll dragon dice."""
    randrange = random.Random(7).randrange
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(dragon=3),
        party=make_party(fighter=2),
    )
    result = commander_ability(
        world, randrange, Action.ABILITY, (Dungeon.DRAGON, Dungeon.DRAGON, Dungeon.DRAGON)
    )
    assert not result.ability


def test_commander_ability_requires_target():
    """Commander ability requires at least one target."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=1),
        party=make_party(fighter=2),
    )
    with pytest.raises(struct.DrollError):
        commander_ability(world, _UNUSED, Action.ABILITY)


def test_commander_fighter_defeats_goblin_plus_additional():
    """Commander fighters defeat all goblins plus one additional."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=2, skeleton=1),
        party=make_party(fighter=2),
    )
    result = Commander.party[Party.FIGHTER][Dungeon.GOBLIN](
        world, _UNUSED, Party.FIGHTER, (Dungeon.GOBLIN, Dungeon.SKELETON)
    )
    assert result.dungeon[Dungeon.GOBLIN] == 0
    assert result.dungeon[Dungeon.SKELETON] == 0
    assert result.party[Party.FIGHTER] == 1


def test_commander_fighter_defeats_skeleton_plus_additional():
    """Commander fighters defeat one skeleton plus one additional."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(skeleton=2, ooze=1),
        party=make_party(fighter=2),
    )
    result = Commander.party[Party.FIGHTER][Dungeon.SKELETON](
        world, _UNUSED, Party.FIGHTER, (Dungeon.SKELETON, Dungeon.OOZE)
    )
    assert result.dungeon[Dungeon.SKELETON] == 1
    assert result.dungeon[Dungeon.OOZE] == 0
    assert result.party[Party.FIGHTER] == 1


def test_mercenary_advances_to_commander():
    """Mercenary advances to Commander at 5+ experience."""
    low_xp = struct.World(experience=4)
    high_xp = struct.World(experience=5)
    assert Mercenary.advance(low_xp) == Mercenary
    assert Mercenary.advance(high_xp) == Commander
    assert Commander.advance(high_xp) == Commander
