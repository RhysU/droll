# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of world-to-world transitions stemming from player actions."""

from dataclasses import replace
import random
import pytest

from droll import player, struct, world
from droll.struct import Artifact, Dungeon, Party, make_dungeon, make_party, make_artifacts, all_dungeon, all_party


def _remove_monsters(world: struct.World) -> struct.World:
    """Remove all monsters from dungeon for testing treasure interactions."""
    from droll.struct import frozen
    return replace(
        world, dungeon=frozen({
            **world.dungeon,
            Dungeon.GOBLIN: 0, Dungeon.SKELETON: 0, Dungeon.OOZE: 0,
        })
    )


class TestPlayer:

    def setup_method(self):
        """Fixtures with a game containing 2 of each dungeon and party item."""
        self.game = replace(
            world.new_world(),
            dungeon=all_dungeon(2),
            party=all_party(2),
        )
        self.randrange = random.Random(4).randrange

    def test_fighter(self):
        """Test fighter hero attacking goblins and oozes."""
        game = player.apply(
            player.Default, self.game, None, "fighter", "goblin"
        )
        assert game.party[Party.FIGHTER] == 1
        assert game.dungeon[Dungeon.GOBLIN] == 0

        game = player.apply(player.Default, game, None, "fighter", "ooze")
        assert game.party[Party.FIGHTER] == 0
        assert game.dungeon[Dungeon.OOZE] == 1

        with pytest.raises(struct.DrollError):
            player.apply(player.Default, game, None, "fighter", "ooze")

    def test_cleric(self):
        """Test cleric hero attacking skeletons and opening chests."""
        with pytest.raises(struct.DrollError):
            player.apply(player.Default, self.game, None, "cleric", "dragon")

        game = player.apply(
            player.Default, self.game, None, "cleric", "skeleton"
        )
        assert game.party[Party.CLERIC] == 1
        assert game.dungeon[Dungeon.SKELETON] == 0

        game = _remove_monsters(game)  # Required for opening chest
        game = player.apply(
            player.Default, game, self.randrange, "cleric", "chest"
        )
        assert game.party[Party.CLERIC] == 0
        assert game.dungeon[Dungeon.CHEST] == 1
        assert sum(game.treasure.own.values()) == 1

    def test_mage(self):
        """Test mage hero attacking oozes and goblins."""
        game = player.apply(player.Default, self.game, None, "mage", "ooze")
        assert game.party[Party.MAGE] == 1
        assert game.dungeon[Dungeon.OOZE] == 0

        game = player.apply(player.Default, game, None, "mage", "goblin")
        assert game.party[Party.MAGE] == 0
        assert game.dungeon[Dungeon.GOBLIN] == 1

    def test_thief(self):
        """Test thief hero opening chests without consuming monsters."""
        game = player.apply(player.Default, self.game, None, "thief", "ooze")
        assert game.party[Party.THIEF] == 1
        assert game.dungeon[Dungeon.OOZE] == 1

        game = _remove_monsters(game)  # Required for opening chest
        game = player.apply(
            player.Default, game, self.randrange, "thief", "chest"
        )
        assert game.party[Party.THIEF] == 0
        assert game.dungeon[Dungeon.CHEST] == 0
        assert sum(game.treasure.own.values()) == 2

        from droll.struct import frozen
        game = replace(game, party=frozen({**game.party, Party.THIEF: 1}))
        with pytest.raises(struct.DrollError):
            player.apply(player.Default, game, None, "thief", "chest")

    def test_champion(self):
        """Test champion hero attacking goblins and drinking potions."""
        game = player.apply(
            player.Default, self.game, None, "champion", "goblin"
        )
        assert game.party[Party.CHAMPION] == 1
        assert game.dungeon[Dungeon.GOBLIN] == 0

        game = _remove_monsters(game)  # Required for drinking potion
        game = player.apply(
            player.Default, game, None, "champion", "potion", "cleric", "mage"
        )
        assert game.party[Party.CHAMPION] == 0
        assert game.dungeon[Dungeon.POTION] == 0
        assert game.party[Party.CLERIC] == 3
        assert game.party[Party.MAGE] == 3

    def test_scroll_quaff(self):
        """Test scroll used to drink potions and obtain duplicate heroes."""
        with pytest.raises(struct.DrollError):
            player.apply(
                player.Default,
                self.game,
                None,
                "scroll",
                "potion",
                "fighter",
                "fighter",
            )  # Too soon

        game = _remove_monsters(self.game)  # Required for drinking potions
        game = player.apply(
            player.Default,
            game,
            None,
            "scroll",
            "potion",
            "fighter",
            "fighter",
        )  # Duplicate
        assert game.party[Party.SCROLL] == 1
        assert game.dungeon[Dungeon.POTION] == 0
        assert game.party[Party.FIGHTER] == 4

    def test_apply_hero_without_target(self):
        """Applying a hero without a target raises DrollError."""
        with pytest.raises(struct.DrollError):
            player.apply(player.Default, self.game, None, "fighter")

    def test_scroll_reroll(self):
        """Test reroll command to reroll dungeon dice (issue #133)."""
        sequence = [0, 1, 2]

        def canned_sequence(start, stop):
            return start + sequence.pop(0)

        game = player.apply(
            player.Default,
            self.game,
            canned_sequence,
            "reroll",
            "chest",
            "ooze",
            "chest",
        )
        assert game.party[Party.SCROLL] == 1
        assert game.dungeon == make_dungeon(
            goblin=3, skeleton=3, ooze=2, chest=0, potion=2, dragon=2
        )

    def test_unknown_command(self):
        """Unknown command raises DrollError without exposing internals."""
        with pytest.raises(struct.DrollError, match='Unknown token "foo"'):
            player.apply(player.Default, self.game, None, "foo", "goblin")

    def test_unknown_target(self):
        """Unknown target raises DrollError without exposing internals."""
        with pytest.raises(struct.DrollError, match='Unknown token "bar"'):
            player.apply(player.Default, self.game, None, "fighter", "bar")

    def test_scroll_not_reroll(self):
        """Using 'scroll' as a noun for rerolling raises DrollError (#133)."""
        with pytest.raises(struct.DrollError, match="reroll"):
            player.apply(player.Default, self.game, None, "scroll", "goblin")

    def test_no_dungeon_hero_target(self):
        """Hero targeting with no dungeon gives user-friendly error."""
        no_dungeon = replace(self.game, dungeon=None)
        for hero in Party:
            with pytest.raises(struct.DrollError, match="You must descend first"):
                player.apply(player.Default, no_dungeon, None, hero.value, "goblin")

    def test_no_dungeon_ability(self):
        """Ability targeting with no dungeon gives user-friendly error."""
        from droll.heroes import enchantress

        no_dungeon = replace(self.game, dungeon=None, ability=True)
        with pytest.raises(struct.DrollError, match="You must descend first"):
            player.apply(enchantress.Enchantress, no_dungeon, None, "ability", "goblin")


