# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of Game (at least driving with basic commands)."""

from dataclasses import replace
import random
import unittest

from droll import action, dice, struct, world
from droll.error import DrollError
from droll.game import Game, GameState
from droll.player import Default


class TestGame(unittest.TestCase):

    def test_game_construction(self):
        """Game can be constructed with various parameter combinations."""
        Game()
        Game(player=Default)
        Game(random=random.Random(4))

    def test_gamestate_truthiness(self):
        """GameState values coerce to boolean correctly for control flow."""
        self.assertTrue(GameState.STOP, "STOP must coerce to True.")
        self.assertFalse(GameState.PLAY, "PLAY must coerce to False.")

    def test_reroll_dungeon_dice(self):
        """Test rerolling dungeon dice using a scroll."""
        g = Game(random=random.Random(4), player=Default)
        g.descend()  # Start delve
        # Set up dungeon with goblin and party with scroll
        g._world = replace(
            g._world,
            depth=1,
            party=replace(g._world.party, scroll=1),
            dungeon=struct.Dungeon(goblin=2),
        )
        pre_scroll = g._world.party.scroll
        g.reroll("goblin")
        # Scroll consumed, dungeon rerolled
        self.assertEqual(g._world.party.scroll, pre_scroll - 1)

    def test_reroll_portion(self):
        """Test rerolling potion using a scroll."""
        g = Game(random=random.Random(4), player=Default)
        g.descend()  # Start delve
        # Set up dungeon with goblin and party with scroll
        g._world = replace(
            g._world,
            depth=1,
            party=replace(g._world.party, scroll=1),
            dungeon=struct.Dungeon(potion=2),
        )
        pre_scroll = g._world.party.scroll
        g.reroll("potion")
        # Scroll consumed, dungeon rerolled
        self.assertEqual(g._world.party.scroll, pre_scroll - 1)

    def test_reroll_multiple_targets(self):
        """Test rerolling multiple dungeon dice."""
        g = Game(random=random.Random(4), player=Default)
        g.descend()
        g._world = replace(
            g._world,
            depth=1,
            party=replace(g._world.party, scroll=1),
            dungeon=struct.Dungeon(goblin=1, skeleton=1),
        )
        g.reroll("goblin", "skeleton")
        self.assertEqual(g._world.party.scroll, 0)

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

    def test_retreat(self):
        """Game.retreat() retreats from dungeon and starts next delve."""
        g = Game(random=random.Random(4), player=Default)
        g.descend()
        # Place a monster so retreat is valid (can't retreat from cleared dungeon)
        g._world = replace(
            g._world, dungeon=struct.Dungeon(goblin=1)
        )
        result = g.retreat()
        self.assertEqual(result, GameState.PLAY)
        # After retreat, a new delve should have started
        self.assertEqual(g._world.depth, 0)
        self.assertIsNotNone(g._world.party)

    def test_next_delve_returns_stop_after_three(self):
        """Game returns STOP when no more delves remain."""
        g = Game(random=random.Random(4), player=Default)
        # Play through 3 delves by retiring from each
        for _ in range(2):
            g.descend()
            g._world = replace(g._world, dungeon=struct.Dungeon())
            result = g.retire()
            self.assertEqual(result, GameState.PLAY)
        # Third delve: retire should trigger STOP
        g.descend()
        g._world = replace(g._world, dungeon=struct.Dungeon())
        result = g.retire()
        self.assertEqual(result, GameState.STOP)


class TestRerollParty(unittest.TestCase):
    """Tests for action.reroll supporting party dice (issue #82)."""

    def setUp(self):
        """Fixture with a world containing known dungeon and party dice."""
        self.world = replace(
            world.new_world(),
            dungeon=struct.Dungeon(goblin=2, skeleton=1),
            party=struct.Party(fighter=2, cleric=1, scroll=2),
        )

    def _canned_randrange(self, sequence):
        """Return a randrange function that yields predetermined values."""
        seq = list(sequence)

        def randrange(start, stop):
            return start + seq.pop(0)

        return randrange

    def test_reroll_single_party_die(self):
        """Rerolling a single party die removes it and re-rolls one party die."""
        # Roll value 0 => fighter
        randrange = self._canned_randrange([0])
        result = action.reroll(
            self.world, randrange, "scroll", "fighter"
        )
        # One scroll consumed for the hero cost
        self.assertEqual(result.party.scroll, 1)
        # Fighter was removed (2-1=1) then re-rolled as fighter (+1=2)
        self.assertEqual(result.party.fighter, 2)
        # Dungeon unchanged
        self.assertEqual(result.dungeon, self.world.dungeon)

    def test_reroll_multiple_party_dice(self):
        """Rerolling multiple party dice removes and re-rolls each."""
        # Roll values: 0 => fighter, 1 => cleric
        randrange = self._canned_randrange([0, 1])
        result = action.reroll(
            self.world, randrange, "scroll", "fighter", "cleric"
        )
        # One scroll consumed
        self.assertEqual(result.party.scroll, 1)
        # fighter: 2 - 1 + 1(rolled) = 2; cleric: 1 - 1 + 1(rolled) = 1
        self.assertEqual(result.party.fighter, 2)
        self.assertEqual(result.party.cleric, 1)
        # Dungeon unchanged
        self.assertEqual(result.dungeon, self.world.dungeon)

    def test_reroll_mix_dungeon_and_party(self):
        """Rerolling a mix of dungeon and party dice handles both."""
        # Dungeon roll: value 0 => goblin; Party roll: value 2 => mage
        randrange = self._canned_randrange([0, 2])
        result = action.reroll(
            self.world, randrange, "scroll", "goblin", "fighter"
        )
        # One scroll consumed
        self.assertEqual(result.party.scroll, 1)
        # Dungeon: goblin was 2, removed 1, re-rolled as goblin (+1) => 2
        self.assertEqual(result.dungeon.goblin, 2)
        # Party: fighter was 2, removed 1, re-rolled as mage (+1)
        self.assertEqual(result.party.fighter, 1)
        self.assertEqual(result.party.mage, 1)

    def test_reroll_party_die_not_present_raises(self):
        """Rerolling a party die that is not present raises DrollError."""
        randrange = self._canned_randrange([])
        with self.assertRaises(DrollError):
            action.reroll(
                self.world, randrange, "scroll", "mage"
            )

    def test_reroll_unknown_target_raises(self):
        """Rerolling a target that is neither dungeon nor party raises DrollError."""
        randrange = self._canned_randrange([])
        with self.assertRaises(DrollError):
            action.reroll(
                self.world, randrange, "scroll", "nonexistent"
            )
