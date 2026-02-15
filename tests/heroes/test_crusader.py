# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Crusader/Paladin hero abilities."""

import random
import unittest

import droll.error
import droll.struct
from droll.heroes.crusader import (
    Crusader,
    Paladin,
    _crusader_ability,
    _paladin_ability,
)


class TestCrusader(unittest.TestCase):

    def test_crusader_ability_adds_fighter(self):
        """Crusader ability adds a fighter to party."""
        state = random.Random(4)
        world = droll.struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=True,
            dungeon=droll.struct.Dungeon(),
            party=droll.struct.Party(fighter=1, cleric=1),
            treasure=droll.struct.Treasure(),
            reserve=droll.struct.Treasure(),
        )
        result = _crusader_ability(world, state.randrange, "ability", "fighter")
        self.assertEqual(result.party.fighter, 2)
        self.assertFalse(result.ability)

    def test_crusader_ability_adds_cleric(self):
        """Crusader ability adds a cleric to party."""
        state = random.Random(4)
        world = droll.struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=True,
            dungeon=droll.struct.Dungeon(),
            party=droll.struct.Party(fighter=1, cleric=1),
            treasure=droll.struct.Treasure(),
            reserve=droll.struct.Treasure(),
        )
        result = _crusader_ability(world, state.randrange, "ability", "cleric")
        self.assertEqual(result.party.cleric, 2)

    def test_crusader_ability_rejects_invalid_target(self):
        """Crusader ability rejects invalid targets like mage."""
        state = random.Random(4)
        world = droll.struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=True,
            dungeon=droll.struct.Dungeon(),
            party=droll.struct.Party(fighter=1, cleric=1),
            treasure=droll.struct.Treasure(),
            reserve=droll.struct.Treasure(),
        )
        with self.assertRaises(droll.error.DrollError):
            _crusader_ability(world, state.randrange, "ability", "mage")

    def test_crusader_advances_to_paladin(self):
        """Crusader advances to Paladin at 5+ experience."""
        low_xp = droll.struct.World(
            delve=1,
            depth=0,
            experience=4,
            ability=True,
            dungeon=None,
            party=None,
            treasure=droll.struct.Treasure(),
            reserve=droll.struct.Treasure(),
        )
        high_xp = droll.struct.World(
            delve=1,
            depth=0,
            experience=5,
            ability=True,
            dungeon=None,
            party=None,
            treasure=droll.struct.Treasure(),
            reserve=droll.struct.Treasure(),
        )
        self.assertEqual(Crusader.advance(low_xp), Crusader)
        self.assertEqual(Crusader.advance(high_xp), Paladin)

    def test_paladin_ability_clears_dungeon(self):
        """Paladin ability consumes treasure and clears dungeon."""
        state = random.Random(4)
        world = droll.struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=2, skeleton=1, dragon=1),
            party=droll.struct.Party(fighter=1, cleric=1),
            treasure=droll.struct.Treasure(elixir=1),
            reserve=droll.struct.Treasure(sword=1, talisman=1),
        )
        result = _paladin_ability(world, state.randrange, "ability", "elixir")
        self.assertEqual(sum(droll.struct.field_values(result.dungeon)), 0)
        self.assertEqual(result.treasure.elixir, 0)
        self.assertFalse(result.ability)

    def test_paladin_ability_opens_chests(self):
        """Paladin ability draws treasure for each chest."""
        state = random.Random(4)
        world = droll.struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=True,
            dungeon=droll.struct.Dungeon(chest=2),
            party=droll.struct.Party(fighter=1),
            treasure=droll.struct.Treasure(bait=1),
            reserve=droll.struct.Treasure(sword=1, talisman=1, sceptre=1),
        )
        pre_treasure = sum(droll.struct.field_values(world.treasure))
        result = _paladin_ability(world, state.randrange, "ability", "bait")
        post_treasure = sum(droll.struct.field_values(result.treasure))
        self.assertEqual(
            post_treasure, pre_treasure - 1 + 2
        )  # -1 consumed, +2 from chests

    def test_paladin_ability_revives_from_potions(self):
        """Paladin ability revives heroes from potions."""
        state = random.Random(4)
        world = droll.struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=True,
            dungeon=droll.struct.Dungeon(potion=2),
            party=droll.struct.Party(fighter=1),
            treasure=droll.struct.Treasure(elixir=1),
            reserve=droll.struct.Treasure(),
        )
        result = _paladin_ability(
            world, state.randrange, "ability", "elixir", "mage", "thief"
        )
        self.assertEqual(result.party.mage, 1)
        self.assertEqual(result.party.thief, 1)

    def test_paladin_ability_requires_treasure(self):
        """Paladin ability fails without specifying treasure."""
        state = random.Random(4)
        world = droll.struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=True,
            dungeon=droll.struct.Dungeon(),
            party=droll.struct.Party(fighter=1),
            treasure=droll.struct.Treasure(elixir=1),
            reserve=droll.struct.Treasure(),
        )
        with self.assertRaises(droll.error.DrollError):
            _paladin_ability(world, state.randrange, "ability")
