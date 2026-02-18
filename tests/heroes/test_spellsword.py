# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Spellsword/Battlemage hero abilities."""

import pytest

import droll.error
import droll.struct
from droll.heroes.spellsword import (
    Spellsword,
    Battlemage,
    _spellsword_ability,
    _battlemage_ability,
)

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


class TestSpellsword:

    def test_spellsword_ability_adds_fighter(self):
        """Spellsword ability adds a fighter to party."""
        world = droll.struct.World(
            ability=True,
            party=droll.struct.Party(fighter=1, mage=1),
        )
        result = _spellsword_ability(world, _UNUSED, "ability", "fighter")
        assert result.party.fighter == 2
        assert not result.ability

    def test_spellsword_ability_adds_mage(self):
        """Spellsword ability adds a mage to party."""
        world = droll.struct.World(
            ability=True,
            party=droll.struct.Party(fighter=1, mage=1),
        )
        result = _spellsword_ability(world, _UNUSED, "ability", "mage")
        assert result.party.mage == 2

    def test_spellsword_ability_rejects_invalid_target(self):
        """Spellsword ability rejects invalid targets like cleric."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(),
            party=droll.struct.Party(fighter=1, mage=1),
        )
        with pytest.raises(droll.error.DrollError):
            _spellsword_ability(world, _UNUSED, "ability", "cleric")

    def test_battlemage_ability_clears_dungeon(self):
        """Battlemage ability clears entire dungeon."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(
                goblin=2, chest=1, potion=1, dragon=2
            ),
            party=droll.struct.Party(fighter=1, mage=1),
        )
        result = _battlemage_ability(world, _UNUSED, "ability")
        assert sum(droll.struct.field_values(result.dungeon)) == 0
        assert not result.ability

    def test_spellsword_ability_default_target(self):
        """Spellsword ability defaults to 'fighter' (first sorted) when no target."""
        world = droll.struct.World(
            ability=True,
            party=droll.struct.Party(fighter=1, mage=1),
        )
        result = _spellsword_ability(world, _UNUSED, "ability")
        assert result.party.fighter == 2

    def test_battlemage_ability_rejects_target(self):
        """Battlemage ability rejects any target argument."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=1),
            party=droll.struct.Party(fighter=1, mage=1),
        )
        with pytest.raises(droll.error.DrollError):
            _battlemage_ability(world, _UNUSED, "ability", "goblin")

    def test_spellsword_advances_to_battlemage(self):
        """Spellsword advances to Battlemage at 5+ experience."""
        low_xp = droll.struct.World(experience=4)
        high_xp = droll.struct.World(experience=5)
        assert Spellsword.advance(low_xp) == Spellsword
        assert Spellsword.advance(high_xp) == Battlemage
