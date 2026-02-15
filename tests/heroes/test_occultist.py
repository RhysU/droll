# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Occultist/Necromancer hero abilities."""

import unittest

import droll.error
import droll.struct
from droll.heroes.occultist import (
    Necromancer,
    Occultist,
    _necromancer_ability,
    _occultist_ability,
)

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


class TestOccultist(unittest.TestCase):

    def test_occultist_transforms_skeleton_to_fighter(self):
        """Occultist transforms 1 skeleton into 1 fighter."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=1, skeleton=2),
            party=droll.struct.Party(cleric=1),
        )
        result = _occultist_ability(world, _UNUSED, "ability", "skeleton")
        # Discard during subsequent regroup phase tested elsewhere
        self.assertEqual(result.dungeon.skeleton, 1)
        self.assertEqual(result.party.fighter, 1)
        self.assertFalse(result.ability)

    def test_occultist_rejects_non_skeleton_target(self):
        """Occultist ability rejects non-skeleton targets."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=1, skeleton=1),
            party=droll.struct.Party(cleric=1),
        )
        with self.assertRaises(droll.error.DrollError):
            _occultist_ability(world, _UNUSED, "ability", "goblin")

    def test_occultist_sets_regroup_discard(self):
        """Occultist marks the created fighter for regroup discard."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(skeleton=1),
            party=droll.struct.Party(cleric=1),
        )
        result = _occultist_ability(world, _UNUSED, "ability", "skeleton")
        self.assertEqual(result.regroup.discard.fighter, 1)

    def test_necromancer_transforms_two_skeletons(self):
        """Necromancer transforms 2 skeletons into 2 fighters when available."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=1, skeleton=2),
            party=droll.struct.Party(cleric=1),
        )
        result = _necromancer_ability(
            world, _UNUSED, "ability", "skeleton", "skeleton"
        )
        # Discard during subsequent regroup phase tested elsewhere
        self.assertEqual(result.dungeon.skeleton, 0)
        self.assertEqual(result.dungeon.goblin, 1)
        self.assertEqual(result.party.fighter, 2)

    def test_necromancer_transforms_one_skeleton(self):
        """Necromancer transforms 1 skeleton into 1 fighter when 1 available."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=1, skeleton=1),
            party=droll.struct.Party(cleric=1),
        )
        result = _necromancer_ability(
            world,
            _UNUSED,
            "ability",
            "skeleton",
        )
        # Discard during subsequent regroup phase tested elsewhere
        self.assertEqual(result.dungeon.skeleton, 0)
        self.assertEqual(result.dungeon.goblin, 1)
        self.assertEqual(result.party.fighter, 1)

    def test_necromancer_sets_regroup_discard(self):
        """Necromancer marks created fighters for regroup discard."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(skeleton=2),
            party=droll.struct.Party(cleric=1),
        )
        result = _necromancer_ability(
            world, _UNUSED, "ability", "skeleton", "skeleton"
        )
        self.assertEqual(result.regroup.discard.fighter, 2)

    def test_necromancer_rejects_non_skeleton_target(self):
        """Necromancer ability rejects non-skeleton targets."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=1, skeleton=2),
            party=droll.struct.Party(cleric=1),
        )
        with self.assertRaises(droll.error.DrollError):
            _necromancer_ability(world, _UNUSED, "ability", "goblin")

    def test_necromancer_rejects_non_skeleton_extra_target(self):
        """Necromancer ability rejects non-skeleton extra targets."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=1, skeleton=2),
            party=droll.struct.Party(cleric=1),
        )
        with self.assertRaises(droll.error.DrollError):
            _necromancer_ability(
                world, _UNUSED, "ability", "skeleton", "goblin"
            )

    def test_occultist_advances_to_necromancer(self):
        """Occultist advances to Necromancer at 5+ experience."""
        low_xp = droll.struct.World(experience=4)
        high_xp = droll.struct.World(experience=5)
        self.assertEqual(Occultist.advance(low_xp), Occultist)
        self.assertEqual(Occultist.advance(high_xp), Necromancer)

    def test_necromancer_does_not_advance(self):
        """Necromancer does not advance further."""
        high_xp = droll.struct.World(experience=10)
        self.assertEqual(Necromancer.advance(high_xp), Necromancer)

