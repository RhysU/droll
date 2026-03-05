# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Spellsword/Battlemage hero abilities."""

import pytest

from droll import struct
from droll.ability import battlemage_ability, spellsword_ability
from droll.heroes.spellsword import Battlemage, Spellsword
from droll.struct import Action, Dungeon, Party, make_dungeon, make_party

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


def test_spellsword_ability_adds_fighter():
    """Spellsword ability adds a fighter to party."""
    world = struct.World(
        ability=True,
        party=make_party(fighter=1, mage=1),
    )
    result = spellsword_ability(world, _UNUSED, Action.ABILITY, (Party.FIGHTER,))
    assert result.party[Party.FIGHTER] == 2
    assert not result.ability


def test_spellsword_ability_adds_mage():
    """Spellsword ability adds a mage to party."""
    world = struct.World(
        ability=True,
        party=make_party(fighter=1, mage=1),
    )
    result = spellsword_ability(world, _UNUSED, Action.ABILITY, (Party.MAGE,))
    assert result.party[Party.MAGE] == 2


def test_spellsword_ability_rejects_invalid_target():
    """Spellsword ability rejects invalid targets like cleric."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(),
        party=make_party(fighter=1, mage=1),
    )
    with pytest.raises(struct.DrollError):
        spellsword_ability(world, _UNUSED, Action.ABILITY, (Party.CLERIC,))


def test_battlemage_ability_clears_dungeon():
    """Battlemage ability clears entire dungeon."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=2, chest=1, potion=1, dragon=2),
        party=make_party(fighter=1, mage=1),
    )
    result = battlemage_ability(world, _UNUSED, Action.ABILITY)
    assert sum(result.dungeon.values()) == 0
    assert not result.ability


def test_spellsword_ability_default_target():
    """Spellsword ability defaults to 'fighter' when no target."""
    world = struct.World(
        ability=True,
        party=make_party(fighter=1, mage=1),
    )
    result = spellsword_ability(world, _UNUSED, Action.ABILITY)
    assert result.party[Party.FIGHTER] == 2


def test_battlemage_ability_rejects_target():
    """Battlemage ability rejects any target argument."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=1),
        party=make_party(fighter=1, mage=1),
    )
    with pytest.raises(struct.DrollError):
        battlemage_ability(world, _UNUSED, Action.ABILITY, (Dungeon.GOBLIN,))


def test_spellsword_advances_to_battlemage():
    """Spellsword advances to Battlemage at 5+ experience."""
    low_xp = struct.World(experience=4)
    high_xp = struct.World(experience=5)
    assert Spellsword.advance(low_xp) == Spellsword
    assert Spellsword.advance(high_xp) == Battlemage
