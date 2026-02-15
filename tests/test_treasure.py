# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of world-to-world transitions stemming from using treasure."""

from dataclasses import fields, replace
import random
import unittest

import droll.error as error
import droll.player as player
import droll.struct as struct
import droll.world as world


class TestTreasure(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures with a game containing dungeon items but no party."""
        self.game = replace(
            world.new_world(),
            dungeon=struct.Dungeon(*([2] * len(fields(struct.Dungeon)))),
            party=struct.Party(),
        )
        self.randrange = random.Random(4).randrange

    def test_elixir(self):
        """Test elixir treasure used to revive a party member."""
        game = replace(
            self.game, treasure=replace(self.game.treasure, elixir=1)
        )
        game = player.apply(
            player.Default, game, self.randrange, "elixir", "cleric"
        )
        self.assertEqual(game.party.cleric, 1)
        self.assertEqual(game.treasure.elixir, 0)

        with self.assertRaises(error.DrollError):
            player.apply(
                player.Default, game, self.randrange, "elixir", "mage"
            )

    def test_bait(self):
        """Test bait treasure used to convert monsters to dragons."""
        game = replace(self.game, treasure=replace(self.game.treasure, bait=2))
        game = player.apply(
            player.Default, game, self.randrange, "bait", "dragon"
        )
        self.assertEqual(game.treasure.bait, 1)
        self.assertEqual(game.dungeon.goblin, 0)
        self.assertEqual(game.dungeon.skeleton, 0)
        self.assertEqual(game.dungeon.ooze, 0)
        self.assertEqual(game.dungeon.dragon, 8)

        with self.assertRaises(error.DrollError):
            player.apply(player.Default, game, self.randrange, "bait")

    def _helper_sword(self, identifier):
        """Test sword when referred to via identifier (e.g. 'sword', 'fighter')."""
        game = replace(
            self.game, treasure=replace(self.game.treasure, sword=2)
        )
        game = player.apply(player.Default, game, None, identifier, "goblin")
        self.assertEqual(game.treasure.sword, 1)
        self.assertEqual(game.party.fighter, 0)
        self.assertEqual(game.dungeon.goblin, 0)

        game = player.apply(player.Default, game, None, identifier, "ooze")
        self.assertEqual(game.treasure.sword, 0)
        self.assertEqual(game.party.fighter, 0)
        self.assertEqual(game.dungeon.ooze, 1)

        with self.assertRaises(error.DrollError):
            player.apply(player.Default, game, None, identifier, "ooze")

    def test_sword_via_fighter(self):
        """Test sword treasure referred to as 'fighter'."""
        self._helper_sword("fighter")

    def test_sword_via_itself(self):
        """Test sword treasure referred to as 'sword'."""
        self._helper_sword("sword")
