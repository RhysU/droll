# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of world-to-world transitions stemming from attacking dragons."""

from dataclasses import fields, replace
import random
import unittest

from droll import error, heroes, player, struct, world


class TestDragon(unittest.TestCase):

    def setUp(self):
        """Set up fixture for a game containing dragons and party members."""
        self.game = replace(
            world.new_world(),
            dungeon=struct.Dungeon(
                goblin=0, skeleton=0, ooze=0, chest=1, potion=2, dragon=3
            ),
            party=struct.Party(*([2] * len(fields(struct.Party)))),
        )
        self.randrange = random.Random(4).randrange

    def test_successful(self):
        """Test successfully defeating a dragon with three distinct heroes."""
        game = player.apply(
            player.Default,
            self.game,
            self.randrange,
            "fighter",
            "dragon",
            "cleric",
            "mage",
        )
        self.assertEqual(game.party.fighter, 1)
        self.assertEqual(game.party.cleric, 1)
        self.assertEqual(game.party.mage, 1)
        self.assertEqual(game.dungeon.dragon, 0)
        self.assertEqual(game.experience, 1)
        self.assertEqual(sum(struct.field_values(game.treasure)), 1)

    def test_treasure_slot1(self):
        """Sword treasure can substitute for fighter in dragon combat."""
        game = replace(
            self.game, treasure=replace(self.game.treasure, sword=7)
        )
        game = replace(game, party=replace(game.party, fighter=0))
        game = player.apply(
            player.Default,
            game,
            self.randrange,  # Notice sword!
            "fighter",
            "dragon",
            "cleric",
            "mage",
        )
        self.assertEqual(game.treasure.sword, 6)
        self.assertEqual(game.party.fighter, 0)
        self.assertEqual(game.party.cleric, 1)
        self.assertEqual(game.party.mage, 1)
        self.assertEqual(game.dungeon.dragon, 0)
        self.assertEqual(game.experience, 1)
        self.assertEqual(sum(struct.field_values(game.treasure)), 7)

    def test_monsters_remain(self):
        """Dragon cannot be attacked while monsters remain in dungeon."""
        game = replace(self.game, dungeon=replace(self.game.dungeon, goblin=1))
        with self.assertRaises(error.DrollError):
            player.apply(
                player.Default,
                game,
                self.randrange,
                "fighter",
                "dragon",
                "cleric",
                "mage",
            )

    def test_too_few_specified(self):
        """Attacking dragon with too few heroes raises an error."""
        with self.assertRaises(error.DrollError):
            player.apply(
                player.Default,
                self.game,
                self.randrange,
                "fighter",
                "dragon",
                "cleric",
            )

        with self.assertRaises(error.DrollError):
            player.apply(
                player.Default, self.game, self.randrange, "fighter", "dragon"
            )

        # Dragon Slayer requires only two
        with self.assertRaises(error.DrollError):
            player.apply(
                heroes.DragonSlayer,
                self.game,
                self.randrange,
                "fighter",
                "dragon",
            )

    def test_only_heroes_accepted(self):
        """Only valid heroes can be used against dragons."""
        with self.assertRaises(error.DrollError):
            player.apply(
                player.Default,
                self.game,
                self.randrange,
                "fighter",
                "dragon",
                "cleric",
                "foo",
            )

    def test_one_scroll(self):
        """A single scroll cannot be used as a hero substitute."""
        with self.assertRaises(error.DrollError):
            player.apply(
                player.Default,
                self.game,
                self.randrange,
                "fighter",
                "dragon",
                "cleric",
                "scroll",
            )

        # Dragon Slayer requires only two
        with self.assertRaises(error.DrollError):
            player.apply(
                heroes.DragonSlayer,
                self.game,
                self.randrange,
                "fighter",
                "dragon",
                "scroll",
            )

    def test_not_enough_distinct(self):
        """Duplicate heroes cannot defeat a dragon."""
        with self.assertRaises(error.DrollError):
            player.apply(
                player.Default,
                self.game,
                self.randrange,
                "fighter",
                "dragon",
                "mage",
                "mage",
            )
