# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Mercenary/Commander hero abilities."""

import random
import unittest

import droll.error
import droll.struct
from droll.heroes.mercenary import (
    Commander,
    Mercenary,
    _commander_ability,
    _mercenary_ability,
    _mercenary_roll_party,
)

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


class TestMercenary(unittest.TestCase):

    def test_mercenary_roll_party_adds_bonus_scroll(self):
        """Mercenary roll adds one bonus scroll with regroup discard."""
        randrange = random.Random(4).randrange
        party, regroup = _mercenary_roll_party(7, randrange)
        self.assertEqual(sum(droll.struct.field_values(party)), 8)
        self.assertEqual(regroup.discard.scroll, 1)

    def test_mercenary_ability_defeats_two_monsters(self):
        """Mercenary ability defeats 2 different monsters."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=1, skeleton=1),
            party=droll.struct.Party(fighter=2),
        )
        result = _mercenary_ability(
            world, _UNUSED, "ability", "goblin", "skeleton"
        )
        self.assertEqual(result.dungeon.goblin, 0)
        self.assertEqual(result.dungeon.skeleton, 0)
        self.assertEqual(result.party.fighter, 2)
        self.assertFalse(result.ability)

    def test_mercenary_ability_defeats_one_when_only_one(self):
        """Mercenary ability defeats 1 monster when only 1 exists."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=1),
            party=droll.struct.Party(fighter=2),
        )
        result = _mercenary_ability(world, _UNUSED, "ability", "goblin")
        self.assertEqual(result.dungeon.goblin, 0)
        self.assertFalse(result.ability)

    def test_mercenary_ability_requires_target(self):
        """Mercenary ability requires at least one target."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=1),
            party=droll.struct.Party(fighter=2),
        )
        with self.assertRaises(droll.error.DrollError):
            _mercenary_ability(world, _UNUSED, "ability")

    def test_commander_ability_rerolls_dungeon_dice(self):
        """Commander ability rerolls dungeon dice."""
        randrange = random.Random(7).randrange
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=2, skeleton=1),
            party=droll.struct.Party(fighter=2),
        )
        result = _commander_ability(
            world, randrange, "ability", "goblin", "goblin"
        )
        self.assertFalse(result.ability)
        self.assertEqual(result.party.fighter, 2)

    def test_commander_ability_rerolls_dragon(self):
        """Commander ability can reroll dragon dice."""
        randrange = random.Random(7).randrange
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(dragon=3),
            party=droll.struct.Party(fighter=2),
        )
        result = _commander_ability(
            world, randrange, "ability", "dragon", "dragon", "dragon"
        )
        self.assertFalse(result.ability)

    def test_commander_ability_requires_target(self):
        """Commander ability requires at least one target."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=1),
            party=droll.struct.Party(fighter=2),
        )
        with self.assertRaises(droll.error.DrollError):
            _commander_ability(world, _UNUSED, "ability")

    def test_commander_fighter_defeats_goblin_plus_additional(self):
        """Commander fighters defeat all goblins plus one additional."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(goblin=2, skeleton=1),
            party=droll.struct.Party(fighter=2),
        )
        result = Commander.party.fighter.goblin(
            world, _UNUSED, "fighter", "goblin", "skeleton"
        )
        self.assertEqual(result.dungeon.goblin, 0)
        self.assertEqual(result.dungeon.skeleton, 0)
        self.assertEqual(result.party.fighter, 1)

    def test_commander_fighter_defeats_skeleton_plus_additional(self):
        """Commander fighters defeat one skeleton plus one additional."""
        world = droll.struct.World(
            ability=True,
            dungeon=droll.struct.Dungeon(skeleton=2, ooze=1),
            party=droll.struct.Party(fighter=2),
        )
        result = Commander.party.fighter.skeleton(
            world, _UNUSED, "fighter", "skeleton", "ooze"
        )
        self.assertEqual(result.dungeon.skeleton, 1)
        self.assertEqual(result.dungeon.ooze, 0)
        self.assertEqual(result.party.fighter, 1)

    def test_mercenary_advances_to_commander(self):
        """Mercenary advances to Commander at 5+ experience."""
        low_xp = droll.struct.World(experience=4)
        high_xp = droll.struct.World(experience=5)
        self.assertEqual(Mercenary.advance(low_xp), Mercenary)
        self.assertEqual(Mercenary.advance(high_xp), Commander)
        self.assertEqual(Commander.advance(high_xp), Commander)
