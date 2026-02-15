# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of dice rolling boundary conditions."""

import random
import unittest

import droll.dice
import droll.struct


class TestDice(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures with a seeded random number generator."""
        self.state = random.Random(4)

    def test_roll_zero_dice(self):
        """Rolling zero dice should return empty results."""
        party = droll.dice.roll_party(dice=0, randrange=self.state.randrange)
        self.assertEqual(sum(droll.struct.field_values(party)), 0)

    def test_roll_dungeon_minimum(self):
        """Roll dungeon with minimum (1) dice."""
        dungeon = droll.dice.roll_dungeon(
            dice=1, randrange=self.state.randrange
        )
        self.assertEqual(sum(droll.struct.field_values(dungeon)), 1)

    def test_roll_dungeon_zero_fails(self):
        """Rolling dungeon with zero dice should fail."""
        with self.assertRaises(AssertionError):
            droll.dice.roll_dungeon(dice=0, randrange=self.state.randrange)

    def test_roll_party_many_dice(self):
        """Roll party with many dice to ensure no overflow issues."""
        party = droll.dice.roll_party(dice=100, randrange=self.state.randrange)
        self.assertEqual(sum(droll.struct.field_values(party)), 100)
