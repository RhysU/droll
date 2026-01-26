# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Spellsword/Battlemage hero abilities."""

import random

import pytest

import droll.error
import droll.struct
from droll.heroes.spellsword import (
    Spellsword, Battlemage, spellsword_ability, battlemage_ability
)


def test_spellsword_ability_adds_fighter():
    """Spellsword ability adds a fighter to party."""
    state = random.Random(4)
    world = droll.struct.World(
        delve=1, depth=1, experience=0, ability=True,
        dungeon=droll.struct.Dungeon(),
        party=droll.struct.Party(fighter=1, mage=1),
        treasure=droll.struct.Treasure(), reserve=droll.struct.Treasure(),
    )
    result = spellsword_ability(world, state.randrange, "ability", "fighter")
    assert result.party.fighter == 2
    assert result.ability is False


def test_spellsword_ability_adds_mage():
    """Spellsword ability adds a mage to party."""
    state = random.Random(4)
    world = droll.struct.World(
        delve=1, depth=1, experience=0, ability=True,
        dungeon=droll.struct.Dungeon(),
        party=droll.struct.Party(fighter=1, mage=1),
        treasure=droll.struct.Treasure(), reserve=droll.struct.Treasure(),
    )
    result = spellsword_ability(world, state.randrange, "ability", "mage")
    assert result.party.mage == 2


def test_spellsword_ability_rejects_invalid_target():
    """Spellsword ability rejects invalid targets like cleric."""
    state = random.Random(4)
    world = droll.struct.World(
        delve=1, depth=1, experience=0, ability=True,
        dungeon=droll.struct.Dungeon(),
        party=droll.struct.Party(fighter=1, mage=1),
        treasure=droll.struct.Treasure(), reserve=droll.struct.Treasure(),
    )
    with pytest.raises(droll.error.DrollError):
        spellsword_ability(world, state.randrange, "ability", "cleric")


def test_battlemage_ability_clears_dungeon():
    """Battlemage ability clears entire dungeon."""
    state = random.Random(4)
    world = droll.struct.World(
        delve=1, depth=1, experience=0, ability=True,
        dungeon=droll.struct.Dungeon(goblin=2, chest=1, potion=1, dragon=2),
        party=droll.struct.Party(fighter=1, mage=1),
        treasure=droll.struct.Treasure(), reserve=droll.struct.Treasure(),
    )
    result = battlemage_ability(world, state.randrange, "ability")
    assert sum(droll.struct.field_values(result.dungeon)) == 0
    assert result.ability is False


def test_spellsword_advances_to_battlemage():
    """Spellsword advances to Battlemage at 5+ experience."""
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
    assert Spellsword.advance(low_xp) == Spellsword
    assert Spellsword.advance(high_xp) == Battlemage
