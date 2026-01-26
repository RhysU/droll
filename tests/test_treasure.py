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
        self.game = replace(
            world.new_world(),
            dungeon=struct.Dungeon(*([2] * len(fields(struct.Dungeon)))),
            party=struct.Party(),
        )
        self.randrange = random.Random(4).randrange

    def test_elixir(self):
        game = replace(
            self.game, treasure=replace(self.game.treasure, elixir=1)
        )
        game = player.apply(player.Default, game, self.randrange, "elixir", "cleric")
        assert game.party.cleric == 1
        assert game.treasure.elixir == 0

        with self.assertRaises(error.DrollError):
            player.apply(player.Default, game, self.randrange, "elixir", "mage")

    def test_bait(self):
        game = replace(
            self.game, treasure=replace(self.game.treasure, bait=2)
        )
        game = player.apply(player.Default, game, self.randrange, "bait", "dragon")
        assert game.treasure.bait == 1
        assert game.dungeon.goblin == 0
        assert game.dungeon.skeleton == 0
        assert game.dungeon.ooze == 0
        assert game.dungeon.dragon == 8

        with self.assertRaises(error.DrollError):
            player.apply(player.Default, game, self.randrange, "bait")

    def _helper_sword(self, identifier):
        """Test sword when referred to via identifier (e.g. 'sword', 'fighter')."""
        game = replace(
            self.game, treasure=replace(self.game.treasure, sword=2)
        )
        game = player.apply(player.Default, game, None, identifier, "goblin")
        assert game.treasure.sword == 1
        assert game.party.fighter == 0
        assert game.dungeon.goblin == 0

        game = player.apply(player.Default, game, None, identifier, "ooze")
        assert game.treasure.sword == 0
        assert game.party.fighter == 0
        assert game.dungeon.ooze == 1

        with self.assertRaises(error.DrollError):
            player.apply(player.Default, game, None, identifier, "ooze")

    def test_sword_via_fighter(self):
        self._helper_sword("fighter")

    def test_sword_via_itself(self):
        self._helper_sword("sword")
