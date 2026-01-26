# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Crusader/Paladin hero abilities."""

import random

import pytest

import droll.error
import droll.struct
from droll.heroes.crusader import Crusader, Paladin, crusader_ability


def test_crusader_ability_adds_fighter():
    """Crusader ability adds a fighter to party."""
    state = random.Random(4)
    world = droll.struct.World(
        delve=1, depth=1, experience=0, ability=True,
        dungeon=droll.struct.Dungeon(),
        party=droll.struct.Party(fighter=1, cleric=1),
        treasure=droll.struct.Treasure(), reserve=droll.struct.Treasure(),
    )
    result = crusader_ability(world, state.randrange, "ability", "fighter")
    assert result.party.fighter == 2
    assert result.ability is False


def test_crusader_ability_adds_cleric():
    """Crusader ability adds a cleric to party."""
    state = random.Random(4)
    world = droll.struct.World(
        delve=1, depth=1, experience=0, ability=True,
        dungeon=droll.struct.Dungeon(),
        party=droll.struct.Party(fighter=1, cleric=1),
        treasure=droll.struct.Treasure(), reserve=droll.struct.Treasure(),
    )
    result = crusader_ability(world, state.randrange, "ability", "cleric")
    assert result.party.cleric == 2


def test_crusader_ability_rejects_invalid_target():
    """Crusader ability rejects invalid targets like mage."""
    state = random.Random(4)
    world = droll.struct.World(
        delve=1, depth=1, experience=0, ability=True,
        dungeon=droll.struct.Dungeon(),
        party=droll.struct.Party(fighter=1, cleric=1),
        treasure=droll.struct.Treasure(), reserve=droll.struct.Treasure(),
    )
    with pytest.raises(droll.error.DrollError):
        crusader_ability(world, state.randrange, "ability", "mage")


def test_crusader_advances_to_paladin():
    """Crusader advances to Paladin at 5+ experience."""
    low_xp = droll.struct.World(
        delve=1, depth=0, experience=4, ability=True,
        dungeon=None, party=None, treasure=droll.struct.Treasure(),
        reserve=droll.struct.Treasure(),
    )
    high_xp = droll.struct.World(
        delve=1, depth=0, experience=5, ability=True,
        dungeon=None, party=None, treasure=droll.struct.Treasure(),
        reserve=droll.struct.Treasure(),
    )
    assert Crusader.advance(low_xp) == Crusader
    assert Crusader.advance(high_xp) == Paladin
