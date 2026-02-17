# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for action module helpers."""

import unittest

import droll.action
import droll.error
import droll.struct

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


class TestDefeatAllPlusAdditional(unittest.TestCase):

    def test_defeats_all_plus_one_additional(self):
        """Defeats all of one type plus one additional."""
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

    def test_no_additional_when_cleared(self):
        """No additional needed when monsters cleared."""
        world = droll.struct.World(
            dungeon=droll.struct.Dungeon(goblin=2),
            party=droll.struct.Party(champion=1),
        )
        result = droll.action.defeat_all_plus_additional(
            world, _UNUSED, "champion", "goblin"
        )
        self.assertEqual(result.dungeon.goblin, 0)

    def test_rejects_extra_additional(self):
        """Rejects more than one additional target."""
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

    def test_requires_additional_when_monsters_remain(self):
        """Requires additional target when monsters remain."""
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


class TestDefeatOnePlusAdditional(unittest.TestCase):

    def test_defeats_one_plus_one_additional(self):
        """Defeats one of primary target plus one additional."""
        world = droll.struct.World(
            dungeon=droll.struct.Dungeon(goblin=2, skeleton=1),
            party=droll.struct.Party(champion=1),
        )
        result = droll.action.defeat_one_plus_additional(
            world, _UNUSED, "champion", "goblin", "skeleton"
        )
        self.assertEqual(result.dungeon.goblin, 1)
        self.assertEqual(result.dungeon.skeleton, 0)
        self.assertEqual(result.party.champion, 0)

    def test_no_additional_when_cleared(self):
        """No additional needed when all monsters cleared after defeating one."""
        world = droll.struct.World(
            dungeon=droll.struct.Dungeon(goblin=1),
            party=droll.struct.Party(fighter=1),
        )
        result = droll.action.defeat_one_plus_additional(
            world, _UNUSED, "fighter", "goblin"
        )
        self.assertEqual(result.dungeon.goblin, 0)
        self.assertEqual(result.party.fighter, 0)

    def test_rejects_additional_when_cleared(self):
        """Rejects additional target when all monsters already cleared."""
        world = droll.struct.World(
            dungeon=droll.struct.Dungeon(goblin=1),
            party=droll.struct.Party(fighter=1),
        )
        with self.assertRaises(droll.error.DrollError):
            droll.action.defeat_one_plus_additional(
                world, _UNUSED, "fighter", "goblin", "skeleton"
            )

    def test_requires_additional_when_monsters_remain(self):
        """Requires additional target when monsters remain after defeating one."""
        world = droll.struct.World(
            dungeon=droll.struct.Dungeon(goblin=1, skeleton=1),
            party=droll.struct.Party(fighter=1),
        )
        with self.assertRaises(droll.error.DrollError):
            droll.action.defeat_one_plus_additional(
                world, _UNUSED, "fighter", "goblin"
            )

    def test_rejects_extra_additional(self):
        """Rejects more than one additional target."""
        world = droll.struct.World(
            dungeon=droll.struct.Dungeon(goblin=1, skeleton=1, ooze=1),
            party=droll.struct.Party(champion=1),
        )
        with self.assertRaises(droll.error.DrollError):
            droll.action.defeat_one_plus_additional(
                world,
                _UNUSED,
                "champion",
                "goblin",
                "skeleton",
                "ooze",
            )

    def test_only_decrements_one_of_primary(self):
        """Defeats only one of the primary target, not all."""
        world = droll.struct.World(
            dungeon=droll.struct.Dungeon(goblin=3, skeleton=1),
            party=droll.struct.Party(champion=1),
        )
        result = droll.action.defeat_one_plus_additional(
            world, _UNUSED, "champion", "goblin", "skeleton"
        )
        self.assertEqual(result.dungeon.goblin, 2)
        self.assertEqual(result.dungeon.skeleton, 0)
        self.assertEqual(result.party.champion, 0)


class TestConvertDungeonToParty(unittest.TestCase):

    def test_converts_up_to_max_count(self):
        """Converts min(available, max_count) dungeon dice to party dice."""
        world = droll.struct.World(
            dungeon=droll.struct.Dungeon(goblin=3),
            party=droll.struct.Party(fighter=1),
        )
        result = droll.action.convert_dungeon_to_party(
            world, source="goblin", destination="thief", max_count=2
        )
        self.assertEqual(result.dungeon.goblin, 1)
        self.assertEqual(result.party.thief, 2)
        self.assertEqual(result.regroup.discard.thief, 2)

    def test_converts_fewer_when_limited(self):
        """Converts only available count when fewer than max_count."""
        world = droll.struct.World(
            dungeon=droll.struct.Dungeon(skeleton=1),
            party=droll.struct.Party(),
        )
        result = droll.action.convert_dungeon_to_party(
            world, source="skeleton", destination="fighter", max_count=2
        )
        self.assertEqual(result.dungeon.skeleton, 0)
        self.assertEqual(result.party.fighter, 1)
        self.assertEqual(result.regroup.discard.fighter, 1)
