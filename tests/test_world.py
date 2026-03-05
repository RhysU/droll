# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of basic world-to-world transitions."""

from dataclasses import replace
import random
import pytest

from droll import dice, dungeon, struct, treasure, world
from droll.struct import Artifact, Dungeon, Party, make_dungeon, make_party, make_artifacts


def _roll_all_goblins(n, _randrange):
    """Deterministic roll where every die lands on goblin."""
    return make_dungeon(goblin=n)


class TestWorld:

    def setup_method(self):
        """Set up test fixtures with a seeded random number generator."""
        self.state = random.Random(4)

    def test_delve_initial(self):
        """Test starting a new delve rolls party dice correctly."""
        game = world.new_world()
        game = world.delve(game, dice.roll_party, self.state.randrange)
        assert game.depth == 0
        assert game.ability is True
        assert sum(game.party.values()) == 7

    def test_dungeon_initial(self):
        """Test descending into first dungeon level rolls dice correctly."""
        game = world.new_world()
        game = world.delve(game, dice.roll_party, self.state.randrange)
        game = world.descend(game, dice.roll_dungeon, self.state.randrange)
        assert game.depth == 1
        assert sum(game.dungeon.values()) == 1

    def test_draw_treasure(self):
        """Test drawing treasure moves one item from box to own."""
        pre = world.new_world()
        post_treasure = treasure.draw_treasure(
            pre.treasure, self.state.randrange
        )
        post = replace(pre, treasure=post_treasure)
        assert sum(pre.treasure.own.values()) == 0
        assert sum(post.treasure.own.values()) == 1
        assert (
            sum(pre.treasure.box.values())
            - sum(post.treasure.box.values())
            == 1
        )

    def test_draw_treasure_empty_box(self):
        """Test drawing from an empty box raises DrollError."""
        pre = world.new_world()
        pre = replace(
            pre,
            treasure=replace(pre.treasure, box=struct.empty_artifact_counts()),
        )
        with pytest.raises(struct.DrollError):
            treasure.draw_treasure(pre.treasure, self.state.randrange)

    def test_replace_treasure(self):
        """Test replacing treasure moves one item from own to box."""
        pre = world.new_world()
        pre = replace(
            pre,
            treasure=replace(
                pre.treasure, own=make_artifacts(elixir=1)
            ),
        )
        post_treasure = treasure.replace_treasure(pre.treasure, Artifact.ELIXIR)
        post = replace(pre, treasure=post_treasure)
        assert sum(pre.treasure.own.values()) == 1
        assert sum(post.treasure.own.values()) == 0
        assert (
            sum(post.treasure.box.values())
            - sum(pre.treasure.box.values())
            == 1
        )

    def test_retire_simple(self):
        """Test retiring from dungeon with no obstacles grants experience."""
        pre = world.new_world()
        pre = world.delve(pre, dice.roll_party, self.state.randrange)
        pre = replace(
            pre,
            depth=3,
            dungeon=make_dungeon(chest=2, potion=5),
        )
        assert pre.depth > 0
        post = world.retire(pre)
        assert post.experience == pre.depth + pre.experience

    def test_retire_monsters(self):
        """Test retiring with monsters requires portal, not ring."""
        pre = world.new_world()
        pre = world.delve(pre, dice.roll_party, self.state.randrange)
        pre = replace(
            pre,
            depth=3,
            dungeon=make_dungeon(skeleton=1, chest=2, potion=5),
        )
        assert pre.depth > 0

        # Neither town portal nor ring of invisibility
        with pytest.raises(struct.DrollError):
            world.retire(pre)

        # Ring of invisibility
        pre = replace(
            pre,
            treasure=replace(
                pre.treasure, own=make_artifacts(ring=1)
            ),
        )
        with pytest.raises(struct.DrollError):
            world.retire(pre)

        # Town portal
        pre = replace(
            pre,
            treasure=replace(
                pre.treasure, own=make_artifacts(portal=1)
            ),
        )
        post = world.retire(pre)
        assert post.experience == pre.depth + pre.experience
        assert post.treasure.own[Artifact.PORTAL] == 0

    def test_retire_dragon(self):
        """Test retiring with dragons uses ring or portal."""
        pre = world.new_world()
        pre = world.delve(pre, dice.roll_party, self.state.randrange)
        pre = replace(
            pre,
            depth=3,
            dungeon=make_dungeon(chest=2, potion=5, dragon=3),
        )
        assert pre.depth > 0

        # Neither town portal nor ring of invisibility
        with pytest.raises(struct.DrollError):
            world.retire(pre)

        # Ring of invisibility
        pre = replace(
            pre,
            treasure=replace(
                pre.treasure, own=make_artifacts(ring=1)
            ),
        )
        post1 = world.retire(pre)
        assert post1.experience == pre.depth + pre.experience
        assert post1.treasure.own[Artifact.RING] == 0
        assert post1.treasure.own[Artifact.PORTAL] == 0

        # Town portal
        pre = replace(
            pre,
            treasure=replace(
                pre.treasure, own=make_artifacts(portal=1)
            ),
        )
        post2 = world.retire(pre)
        assert post2.experience == pre.depth + pre.experience
        assert post2.treasure.own[Artifact.RING] == 0
        assert post2.treasure.own[Artifact.PORTAL] == 0

        # Both should consume the ring of invisibility first
        pre = replace(
            pre,
            treasure=replace(
                pre.treasure, own=make_artifacts(ring=1, portal=1)
            ),
        )
        post3 = world.retire(pre)
        assert post3.experience == pre.depth + pre.experience
        assert post3.treasure.own[Artifact.RING] == 0
        assert post3.treasure.own[Artifact.PORTAL] == 1

    def test_descend_simple(self):
        """Test descending to next level with no obstacles increments depth."""
        pre = world.new_world()
        pre = world.delve(pre, dice.roll_party, self.state.randrange)
        pre = replace(
            pre,
            depth=3,
            dungeon=make_dungeon(chest=2, potion=5),
        )
        post = world.descend(pre, dice.roll_dungeon, self.state.randrange)
        assert post.depth == pre.depth + 1

    def test_descend_monsters(self):
        """Test descending with monsters blocks without treasure."""
        pre = world.new_world()
        pre = world.delve(pre, dice.roll_party, self.state.randrange)
        pre = replace(
            pre,
            depth=3,
            dungeon=make_dungeon(skeleton=1, chest=2, potion=5, dragon=1),
        )
        assert pre.depth > 0

        # Neither town portal nor ring of invisibility
        with pytest.raises(struct.DrollError):
            world.descend(pre, dice.roll_dungeon, self.state.randrange)

        # Ring of invisibility
        pre = replace(
            pre,
            treasure=replace(
                pre.treasure, own=make_artifacts(ring=1)
            ),
        )
        with pytest.raises(struct.DrollError):
            world.descend(pre, dice.roll_dungeon, self.state.randrange)

        # Town portal
        pre = replace(
            pre,
            treasure=replace(
                pre.treasure, own=make_artifacts(ring=1)
            ),
        )
        with pytest.raises(struct.DrollError):
            world.descend(pre, dice.roll_dungeon, self.state.randrange)

    def test_descend_dragon(self):
        """Test descending with dragons requires ring, portal doesn't work."""
        pre = world.new_world()
        pre = world.delve(pre, dice.roll_party, self.state.randrange)
        pre = replace(
            pre,
            depth=3,
            dungeon=make_dungeon(chest=2, potion=5, dragon=3),
        )
        assert pre.depth > 0

        # Neither town portal nor ring of invisibility
        with pytest.raises(struct.DrollError):
            world.descend(pre, dice.roll_dungeon, self.state.randrange)

        # Ring of invisibility
        pre = replace(
            pre,
            treasure=replace(
                pre.treasure, own=make_artifacts(ring=1)
            ),
        )
        post1 = world.descend(pre, dice.roll_dungeon, self.state.randrange)
        assert post1.depth == pre.depth + 1
        assert post1.treasure.own[Artifact.RING] == 0
        assert post1.treasure.own[Artifact.PORTAL] == 0

        # Town portal
        pre = replace(
            pre,
            treasure=replace(
                pre.treasure, own=make_artifacts(portal=1)
            ),
        )
        with pytest.raises(struct.DrollError):
            world.descend(pre, dice.roll_dungeon, self.state.randrange)

        # Both should consume the ring of invisibility
        pre = replace(
            pre,
            treasure=replace(
                pre.treasure, own=make_artifacts(ring=1, portal=1)
            ),
        )
        post3 = world.descend(pre, dice.roll_dungeon, self.state.randrange)
        assert post3.depth == pre.depth + 1
        assert post3.treasure.own[Artifact.RING] == 0
        assert post3.treasure.own[Artifact.PORTAL] == 1

    def test_regroup_discard(self):
        """Temporary party dice must be discarded during next regroup phase."""
        pre1 = world.new_world()
        pre1 = world.delve(pre1, dice.roll_party, self.state.randrange)
        pre1 = replace(
            pre1,
            depth=3,
            party=make_party(fighter=5, cleric=4, mage=3, thief=2, champion=1, scroll=0),
            regroup=struct.Regroup(
                discard=make_party(fighter=0, cleric=5, mage=3, thief=1, champion=0, scroll=0)
            ),
        )

        expected_party = make_party(fighter=5, cleric=0, mage=0, thief=1, champion=1, scroll=0)
        expected_discard = make_party()

        # First, confirm descending works as expected
        descended = world.descend(
            pre1, dice.roll_dungeon, self.state.randrange
        )
        assert descended.party == expected_party
        assert descended.regroup.discard == expected_discard

        # Second, confirm retiring works as expected
        retired = world.retire(pre1)
        assert retired.party == expected_party
        assert retired.regroup.discard == expected_discard

        # Third, confirm retreating works as expected
        pre2 = replace(
            pre1, dungeon=make_dungeon(goblin=1)
        )  # Threat required!
        retreated = world.retreat(pre2)
        assert retreated.party == expected_party
        assert retreated.regroup.discard == expected_discard

    def test_finished_dungeon(self):
        """Test finished_dungeon detects when no actions remain."""
        assert dungeon.finished_dungeon(None)
        assert dungeon.finished_dungeon(make_dungeon())
        assert not dungeon.finished_dungeon(make_dungeon(dragon=3))
        assert not dungeon.finished_dungeon(make_dungeon(goblin=1))
        assert not dungeon.finished_dungeon(make_dungeon(skeleton=2))
        assert not dungeon.finished_dungeon(make_dungeon(ooze=1))
        assert not dungeon.finished_dungeon(make_dungeon(chest=2, potion=3))

    def test_retreat_valid(self):
        """Test valid retreat scenarios."""
        game = world.new_world()
        game = world.delve(game, dice.roll_party, self.state.randrange)
        game = replace(game, depth=2, dungeon=make_dungeon(goblin=1))
        result = world.retreat(game)
        assert result.depth == 0
        assert result.dungeon is None

    def test_retreat_at_depth_one_with_monster(self):
        """Test retreat succeeds at depth 1 when a monster is present"""
        game = world.new_world()
        game = world.delve(game, dice.roll_party, self.state.randrange)
        game = replace(game, depth=1, dungeon=make_dungeon(goblin=1))
        result = world.retreat(game)
        assert result.depth == 0
        assert result.dungeon is None

    def test_retreat_at_depth_one_without_monster(self):
        """Test retreat fails at depth 1 when no monster is present"""
        game = world.new_world()
        game = world.delve(game, dice.roll_party, self.state.randrange)
        game = replace(game, depth=1)
        with pytest.raises(struct.DrollError):
            world.retreat(game)

    def test_retreat_without_descending(self):
        """Test retreat fails if not yet descended."""
        game = world.new_world()
        game = world.delve(game, dice.roll_party, self.state.randrange)
        assert game.depth == 0
        with pytest.raises(struct.DrollError):
            world.retreat(game)

    def test_retreat_when_could_retire(self):
        """Test retreat fails when dungeon is defeated."""
        game = world.new_world()
        game = world.delve(game, dice.roll_party, self.state.randrange)
        game = replace(game, depth=2, dungeon=make_dungeon())
        with pytest.raises(struct.DrollError):
            world.retreat(game)

    def test_max_dungeon_depth(self):
        """Test maximum dungeon depth limit is enforced."""
        game = world.new_world()
        game = world.delve(game, dice.roll_party, self.state.randrange)
        game = replace(game, depth=10, dungeon=make_dungeon())
        with pytest.raises(struct.DrollError):
            world.descend(game, dice.roll_dungeon, self.state.randrange)

    def test_delve_maximum(self):
        """Test that a fourth delve is rejected after three."""
        game = world.new_world()
        game = world.delve(game, dice.roll_party, self.state.randrange)
        game = world.delve(game, dice.roll_party, self.state.randrange)
        game = world.delve(game, dice.roll_party, self.state.randrange)
        assert game.delve == 3
        with pytest.raises(struct.DrollError):
            world.delve(game, dice.roll_party, self.state.randrange)

    def test_score(self):
        """Test score calculation includes experience and treasure bonuses."""
        game = struct.World(
            delve=3,
            depth=1,
            experience=15,
            ability=False,
            dungeon=None,
            treasure=struct.Treasure(
                own=make_artifacts(bait=1, scale=2),
            ),
        )
        assert world.score(game) == 20

    def test_dragon_carryforward(self):
        """Exhaustively check new dice = min(7 - dragons, depth) per rules."""
        game = world.new_world()
        game = world.delve(game, dice.roll_party, self.state.randrange)
        for depth, dragons, new_dice in [
            (1, 0, 1), (2, 0, 2), (3, 0, 3), (4, 0, 4), (5, 0, 5),
            (6, 0, 6), (7, 0, 7), (8, 0, 7), (9, 0, 7), (10, 0, 7),
            (1, 1, 1), (2, 1, 2), (3, 1, 3), (4, 1, 4), (5, 1, 5),
            (6, 1, 6), (7, 1, 6), (8, 1, 6), (9, 1, 6), (10, 1, 6),
            (1, 2, 1), (2, 2, 2), (3, 2, 3), (4, 2, 4), (5, 2, 5),
            (6, 2, 5), (7, 2, 5), (8, 2, 5), (9, 2, 5), (10, 2, 5),
        ]:
            g = replace(
                game, depth=depth - 1, dungeon=make_dungeon(dragon=dragons)
            )
            result = world.descend(g, _roll_all_goblins, self.state.randrange)
            assert result.depth == depth
            assert result.dungeon == make_dungeon(
                goblin=new_dice, dragon=dragons
            ), f"depth={depth}, dragons={dragons}"
