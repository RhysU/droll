# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Enchantress/Beguiler hero abilities."""

import random
import unittest

import droll.error
import droll.struct
from droll.heroes.enchantress import (
    Enchantress,
    Beguiler,
    _enchantress_ability,
    _beguiler_ability,
)


class TestEnchantress(unittest.TestCase):

    def test_enchantress_transforms_monster_to_potion(self):
        """Enchantress transforms 1 monster into 1 potion."""
        state = random.Random(4)
        world = droll.struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=2, skeleton=1),
            party=droll.struct.Party(fighter=1),
            treasure=droll.struct.Treasure(),
            reserve=droll.struct.Treasure(),
        )
        result = _enchantress_ability(
            world, state.randrange, "ability", "goblin"
        )
        self.assertEqual(result.dungeon.goblin, 1)
        self.assertEqual(result.dungeon.potion, 1)
        self.assertFalse(result.ability)

    def test_beguiler_transforms_two_monsters(self):
        """Beguiler transforms 2 monsters into 1 potion when available."""
        state = random.Random(4)
        world = droll.struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=2, skeleton=1),
            party=droll.struct.Party(fighter=1),
            treasure=droll.struct.Treasure(),
            reserve=droll.struct.Treasure(),
        )
        result = _beguiler_ability(
            world, state.randrange, "ability", "goblin", "skeleton"
        )
        self.assertEqual(result.dungeon.goblin, 1)
        self.assertEqual(result.dungeon.skeleton, 0)
        self.assertEqual(result.dungeon.potion, 1)

    def test_beguiler_requires_two_when_available(self):
        """Beguiler must transform 2 monsters when 2+ available."""
        state = random.Random(4)
        world = droll.struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=2, skeleton=1),
            party=droll.struct.Party(fighter=1),
            treasure=droll.struct.Treasure(),
            reserve=droll.struct.Treasure(),
        )
        with self.assertRaises(droll.error.DrollError):
            _beguiler_ability(world, state.randrange, "ability", "goblin")

    def test_enchantress_advances_to_beguiler(self):
        """Enchantress advances to Beguiler at 5+ experience."""
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
        self.assertEqual(Enchantress.advance(low_xp), Enchantress)
        self.assertEqual(Enchantress.advance(high_xp), Beguiler)
