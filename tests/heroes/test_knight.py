# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Knight/DragonSlayer hero abilities."""

import random
import unittest

import droll.dice
import droll.struct
from droll.heroes.knight import Knight, DragonSlayer, _knight_roll_party

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


class TestKnight(unittest.TestCase):

    def test_knight_roll_party_converts_scrolls(self):
        """Knight converts scrolls to champions when rolling party."""
        randrange = random.Random(4).randrange
        party, regroup = _knight_roll_party(7, randrange)
        self.assertEqual(party.scroll, 0)
        self.assertEqual(sum(droll.struct.field_values(party)), 7)
        self.assertEqual(regroup, droll.struct.Regroup())

    def test_knight_ability_baits_dragon(self):
        """Knight ability converts monsters to dragons without treasure."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=2, skeleton=1),
            party=droll.struct.Party(fighter=2, champion=1),
        )
        result = Knight.ability(world, _UNUSED, "ability")
        self.assertEqual(result.dungeon.dragon, 3)
        self.assertEqual(result.dungeon.goblin, 0)
        self.assertEqual(result.dungeon.skeleton, 0)
        self.assertFalse(result.ability)

    def test_dragonslayer_defeats_dragon_with_two_heroes(self):
        """DragonSlayer defeats a dragon with only 2 distinct heroes."""
        randrange = random.Random(4).randrange
        world = droll.struct.World(
            delve=1,
            depth=1,
            dungeon=droll.struct.Dungeon(dragon=3),
            party=droll.struct.Party(fighter=1, mage=1),
            treasure=droll.struct.Treasure(),
            reserve=droll.struct.Treasure(scale=6),
        )
        result = DragonSlayer.party.fighter.dragon(
            world, randrange, "fighter", "dragon", "mage"
        )
        self.assertEqual(result.dungeon.dragon, 0)
        self.assertEqual(result.experience, 1)

    def test_dragonslayer_advance(self):
        """Knight advances to DragonSlayer advances to DragonSlayer."""
        low_xp = droll.struct.World(experience=2)
        mid_xp = droll.struct.World(experience=7)
        high_xp = droll.struct.World(experience=15)
        self.assertEqual(Knight.advance(low_xp), Knight)
        self.assertEqual(Knight.advance(mid_xp), DragonSlayer)
        self.assertEqual(DragonSlayer.advance(high_xp), DragonSlayer)
