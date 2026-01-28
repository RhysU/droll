# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Minstrel/Bard hero abilities."""

import random
import unittest

import droll.error
import droll.struct
from droll.heroes.minstrel import Minstrel, Bard, _minstrel_ability
import droll.action


class TestMinstrel(unittest.TestCase):

    def test_minstrel_ability_discards_dragons(self):
        """Minstrel/Bard ability discards all dragon dice."""
        state = random.Random(4)
        world = droll.struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=1, dragon=3),
            party=droll.struct.Party(fighter=1),
            treasure=droll.struct.Treasure(),
            reserve=droll.struct.Treasure(),
        )
        result = _minstrel_ability(world, state.randrange, "ability")
        assert result.dungeon.dragon == 0
        assert result.dungeon.goblin == 1
        assert result.ability is False

    def test_minstrel_ability_rejects_non_dragon(self):
        """Minstrel/Bard ability only works on dragons."""
        state = random.Random(4)
        world = droll.struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=1, dragon=3),
            party=droll.struct.Party(fighter=1),
            treasure=droll.struct.Treasure(),
            reserve=droll.struct.Treasure(),
        )
        with self.assertRaises(droll.error.DrollError):
            _minstrel_ability(world, state.randrange, "ability", "goblin")

    def test_minstrel_advances_to_bard(self):
        """Minstrel advances to Bard at 5+ experience."""
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
        assert Minstrel.advance(low_xp) == Minstrel
        assert Minstrel.advance(high_xp) == Bard

    def test_bard_champion_defeats_plus_one(self):
        """Bard's champion defeats all of one type plus one additional."""
        state = random.Random(4)
        world = droll.struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=2, skeleton=1),
            party=droll.struct.Party(champion=1),
            treasure=droll.struct.Treasure(),
            reserve=droll.struct.Treasure(),
        )
        result = droll.action.defeat_all_plus_additional(
            world, state.randrange, "champion", "goblin", "skeleton"
        )
        assert result.dungeon.goblin == 0
        assert result.dungeon.skeleton == 0
        assert result.party.champion == 0

    def test_bard_champion_no_additional_when_cleared(self):
        """Bard's champion needs no additional when monsters cleared."""
        state = random.Random(4)
        world = droll.struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=2),
            party=droll.struct.Party(champion=1),
            treasure=droll.struct.Treasure(),
            reserve=droll.struct.Treasure(),
        )
        result = droll.action.defeat_all_plus_additional(
            world, state.randrange, "champion", "goblin"
        )
        assert result.dungeon.goblin == 0

    def test_bard_champion_rejects_extra_additional(self):
        """Bard's champion rejects more than one additional target."""
        state = random.Random(4)
        world = droll.struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=1, skeleton=2),
            party=droll.struct.Party(champion=1),
            treasure=droll.struct.Treasure(),
            reserve=droll.struct.Treasure(),
        )
        with self.assertRaises(droll.error.DrollError):
            droll.action.defeat_all_plus_additional(
                world,
                state.randrange,
                "champion",
                "goblin",
                "skeleton",
                "skeleton",
            )

    def test_bard_champion_requires_additional_when_monsters_remain(self):
        """Bard's champion requires additional target when monsters remain."""
        state = random.Random(4)
        world = droll.struct.World(
            delve=1,
            depth=1,
            experience=0,
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=1, skeleton=1),
            party=droll.struct.Party(champion=1),
            treasure=droll.struct.Treasure(),
            reserve=droll.struct.Treasure(),
        )
        with self.assertRaises(droll.error.DrollError):
            droll.action.defeat_all_plus_additional(
                world,
                state.randrange,
                "champion",
                "goblin",
            )
