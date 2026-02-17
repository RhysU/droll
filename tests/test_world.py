# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of basic world-to-world transitions."""

from dataclasses import replace
import random
import unittest

from droll import dice, error, struct, world


class TestWorld(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures with a seeded random number generator."""
        self.state = random.Random(4)

    def test_game_initial(self):
        """Test initial game state has correct experience, treasure, and reserve."""
        game = world.new_world()
        self.assertEqual(0, game.experience)
        self.assertEqual(0, sum(struct.field_values(game.treasure)))
        self.assertEqual(
            (6 * 3) + (4 * 3) + 6, sum(struct.field_values(game.reserve))
        )

    def test_delve_initial(self):
        """Test starting a new delve rolls party dice correctly."""
        game = world.new_world()
        game = world.delve(game, dice.roll_party, self.state.randrange)
        self.assertEqual(0, game.depth)
        self.assertTrue(game.ability is True)
        self.assertEqual(7, sum(struct.field_values(game.party)))

    def test_dungeon_initial(self):
        """Test descending into first dungeon level rolls dice correctly."""
        game = world.new_world()
        game = world.delve(game, dice.roll_party, self.state.randrange)
        game = world.descend(game, dice.roll_dungeon, self.state.randrange)
        self.assertEqual(1, game.depth)
        self.assertEqual(1, sum(struct.field_values(game.dungeon)))

    def test_draw_treasure(self):
        """Test drawing treasure moves one item from reserve to treasure."""
        pre = world.new_world()
        post = world.draw_treasure(pre, self.state.randrange)
        self.assertEqual(sum(struct.field_values(pre.treasure)), 0)
        self.assertEqual(sum(struct.field_values(post.treasure)), 1)
        self.assertEqual(
            sum(struct.field_values(pre.reserve))
            - sum(struct.field_values(post.reserve)),
            1,
        )

    def test_replace_treasure(self):
        """Test replacing treasure moves one item from treasure to reserve."""
        pre = world.new_world()
        pre = replace(pre, treasure=replace(pre.treasure, elixir=1))
        post = world.replace_treasure(pre, "elixir")
        self.assertEqual(sum(struct.field_values(pre.treasure)), 1)
        self.assertEqual(sum(struct.field_values(post.treasure)), 0)
        self.assertEqual(
            sum(struct.field_values(post.reserve))
            - sum(struct.field_values(pre.reserve)),
            1,
        )

    def test_retire_simple(self):
        """Test retiring from dungeon with no obstacles grants experience."""
        pre = world.new_world()
        pre = world.delve(pre, dice.roll_party, self.state.randrange)
        pre = replace(
            pre,
            depth=3,
            dungeon=struct.Dungeon(
                goblin=0, skeleton=0, ooze=0, chest=2, potion=5, dragon=0
            ),
        )
        self.assertGreater(pre.depth, 0)
        post = world.retire(pre)
        self.assertEqual(post.experience, pre.depth + pre.experience)

    def test_retire_monsters(self):
        """Test retiring with monsters requires portal, not ring."""
        pre = world.new_world()
        pre = world.delve(pre, dice.roll_party, self.state.randrange)
        pre = replace(
            pre,
            depth=3,
            dungeon=struct.Dungeon(
                goblin=0, skeleton=1, ooze=0, chest=2, potion=5, dragon=0
            ),
        )
        self.assertGreater(pre.depth, 0)

        # Neither town portal nor ring of invisibility
        with self.assertRaises(error.DrollError):
            world.retire(pre)

        # Ring of invisibility
        pre = replace(pre, treasure=replace(pre.treasure, ring=1))
        with self.assertRaises(error.DrollError):
            world.retire(pre)

        # Town portal
        pre = replace(pre, treasure=replace(pre.treasure, portal=1))
        post = world.retire(pre)
        self.assertEqual(post.experience, pre.depth + pre.experience)
        self.assertEqual(post.treasure.portal, 0)

    def test_retire_dragon(self):
        """Test retiring with dragons can use ring or portal, ring preferred."""
        pre = world.new_world()
        pre = world.delve(pre, dice.roll_party, self.state.randrange)
        pre = replace(
            pre,
            depth=3,
            dungeon=struct.Dungeon(
                goblin=0, skeleton=0, ooze=0, chest=2, potion=5, dragon=3
            ),
        )
        self.assertGreater(pre.depth, 0)

        # Neither town portal nor ring of invisibility
        with self.assertRaises(error.DrollError):
            world.retire(pre)

        # Ring of invisibility
        pre = replace(pre, treasure=replace(pre.treasure, ring=1, portal=0))
        post1 = world.retire(pre)
        self.assertEqual(post1.experience, pre.depth + pre.experience)
        self.assertEqual(post1.treasure.ring, 0)
        self.assertEqual(post1.treasure.portal, 0)

        # Town portal
        pre = replace(pre, treasure=replace(pre.treasure, ring=0, portal=1))
        post2 = world.retire(pre)
        self.assertEqual(post2.experience, pre.depth + pre.experience)
        self.assertEqual(post2.treasure.ring, 0)
        self.assertEqual(post2.treasure.portal, 0)

        # Both should consume the ring of invisibility first
        pre = replace(pre, treasure=replace(pre.treasure, ring=1, portal=1))
        post3 = world.retire(pre)
        self.assertEqual(post3.experience, pre.depth + pre.experience)
        self.assertEqual(post3.treasure.ring, 0)
        self.assertEqual(post3.treasure.portal, 1)

    def test_descend_simple(self):
        """Test descending to next level with no obstacles increments depth."""
        pre = world.new_world()
        pre = world.delve(pre, dice.roll_party, self.state.randrange)
        pre = replace(
            pre,
            depth=3,
            dungeon=struct.Dungeon(
                goblin=0, skeleton=0, ooze=0, chest=2, potion=5, dragon=0
            ),
        )
        post = world.descend(pre, dice.roll_dungeon, self.state.randrange)
        self.assertEqual(post.depth, pre.depth + 1)

    def test_descend_monsters(self):
        """Test descending with monsters or dragons blocks without appropriate treasure."""
        pre = world.new_world()
        pre = world.delve(pre, dice.roll_party, self.state.randrange)
        pre = replace(
            pre,
            depth=3,
            dungeon=struct.Dungeon(
                goblin=0, skeleton=1, ooze=0, chest=2, potion=5, dragon=1
            ),
        )
        self.assertGreater(pre.depth, 0)

        # Neither town portal nor ring of invisibility
        with self.assertRaises(error.DrollError):
            world.descend(pre, dice.roll_dungeon, self.state.randrange)

        # Ring of invisibility
        pre = replace(pre, treasure=replace(pre.treasure, ring=1, portal=0))
        with self.assertRaises(error.DrollError):
            world.descend(pre, dice.roll_dungeon, self.state.randrange)

        # Town portal
        pre = replace(pre, treasure=replace(pre.treasure, ring=1, portal=0))
        with self.assertRaises(error.DrollError):
            world.descend(pre, dice.roll_dungeon, self.state.randrange)

    def test_descend_dragon(self):
        """Test descending with dragons requires ring, portal doesn't work."""
        pre = world.new_world()
        pre = world.delve(pre, dice.roll_party, self.state.randrange)
        pre = replace(
            pre,
            depth=3,
            dungeon=struct.Dungeon(
                goblin=0, skeleton=0, ooze=0, chest=2, potion=5, dragon=3
            ),
        )
        self.assertGreater(pre.depth, 0)

        # Neither town portal nor ring of invisibility
        with self.assertRaises(error.DrollError):
            world.descend(pre, dice.roll_dungeon, self.state.randrange)

        # Ring of invisibility
        pre = replace(pre, treasure=replace(pre.treasure, ring=1, portal=0))
        post1 = world.descend(pre, dice.roll_dungeon, self.state.randrange)
        self.assertEqual(post1.depth, pre.depth + 1)
        self.assertEqual(post1.treasure.ring, 0)
        self.assertEqual(post1.treasure.portal, 0)

        # Town portal
        pre = replace(pre, treasure=replace(pre.treasure, ring=0, portal=1))
        with self.assertRaises(error.DrollError):
            world.descend(pre, dice.roll_dungeon, self.state.randrange)

        # Both should consume the ring of invisibility
        pre = replace(pre, treasure=replace(pre.treasure, ring=1, portal=1))
        post3 = world.descend(pre, dice.roll_dungeon, self.state.randrange)
        self.assertEqual(post3.depth, pre.depth + 1)
        self.assertEqual(post3.treasure.ring, 0)
        self.assertEqual(post3.treasure.portal, 1)

    def test_regroup_discard(self):
        """Temporary party dice must be discarded during next regroup phase."""
        # Largely the same test case for descending, retiring, and retreating
        pre1 = world.new_world()
        pre1 = world.delve(pre1, dice.roll_party, self.state.randrange)
        pre1 = replace(
            pre1,
            depth=3,
            party=struct.Party(
                fighter=5, cleric=4, mage=3, thief=2, champion=1, scroll=0
            ),
            regroup=struct.Regroup(
                discard=struct.Party(
                    fighter=0, cleric=5, mage=3, thief=1, champion=0, scroll=0
                )
            ),
        )

        # First, confirm descending works as expected
        descended = world.descend(
            pre1, dice.roll_dungeon, self.state.randrange
        )
        self.assertEqual(
            descended.party,
            struct.Party(
                fighter=5, cleric=0, mage=0, thief=1, champion=1, scroll=0
            ),
        )
        self.assertEqual(
            descended.regroup.discard,
            struct.Party(
                fighter=0, cleric=0, mage=0, thief=0, champion=0, scroll=0
            ),
        )

        # Second, confirm retiring works as expected
        retired = world.retire(pre1)
        self.assertEqual(
            retired.party,
            struct.Party(
                fighter=5, cleric=0, mage=0, thief=1, champion=1, scroll=0
            ),
        )
        self.assertEqual(
            retired.regroup.discard,
            struct.Party(
                fighter=0, cleric=0, mage=0, thief=0, champion=0, scroll=0
            ),
        )

        # Third, confirm retreating works as expected
        pre2 = replace(
            pre1, dungeon=struct.Dungeon(goblin=1)  # Threat required!
        )
        retreated = world.retreat(pre2)
        self.assertEqual(
            retreated.party,
            struct.Party(
                fighter=5, cleric=0, mage=0, thief=1, champion=1, scroll=0
            ),
        )
        self.assertEqual(
            retreated.regroup.discard,
            struct.Party(
                fighter=0, cleric=0, mage=0, thief=0, champion=0, scroll=0
            ),
        )

    def test_exhausted_dungeon(self):
        """Test exhausted_dungeon detects when no actions remain."""
        # None dungeon is exhausted
        self.assertTrue(world.exhausted_dungeon(None))

        # Empty dungeon is exhausted
        self.assertTrue(world.exhausted_dungeon(struct.Dungeon()))

        # Dungeon with only dragons (blocking) is not exhausted
        self.assertFalse(world.exhausted_dungeon(struct.Dungeon(dragon=3)))

        # Dungeon with monsters is not exhausted
        self.assertFalse(world.exhausted_dungeon(struct.Dungeon(goblin=1)))
        self.assertFalse(world.exhausted_dungeon(struct.Dungeon(skeleton=2)))
        self.assertFalse(world.exhausted_dungeon(struct.Dungeon(ooze=1)))

        # Dungeon with chests/potions still has actions (not exhausted)
        self.assertFalse(
            world.exhausted_dungeon(struct.Dungeon(chest=2, potion=3))
        )

    def test_retreat_valid(self):
        """Test valid retreat scenarios."""
        game = world.new_world()
        game = world.delve(game, dice.roll_party, self.state.randrange)
        game = replace(game, depth=2, dungeon=struct.Dungeon(goblin=1))
        result = world.retreat(game)
        self.assertEqual(result.depth, 0)
        self.assertIsNone(result.dungeon)

    def test_retreat_at_depth_one_with_monster(self):
        """Test retreat succeeds at depth 1 when a monster is present"""
        game = world.new_world()
        game = world.delve(game, dice.roll_party, self.state.randrange)
        game = replace(game, depth=1, dungeon=struct.Dungeon(goblin=1))
        result = world.retreat(game)
        self.assertEqual(result.depth, 0)
        self.assertIsNone(result.dungeon)

    def test_retreat_at_depth_one_without_monster(self):
        """Test retreat fails at depth 1 when no monster is present"""
        game = world.new_world()
        game = world.delve(game, dice.roll_party, self.state.randrange)
        game = replace(game, depth=1)
        with self.assertRaises(error.DrollError):
            world.retreat(game)

    def test_retreat_without_descending(self):
        """Test retreat fails if not yet descended."""
        game = world.new_world()
        game = world.delve(game, dice.roll_party, self.state.randrange)
        self.assertEqual(game.depth, 0)

        with self.assertRaises(error.DrollError):
            world.retreat(game)

    def test_retreat_when_could_retire(self):
        """Test retreat fails when dungeon is defeated (should retire instead)."""
        game = world.new_world()
        game = world.delve(game, dice.roll_party, self.state.randrange)
        game = replace(game, depth=2, dungeon=struct.Dungeon())

        with self.assertRaises(error.DrollError):
            world.retreat(game)

    def test_max_dungeon_depth(self):
        """Test maximum dungeon depth limit is enforced."""
        game = world.new_world()
        game = world.delve(game, dice.roll_party, self.state.randrange)
        game = replace(game, depth=10, dungeon=struct.Dungeon())

        with self.assertRaises(error.DrollError):
            world.descend(game, dice.roll_dungeon, self.state.randrange)

    def test_dungeon_dice_count(self):
        """Test that dungeon rolls use exactly 7 dice (minus dragons)."""
        game = world.new_world()
        game = world.delve(game, dice.roll_party, self.state.randrange)
        game = world.descend(game, dice.roll_dungeon, self.state.randrange)
        # First dungeon at depth 1 should have exactly 1 die (min of depth and 7)
        self.assertEqual(sum(struct.field_values(game.dungeon)), 1)

        # At depth 7+, should have 7 dice
        game2 = replace(game, depth=6, dungeon=struct.Dungeon())
        game2 = world.descend(game2, dice.roll_dungeon, self.state.randrange)
        self.assertEqual(sum(struct.field_values(game2.dungeon)), 7)

    def test_delve_maximum(self):
        """Test that a fourth delve is rejected after three."""
        game = world.new_world()
        game = world.delve(game, dice.roll_party, self.state.randrange)
        game = world.delve(game, dice.roll_party, self.state.randrange)
        game = world.delve(game, dice.roll_party, self.state.randrange)
        self.assertEqual(game.delve, 3)
        with self.assertRaises(error.DrollError):
            world.delve(game, dice.roll_party, self.state.randrange)

    def test_score(self):
        """Test score calculation includes experience and treasure bonuses."""
        game = struct.World(
            delve=3,
            depth=1,
            experience=15,
            ability=None,
            dungeon=None,
            party=None,
            treasure=struct.Treasure(
                sword=0,
                talisman=0,
                sceptre=0,
                tools=0,
                scroll=0,
                elixir=0,
                bait=1,
                portal=0,
                ring=0,
                scale=2,
            ),
            reserve=None,
        )
        self.assertEqual(20, world.score(game))
