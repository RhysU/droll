# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Enchantress/Beguiler hero abilities."""

import unittest

import droll.error
import droll.struct
from droll.heroes.enchantress import (
    Enchantress,
    Beguiler,
    _enchantress_ability,
    _beguiler_ability,
)

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


class TestEnchantress(unittest.TestCase):

    def test_enchantress_transforms_monster_to_potion(self):
        """Enchantress transforms 1 monster into 1 potion."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=2, skeleton=1),
            party=droll.struct.Party(fighter=1),
        )
        result = _enchantress_ability(world, _UNUSED, "ability", "goblin")
        self.assertEqual(result.dungeon.goblin, 1)
        self.assertEqual(result.dungeon.potion, 1)
        self.assertFalse(result.ability)

    def test_beguiler_transforms_two_monsters(self):
        """Beguiler transforms 2 monsters into 1 potion when available."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=2, skeleton=1),
            party=droll.struct.Party(fighter=1),
        )
        result = _beguiler_ability(
            world, _UNUSED, "ability", "goblin", "skeleton"
        )
        self.assertEqual(result.dungeon.goblin, 1)
        self.assertEqual(result.dungeon.skeleton, 0)
        self.assertEqual(result.dungeon.potion, 1)

    def test_beguiler_requires_two_when_available(self):
        """Beguiler must transform 2 monsters when 2+ available."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=2, skeleton=1),
            party=droll.struct.Party(fighter=1),
        )
        with self.assertRaises(droll.error.DrollError):
            _beguiler_ability(world, _UNUSED, "ability", "goblin")

    def test_beguiler_rejects_too_many_targets(self):
        """Beguiler rejects more than 2 targets."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=2, skeleton=1),
            party=droll.struct.Party(fighter=1),
        )
        with self.assertRaises(droll.error.DrollError):
            _beguiler_ability(
                world, _UNUSED, "ability", "goblin", "skeleton", "goblin"
            )

    def test_enchantress_advances_to_beguiler(self):
        """Enchantress advances to Beguiler at 5+ experience."""
        low_xp = droll.struct.World(experience=4)
        high_xp = droll.struct.World(experience=5)
        self.assertEqual(Enchantress.advance(low_xp), Enchantress)
        self.assertEqual(Enchantress.advance(high_xp), Beguiler)