# Shorthand: method returns unsorted generator
def complete(*args):
    """Return sorted list of completions for testing purposes."""
    return list(sorted(player.complete(*args)))


class TestComplete:

    def setup_method(self):
        """Set up test fixtures for completion testing."""
        self.game = replace(
            world.new_world(),
            dungeon=all_dungeon(2),
            party=all_party(2),
        )

    def test_complete0(self):
        """Complete available party and treasure in the zeroth position."""
        game = self.game
        assert complete(game, ("fig",), "fig", 0) == ["fighter"]
        from droll.struct import frozen
        game = replace(game, party=frozen({**game.party, Party.FIGHTER: 0}))
        assert complete(game, ("fig",), "fig", 0) == []  # party
        assert complete(game, ("gob",), "gob", 0) == []  # dungeon
        assert complete(game, ("bai",), "bai", 0) == []  # treasure
        game = replace(
            game,
            treasure=replace(
                game.treasure, own=make_artifacts(bait=1)
            ),
        )
        assert complete(game, ("bai",), "bai", 0) == ["bait"]  # treasure

    def test_complete0_excludes_noncommand_treasures(self):
        """Non-command treasures (portal, ring, scale) excluded from pos 0."""
        game = self.game
        game = replace(
            game,
            treasure=replace(
                game.treasure,
                own=make_artifacts(portal=1, ring=1, scale=1),
            ),
        )
        assert complete(game, ("por",), "por", 0) == []
        assert complete(game, ("rin",), "rin", 0) == []
        assert complete(game, ("sca",), "sca", 0) == []
        game = replace(
            game,
            treasure=replace(
                game.treasure, own=make_artifacts(elixir=1)
            ),
        )
        assert complete(game, ("eli",), "eli", 0) == ["elixir"]

    def test_complete1(self):
        """Complete available party and dungeon in the first position."""
        game = self.game
        assert complete(game, ("fig", "gob"), "gob", 1) == ["goblin"]
        assert complete(game, ("fig", "fig"), "fig", 1) == ["fighter"]  # party
        from droll.struct import frozen
        game = replace(game, dungeon=frozen({**game.dungeon, Dungeon.GOBLIN: 0}))
        assert complete(game, ("fig", "gob"), "gob", 1) == []  # dungeon
        game = replace(game, party=frozen({**game.party, Party.FIGHTER: 0}))
        assert complete(game, ("fig", "fig"), "fig", 1) == []  # dungeon
        game = replace(
            game,
            treasure=replace(
                game.treasure, own=make_artifacts(bait=1)
            ),
        )
        assert complete(game, ("fig", "bai"), "fig", 1) == []  # treasure

        # Special case associated with 'elixir'
        game = replace(game, party=make_party())
        game = replace(game, treasure=struct.Treasure())
        assert complete(game, ("elixir", ""), "", 1) == sorted(p.value for p in Party)

    def test_complete2(self):
        """Complete all party and dungeon in the second position."""
        from droll.struct import frozen
        game = replace(self.game, party=frozen({**self.game.party, Party.FIGHTER: 0}))
        game = _remove_monsters(game)
        assert complete(game, ("X", "Y", "fig"), "fig", 2) == ["fighter"]
        assert complete(game, ("X", "Y", "gob"), "gob", 2) == ["goblin"]
        assert complete(game, ("X", "Y", "ch"), "ch", 2) == [
            "champion",
            "chest",
        ]
