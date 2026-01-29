# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of basic world-to-world transitions."""

from dataclasses import replace
import random
import unittest

import droll.dice
import droll.error
import droll.struct
import droll.world


class TestWorld(unittest.TestCase):

    def setUp(self):
        self.state = random.Random(4)

    def test_game_initial(self):
        game = droll.world.new_world()
        assert 0 == game.experience
        assert 0 == sum(droll.struct.field_values(game.treasure))
        assert (6 * 3) + (4 * 3) + 6 == sum(
            droll.struct.field_values(game.reserve)
        )

    def test_delve_initial(self):
        game = droll.world.new_world()
        game = droll.world.delve(
            game, droll.dice.roll_party, self.state.randrange
        )
        assert 0 == game.depth
        assert game.ability is True
        assert 7 == sum(droll.struct.field_values(game.party))

    def test_dungeon_initial(self):
        game = droll.world.new_world()
        game = droll.world.delve(
            game, droll.dice.roll_party, self.state.randrange
        )
        game = droll.world.descend(
            game, droll.dice.roll_dungeon, self.state.randrange
        )
        assert 1 == game.depth
        assert 1 == sum(droll.struct.field_values(game.dungeon))

    def test_draw_treasure(self):
        pre = droll.world.new_world()
        post = droll.world.draw_treasure(pre, self.state.randrange)
        assert sum(droll.struct.field_values(pre.treasure)) == 0
        assert sum(droll.struct.field_values(post.treasure)) == 1
        assert (
            sum(droll.struct.field_values(pre.reserve))
            - sum(droll.struct.field_values(post.reserve))
            == 1
        )

    def test_replace_treasure(self):
        pre = droll.world.new_world()
        pre = replace(pre, treasure=replace(pre.treasure, elixir=1))
        post = droll.world.replace_treasure(pre, "elixir")
        assert sum(droll.struct.field_values(pre.treasure)) == 1
        assert sum(droll.struct.field_values(post.treasure)) == 0
        assert (
            sum(droll.struct.field_values(post.reserve))
            - sum(droll.struct.field_values(pre.reserve))
            == 1
        )

    def test_retire_simple(self):
        pre = droll.world.new_world()
        pre = droll.world.delve(
            pre, droll.dice.roll_party, self.state.randrange
        )
        pre = replace(
            pre,
            depth=3,
            dungeon=droll.struct.Dungeon(
                goblin=0, skeleton=0, ooze=0, chest=2, potion=5, dragon=0
            ),
        )
        assert pre.depth > 0
        post = droll.world.retire(pre)
        assert post.experience == pre.depth + pre.experience

    def test_retire_monsters(self):
        pre = droll.world.new_world()
        pre = droll.world.delve(
            pre, droll.dice.roll_party, self.state.randrange
        )
        pre = replace(
            pre,
            depth=3,
            dungeon=droll.struct.Dungeon(
                goblin=0, skeleton=1, ooze=0, chest=2, potion=5, dragon=0
            ),
        )
        assert pre.depth > 0

        # Neither town portal nor ring of invisibility
        with self.assertRaises(droll.error.DrollError):
            droll.world.retire(pre)

        # Ring of invisibility
        pre = replace(pre, treasure=replace(pre.treasure, ring=1))
        with self.assertRaises(droll.error.DrollError):
            droll.world.retire(pre)

        # Town portal
        pre = replace(pre, treasure=replace(pre.treasure, portal=1))
        post = droll.world.retire(pre)
        assert post.experience == pre.depth + pre.experience
        assert post.treasure.portal == 0

    def test_retire_dragon(self):
        pre = droll.world.new_world()
        pre = droll.world.delve(
            pre, droll.dice.roll_party, self.state.randrange
        )
        pre = replace(
            pre,
            depth=3,
            dungeon=droll.struct.Dungeon(
                goblin=0, skeleton=0, ooze=0, chest=2, potion=5, dragon=3
            ),
        )
        assert pre.depth > 0

        # Neither town portal nor ring of invisibility
        with self.assertRaises(droll.error.DrollError):
            droll.world.retire(pre)

        # Ring of invisibility
        pre = replace(pre, treasure=replace(pre.treasure, ring=1, portal=0))
        post1 = droll.world.retire(pre)
        assert post1.experience == pre.depth + pre.experience
        assert post1.treasure.ring == 0
        assert post1.treasure.portal == 0

        # Town portal
        pre = replace(pre, treasure=replace(pre.treasure, ring=0, portal=1))
        post2 = droll.world.retire(pre)
        assert post2.experience == pre.depth + pre.experience
        assert post2.treasure.ring == 0
        assert post2.treasure.portal == 0

        # Both should consume the ring of invisibility first
        pre = replace(pre, treasure=replace(pre.treasure, ring=1, portal=1))
        post3 = droll.world.retire(pre)
        assert post3.experience == pre.depth + pre.experience
        assert post3.treasure.ring == 0
        assert post3.treasure.portal == 1

    def test_next_dungeon_simple(self):
        pre = droll.world.new_world()
        pre = droll.world.delve(
            pre, droll.dice.roll_party, self.state.randrange
        )
        pre = replace(
            pre,
            depth=3,
            dungeon=droll.struct.Dungeon(
                goblin=0, skeleton=0, ooze=0, chest=2, potion=5, dragon=0
            ),
        )
        post = droll.world.descend(
            pre, droll.dice.roll_dungeon, self.state.randrange
        )
        assert post.depth == pre.depth + 1

    def test_next_dungeon_monsters(self):
        pre = droll.world.new_world()
        pre = droll.world.delve(
            pre, droll.dice.roll_party, self.state.randrange
        )
        pre = replace(
            pre,
            depth=3,
            dungeon=droll.struct.Dungeon(
                goblin=0, skeleton=1, ooze=0, chest=2, potion=5, dragon=1
            ),
        )
        assert pre.depth > 0

        # Neither town portal nor ring of invisibility
        with self.assertRaises(droll.error.DrollError):
            droll.world.descend(
                pre, droll.dice.roll_dungeon, self.state.randrange
            )

        # Ring of invisibility
        pre = replace(pre, treasure=replace(pre.treasure, ring=1, portal=0))
        with self.assertRaises(droll.error.DrollError):
            droll.world.descend(
                pre, droll.dice.roll_dungeon, self.state.randrange
            )

        # Town portal
        pre = replace(pre, treasure=replace(pre.treasure, ring=1, portal=0))
        with self.assertRaises(droll.error.DrollError):
            droll.world.descend(
                pre, droll.dice.roll_dungeon, self.state.randrange
            )

    def test_next_dungeon_dragon(self):
        pre = droll.world.new_world()
        pre = droll.world.delve(
            pre, droll.dice.roll_party, self.state.randrange
        )
        pre = replace(
            pre,
            depth=3,
            dungeon=droll.struct.Dungeon(
                goblin=0, skeleton=0, ooze=0, chest=2, potion=5, dragon=3
            ),
        )
        assert pre.depth > 0

        # Neither town portal nor ring of invisibility
        with self.assertRaises(droll.error.DrollError):
            droll.world.descend(
                pre, droll.dice.roll_dungeon, self.state.randrange
            )

        # Ring of invisibility
        pre = replace(pre, treasure=replace(pre.treasure, ring=1, portal=0))
        post1 = droll.world.descend(
            pre, droll.dice.roll_dungeon, self.state.randrange
        )
        assert post1.depth == pre.depth + 1
        assert post1.treasure.ring == 0
        assert post1.treasure.portal == 0

        # Town portal
        pre = replace(pre, treasure=replace(pre.treasure, ring=0, portal=1))
        with self.assertRaises(droll.error.DrollError):
            droll.world.descend(
                pre, droll.dice.roll_dungeon, self.state.randrange
            )

        # Both should consume the ring of invisibility
        pre = replace(pre, treasure=replace(pre.treasure, ring=1, portal=1))
        post3 = droll.world.descend(
            pre, droll.dice.roll_dungeon, self.state.randrange
        )
        assert post3.depth == pre.depth + 1
        assert post3.treasure.ring == 0
        assert post3.treasure.portal == 1

    def test_exhausted_dungeon(self):
        """Test exhausted_dungeon detects when no actions remain."""
        # None dungeon is exhausted
        assert droll.world.exhausted_dungeon(None)

        # Empty dungeon is exhausted
        assert droll.world.exhausted_dungeon(droll.struct.Dungeon())

        # Dungeon with only dragons (blocking) is not exhausted
        assert not droll.world.exhausted_dungeon(
            droll.struct.Dungeon(dragon=3)
        )

        # Dungeon with monsters is not exhausted
        assert not droll.world.exhausted_dungeon(
            droll.struct.Dungeon(goblin=1)
        )
        assert not droll.world.exhausted_dungeon(
            droll.struct.Dungeon(skeleton=2)
        )
        assert not droll.world.exhausted_dungeon(droll.struct.Dungeon(ooze=1))

        # Dungeon with chests/potions still has actions (not exhausted)
        assert not droll.world.exhausted_dungeon(
            droll.struct.Dungeon(chest=2, potion=3)
        )

    def test_retreat_valid(self):
        """Test valid retreat scenarios."""
        game = droll.world.new_world()
        game = droll.world.delve(
            game, droll.dice.roll_party, self.state.randrange
        )
        game = replace(game, depth=2, dungeon=droll.struct.Dungeon(goblin=1))
        result = droll.world.retreat(game)
        assert result.depth == 0
        assert result.dungeon is None

    def test_retreat_at_depth_one_with_monster(self):
        """Test retreat succeeds at depth 1 when a monster is present"""
        game = droll.world.new_world()
        game = droll.world.delve(
            game, droll.dice.roll_party, self.state.randrange
        )
        game = replace(game, depth=1, dungeon=droll.struct.Dungeon(goblin=1))
        result = droll.world.retreat(game)
        assert result.depth == 0
        assert result.dungeon is None

    def test_retreat_at_depth_one_without_monster(self):
        """Test retreat fails at depth 1 when no monster is present"""
        game = droll.world.new_world()
        game = droll.world.delve(
            game, droll.dice.roll_party, self.state.randrange
        )
        game = replace(game, depth=1)
        with self.assertRaises(droll.error.DrollError):
            droll.world.retreat(game)

    def test_retreat_without_descending(self):
        """Test retreat fails if not yet descended."""
        game = droll.world.new_world()
        game = droll.world.delve(
            game, droll.dice.roll_party, self.state.randrange
        )
        assert game.depth == 0

        with self.assertRaises(droll.error.DrollError):
            droll.world.retreat(game)

    def test_retreat_when_could_retire(self):
        """Test retreat fails when dungeon is defeated (should retire instead)."""
        game = droll.world.new_world()
        game = droll.world.delve(
            game, droll.dice.roll_party, self.state.randrange
        )
        game = replace(game, depth=2, dungeon=droll.struct.Dungeon())

        with self.assertRaises(droll.error.DrollError):
            droll.world.retreat(game)

    def test_max_dungeon_depth(self):
        """Test maximum dungeon depth limit is enforced."""
        game = droll.world.new_world()
        game = droll.world.delve(
            game, droll.dice.roll_party, self.state.randrange
        )
        game = replace(game, depth=10, dungeon=droll.struct.Dungeon())

        with self.assertRaises(droll.error.DrollError):
            droll.world.descend(
                game, droll.dice.roll_dungeon, self.state.randrange
            )

    def test_dungeon_dice_count(self):
        """Test that dungeon rolls use exactly 7 dice (minus dragons)."""
        game = droll.world.new_world()
        game = droll.world.delve(
            game, droll.dice.roll_party, self.state.randrange
        )
        game = droll.world.descend(
            game, droll.dice.roll_dungeon, self.state.randrange
        )
        # First dungeon at depth 1 should have exactly 1 die (min of depth and 7)
        assert sum(droll.struct.field_values(game.dungeon)) == 1

        # At depth 7+, should have 7 dice
        game2 = replace(game, depth=6, dungeon=droll.struct.Dungeon())
        game2 = droll.world.descend(
            game2, droll.dice.roll_dungeon, self.state.randrange
        )
        assert sum(droll.struct.field_values(game2.dungeon)) == 7

    def test_score(self):
        world = droll.struct.World(
            delve=3,
            depth=1,
            experience=15,
            ability=None,
            dungeon=None,
            party=None,
            treasure=droll.struct.Treasure(
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
        assert 20 == droll.world.score(world)
