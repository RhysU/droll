# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Minstrel/Bard hero abilities."""

import unittest

import droll.error
import droll.struct
from droll.heroes.minstrel import Minstrel, Bard, _minstrel_ability
import droll.action

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


class TestMinstrel(unittest.TestCase):

    def test_minstrel_ability_discards_dragons(self):
        """Minstrel/Bard ability discards all dragon dice."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=1, dragon=3),
            party=droll.struct.Party(fighter=1),
        )
        result = _minstrel_ability(world, _UNUSED, "ability")
        self.assertEqual(result.dungeon.dragon, 0)
        self.assertEqual(result.dungeon.goblin, 1)
        self.assertFalse(result.ability)

    def test_minstrel_ability_rejects_non_dragon(self):
        """Minstrel/Bard ability only works on dragons."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=1, dragon=3),
            party=droll.struct.Party(fighter=1),
        )
        with self.assertRaises(droll.error.DrollError):
            _minstrel_ability(world, _UNUSED, "ability", "goblin")

    def test_minstrel_advances_to_bard(self):
        """Minstrel advances to Bard at 5+ experience."""
        low_xp = droll.struct.World(experience=4)
        high_xp = droll.struct.World(experience=5)
        self.assertEqual(Minstrel.advance(low_xp), Minstrel)
        self.assertEqual(Minstrel.advance(high_xp), Bard)

    def test_bard_champion_defeats_plus_one(self):
        """Bard's champion defeats all of one type plus one additional."""
        world = droll.struct.World(
            dungeon=droll.struct.Dungeon(goblin=2, skeleton=1),
            party=droll.struct.Party(champion=1),
        )
        result = droll.action.defeat_all_plus_additional(
            world, _UNUSED, "champion", "goblin", "skeleton"
        )
        self.assertEqual(result.dungeon.goblin, 0)
        self.assertEqual(result.dungeon.skeleton, 0)
        self.assertEqual(result.party.champion, 0)

    def test_bard_champion_no_additional_when_cleared(self):
        """Bard's champion needs no additional when monsters cleared."""
        world = droll.struct.World(
            dungeon=droll.struct.Dungeon(goblin=2),
            party=droll.struct.Party(champion=1),
        )
        result = droll.action.defeat_all_plus_additional(
            world, _UNUSED, "champion", "goblin"
        )
        self.assertEqual(result.dungeon.goblin, 0)

    def test_bard_champion_rejects_extra_additional(self):
        """Bard's champion rejects more than one additional target."""
        world = droll.struct.World(
            dungeon=droll.struct.Dungeon(goblin=1, skeleton=2),
            party=droll.struct.Party(champion=1),
        )
        with self.assertRaises(droll.error.DrollError):
            droll.action.defeat_all_plus_additional(
                world,
                _UNUSED,
                "champion",
                "goblin",
                "skeleton",
                "skeleton",
            )

    def test_bard_champion_requires_additional_when_monsters_remain(self):
        """Bard's champion requires additional target when monsters remain."""
        world = droll.struct.World(
            dungeon=droll.struct.Dungeon(goblin=1, skeleton=1),
            party=droll.struct.Party(champion=1),
        )
        with self.assertRaises(droll.error.DrollError):
            droll.action.defeat_all_plus_additional(
                world,
                _UNUSED,
                "champion",
                "goblin",
            )
