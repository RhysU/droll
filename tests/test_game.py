# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of Game (at least driving with basic commands)."""

import random
from dataclasses import replace
import unittest

from droll.error import DrollError
from droll.game import Game, GameState
from droll.player import Default
import droll.struct


class TestGame(unittest.TestCase):

    def test_game_construction(self):
        Game()
        Game(player=Default)
        Game(random=random.Random(4))

    def test_gamestate_truthiness(self):
        assert GameState.STOP, "STOP must coerce to True."
        assert not GameState.PLAY, "PLAY must coerce to False."

    def test_reroll_dungeon_dice(self):
        """Test rerolling dungeon dice using a scroll."""
        g = Game(random=random.Random(4), player=Default)
        g.descend()  # Start delve
        # Set up dungeon with goblin and party with scroll
        g._world = replace(
            g._world,
            depth=1,
            party=replace(g._world.party, scroll=1),
            dungeon=droll.struct.Dungeon(goblin=2),
        )
        pre_scroll = g._world.party.scroll
        g.reroll("goblin")
        # Scroll consumed, dungeon rerolled
        assert g._world.party.scroll == pre_scroll - 1

    def test_reroll_portion(self):
        """Test rerolling potion using a scroll."""
        g = Game(random=random.Random(4), player=Default)
        g.descend()  # Start delve
        # Set up dungeon with goblin and party with scroll
        g._world = replace(
            g._world,
            depth=1,
            party=replace(g._world.party, scroll=1),
            dungeon=droll.struct.Dungeon(potion=2),
        )
        pre_scroll = g._world.party.scroll
        g.reroll("potion")
        # Scroll consumed, dungeon rerolled
        assert g._world.party.scroll == pre_scroll - 1

    def test_reroll_multiple_targets(self):
        """Test rerolling multiple dungeon dice."""
        g = Game(random=random.Random(4), player=Default)
        g.descend()
        g._world = replace(
            g._world,
            depth=1,
            party=replace(g._world.party, scroll=1),
            dungeon=droll.struct.Dungeon(goblin=1, skeleton=1),
        )
        g.reroll("goblin", "skeleton")
        assert g._world.party.scroll == 0

    def test_apply_portal_directly_fails(self):
        """Test that using portal directly gives helpful error."""
        g = Game(random=random.Random(4), player=Default)
        g.descend()
        g._world = replace(
            g._world,
            treasure=replace(g._world.treasure, portal=1),
        )
        with self.assertRaises(DrollError):
            g.apply("portal")

    def test_apply_ring_directly_fails(self):
        """Test that using ring directly gives helpful error."""
        g = Game(random=random.Random(4), player=Default)
        g.descend()
        g._world = replace(
            g._world,
            treasure=replace(g._world.treasure, ring=1),
        )
        with self.assertRaises(DrollError):
            g.apply("ring")
