# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Mercenary/Commander hero abilities."""

import random
import pytest

from droll import struct
from droll.ability import commander_ability, mercenary_ability
from droll.heroes.mercenary import Commander, Mercenary, _mercenary_roll_party

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


def test_mercenary_roll_party_adds_bonus_scroll():
    """Mercenary roll adds one bonus scroll with regroup discard."""
    randrange = random.Random(4).randrange
    party, regroup = _mercenary_roll_party(7, randrange)
    assert sum(struct.field_values(party)) == 8
    assert regroup.discard.scroll == 1


def testmercenary_ability_defeats_two_monsters():
    """Mercenary ability defeats 2 different monsters."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(goblin=1, skeleton=1),
        party=struct.Party(fighter=2),
    )
    result = mercenary_ability(world, _UNUSED, "ability", ("goblin", "skeleton"))
    assert result.dungeon.goblin == 0
    assert result.dungeon.skeleton == 0
    assert result.party.fighter == 2
    assert not result.ability


def testmercenary_ability_defeats_one_when_only_one():
    """Mercenary ability defeats 1 monster when only 1 exists."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(goblin=1),
        party=struct.Party(fighter=2),
    )
    result = mercenary_ability(world, _UNUSED, "ability", ("goblin",))
    assert result.dungeon.goblin == 0
    assert not result.ability


def testmercenary_ability_requires_target():
    """Mercenary ability requires at least one target."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(goblin=1),
        party=struct.Party(fighter=2),
    )
    with pytest.raises(struct.DrollError):
        mercenary_ability(world, _UNUSED, "ability")


def testcommander_ability_rerolls_dungeon_dice():
    """Commander ability rerolls dungeon dice."""
    randrange = random.Random(7).randrange
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(goblin=2, skeleton=1),
        party=struct.Party(fighter=2),
    )
    result = commander_ability(world, randrange, "ability", ("goblin", "goblin"))
    assert not result.ability
    assert result.party.fighter == 2


def testcommander_ability_rerolls_dragon():
    """Commander ability can reroll dragon dice."""
    randrange = random.Random(7).randrange
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(dragon=3),
        party=struct.Party(fighter=2),
    )
    result = commander_ability(
        world, randrange, "ability", ("dragon", "dragon", "dragon")
    )
    assert not result.ability


def testcommander_ability_requires_target():
    """Commander ability requires at least one target."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(goblin=1),
        party=struct.Party(fighter=2),
    )
    with pytest.raises(struct.DrollError):
        commander_ability(world, _UNUSED, "ability")


def test_commander_fighter_defeats_goblin_plus_additional():
    """Commander fighters defeat all goblins plus one additional."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(goblin=2, skeleton=1),
        party=struct.Party(fighter=2),
    )
    result = Commander.party.fighter.goblin(
        world, _UNUSED, "fighter", ("goblin", "skeleton")
    )
    assert result.dungeon.goblin == 0
    assert result.dungeon.skeleton == 0
    assert result.party.fighter == 1


def test_commander_fighter_defeats_skeleton_plus_additional():
    """Commander fighters defeat one skeleton plus one additional."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(skeleton=2, ooze=1),
        party=struct.Party(fighter=2),
    )
    result = Commander.party.fighter.skeleton(
        world, _UNUSED, "fighter", ("skeleton", "ooze")
    )
    assert result.dungeon.skeleton == 1
    assert result.dungeon.ooze == 0
    assert result.party.fighter == 1


def test_mercenary_advances_to_commander():
    """Mercenary advances to Commander at 5+ experience."""
    low_xp = struct.World(experience=4)
    high_xp = struct.World(experience=5)
    assert Mercenary.advance(low_xp) == Mercenary
    assert Mercenary.advance(high_xp) == Commander
    assert Commander.advance(high_xp) == Commander
