# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of dice rolling boundary conditions."""

import random
import unittest

from droll.dice import roll_dungeon, roll_party
from droll.struct import field_values


class TestDice(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures with a seeded random number generator."""
        self.randrange = random.Random(4).randrange

    def test_roll_zero_dice(self):
        """Rolling zero dice should return empty results."""
        party = roll_party(dice=0, randrange=self.randrange)
        self.assertEqual(sum(field_values(party)), 0)

    def test_roll_dungeon_minimum(self):
        """Roll dungeon with minimum (1) dice."""
        dungeon = roll_dungeon(dice=1, randrange=self.randrange)
        self.assertEqual(sum(field_values(dungeon)), 1)

    def test_roll_dungeon_zero_fails(self):
        """Rolling dungeon with zero dice should fail."""
        with self.assertRaises(AssertionError):
            roll_dungeon(dice=0, randrange=self.randrange)

    def test_roll_party_many_dice(self):
        """Roll party with many dice to ensure no overflow issues."""
        party = roll_party(dice=100, randrange=self.randrange)
        self.assertEqual(sum(field_values(party)), 100)
