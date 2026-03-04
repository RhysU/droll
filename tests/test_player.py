# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of world-to-world transitions stemming from player actions."""

from dataclasses import fields, replace
import random
import pytest

from droll import player, struct, world


def _remove_monsters(world: struct.World) -> struct.World:
    """Remove all monsters from dungeon for testing treasure interactions."""
    return replace(
        world, dungeon=replace(world.dungeon, goblin=0, skeleton=0, ooze=0)
    )


class TestPlayer:

    def setup_method(self):
        """Fixtures with a game containing 2 of each dungeon and party item."""
        self.game = replace(
            world.new_world(),
            dungeon=struct.Dungeon(*([2] * len(fields(struct.Dungeon)))),
            party=struct.Party(*([2] * len(fields(struct.Party)))),
        )
        self.randrange = random.Random(4).randrange

    def test_fighter(self):
        """Test fighter hero attacking goblins and oozes."""
        game = player.apply(
            player.Default, self.game, None, "fighter", "goblin"
        )
        assert game.party.fighter == 1
        assert game.dungeon.goblin == 0

        game = player.apply(player.Default, game, None, "fighter", "ooze")
        assert game.party.fighter == 0
        assert game.dungeon.ooze == 1

        with pytest.raises(struct.DrollError):
            player.apply(player.Default, game, None, "fighter", "ooze")

    def test_cleric(self):
        """Test cleric hero attacking skeletons and opening chests."""
        with pytest.raises(struct.DrollError):
            player.apply(player.Default, self.game, None, "cleric", "dragon")

        game = player.apply(
            player.Default, self.game, None, "cleric", "skeleton"
        )
        assert game.party.cleric == 1
        assert game.dungeon.skeleton == 0

        game = _remove_monsters(game)  # Required for opening chest
        game = player.apply(
            player.Default, game, self.randrange, "cleric", "chest"
        )
        assert game.party.cleric == 0
        assert game.dungeon.chest == 1
        assert sum(struct.field_values(game.treasure.own)) == 1

    def test_mage(self):
        """Test mage hero attacking oozes and goblins."""
        game = player.apply(player.Default, self.game, None, "mage", "ooze")
        assert game.party.mage == 1
        assert game.dungeon.ooze == 0

        game = player.apply(player.Default, game, None, "mage", "goblin")
        assert game.party.mage == 0
        assert game.dungeon.goblin == 1

    def test_thief(self):
        """Test thief hero opening chests without consuming monsters."""
        game = player.apply(player.Default, self.game, None, "thief", "ooze")
        assert game.party.thief == 1
        assert game.dungeon.ooze == 1

        game = _remove_monsters(game)  # Required for opening chest
        game = player.apply(
            player.Default, game, self.randrange, "thief", "chest"
        )
        assert game.party.thief == 0
        assert game.dungeon.chest == 0
        assert sum(struct.field_values(game.treasure.own)) == 2

        game = replace(game, party=replace(game.party, thief=1))  # Add one
        with pytest.raises(struct.DrollError):
            player.apply(player.Default, game, None, "thief", "chest")

    def test_champion(self):
        """Test champion hero attacking goblins and drinking potions."""
        game = player.apply(
            player.Default, self.game, None, "champion", "goblin"
        )
        assert game.party.champion == 1
        assert game.dungeon.goblin == 0

        game = _remove_monsters(game)  # Required for drinking potion
        game = player.apply(
            player.Default, game, None, "champion", "potion", "cleric", "mage"
        )  # Different
        assert game.party.champion == 0
        assert game.dungeon.potion == 0
        assert game.party.cleric == 3
        assert game.party.mage == 3

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
        assert game.party.scroll == 1
        assert game.dungeon.potion == 0
        assert game.party.fighter == 4

    def test_apply_hero_without_target(self):
        """Applying a hero without a target raises DrollError."""
        with pytest.raises(struct.DrollError):
            player.apply(player.Default, self.game, None, "fighter")

    def test_scroll_reroll(self):
        """Test reroll command to reroll dungeon dice (issue #133)."""
        # Consumed by canned_sequence just below
        sequence = [0, 1, 2]

        def canned_sequence(start, stop):
            """Predetermined sequence values for deterministic testing."""
            return start + sequence.pop(0)

        # 'reroll' re-rolls chests via the scroll mechanic
        game = player.apply(
            player.Default,
            self.game,
            canned_sequence,
            "reroll",
            "chest",
            "ooze",
            "chest",
        )
        assert game.party.scroll == 1
        assert game.dungeon == struct.Dungeon(
            goblin=3, skeleton=3, ooze=2, chest=0, potion=2, dragon=2
        )

    def test_unknown_command(self):
        """Unknown command raises DrollError without exposing internals."""
        with pytest.raises(struct.DrollError, match='Unknown command "foo"'):
            player.apply(player.Default, self.game, None, "foo", "goblin")

    def test_unknown_target(self):
        """Unknown target raises DrollError without exposing internals."""
        with pytest.raises(struct.DrollError, match='Unknown target "bar"'):
            player.apply(player.Default, self.game, None, "fighter", "bar")

    def test_scroll_not_reroll(self):
        """Using 'scroll' as a noun for rerolling raises DrollError (#133)."""
        with pytest.raises(struct.DrollError, match="reroll"):
            player.apply(player.Default, self.game, None, "scroll", "goblin")

    def test_no_dungeon_hero_target(self):
        """Hero targeting with no dungeon gives user-friendly error."""
        no_dungeon = replace(self.game, dungeon=None)
        for hero in struct.field_names(struct.Party):
            with pytest.raises(struct.DrollError, match="You must descend first"):
                player.apply(player.Default, no_dungeon, None, hero, "goblin")

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
            dungeon=struct.Dungeon(*([2] * len(fields(struct.Dungeon)))),
            party=struct.Party(*([2] * len(fields(struct.Party)))),
        )

    def test_complete0(self):
        """Complete available party and treasure in the zeroth position."""
        game = self.game
        assert complete(game, ("fig",), "fig", 0) == ["fighter"]
        game = replace(game, party=replace(game.party, fighter=0))
        assert complete(game, ("fig",), "fig", 0) == []  # party
        assert complete(game, ("gob",), "gob", 0) == []  # dungeon
        assert complete(game, ("bai",), "bai", 0) == []  # treasure
        game = replace(
            game,
            treasure=replace(
                game.treasure, own=replace(game.treasure.own, bait=1)
            ),
        )
        assert complete(game, ("bai",), "bai", 0) == ["bait"]  # treasure

    def test_complete0_excludes_noncommand_treasures(self):
        """Non-command treasures (portal, ring, scale) excluded from pos 0."""
        game = self.game
        # Add all three non-command treasures
        game = replace(
            game,
            treasure=replace(
                game.treasure,
                own=replace(game.treasure.own, portal=1, ring=1, scale=1),
            ),
        )
        # None of them should appear in completions
        assert complete(game, ("por",), "por", 0) == []
        assert complete(game, ("rin",), "rin", 0) == []
        assert complete(game, ("sca",), "sca", 0) == []
        # But a command treasure like elixir should still work
        game = replace(
            game,
            treasure=replace(
                game.treasure, own=replace(game.treasure.own, elixir=1)
            ),
        )
        assert complete(game, ("eli",), "eli", 0) == ["elixir"]

    def test_complete1(self):
        """Complete available party and dungeon in the first position."""
        game = self.game
        # Vanilla first position stuff
        assert complete(game, ("fig", "gob"), "gob", 1) == ["goblin"]
        assert complete(game, ("fig", "fig"), "fig", 1) == ["fighter"]  # party
        game = replace(game, dungeon=replace(game.dungeon, goblin=0))
        assert complete(game, ("fig", "gob"), "gob", 1) == []  # dungeon
        game = replace(game, party=replace(game.party, fighter=0))
        assert complete(game, ("fig", "fig"), "fig", 1) == []  # dungeon
        game = replace(
            game,
            treasure=replace(
                game.treasure, own=replace(game.treasure.own, bait=1)
            ),
        )
        assert complete(game, ("fig", "bai"), "fig", 1) == []  # treasure

        # Special case associated with 'elixir'
        game = replace(game, party=struct.Party())
        game = replace(game, treasure=struct.Treasure())
        assert complete(game, ("elixir", ""), "", 1) == list(
            sorted(struct.field_names(struct.Party))
        )

    def test_complete2(self):
        """Complete all party and dungeon in the second position."""
        game = replace(self.game, party=replace(self.game.party, fighter=0))
        game = _remove_monsters(game)
        assert complete(game, ("X", "Y", "fig"), "fig", 2) == ["fighter"]
        assert complete(game, ("X", "Y", "gob"), "gob", 2) == ["goblin"]
        assert complete(game, ("X", "Y", "ch"), "ch", 2) == [
            "champion",
            "chest",
        ]
