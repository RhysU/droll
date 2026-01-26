# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of world-to-world transitions stemming from player actions."""

from dataclasses import fields, replace
import random

import pytest

import droll.error as error
import droll.player as player
import droll.struct as struct
import droll.world as world


@pytest.fixture(name="game")
def _game():
    return replace(
        world.new_world(),
        dungeon=struct.Dungeon(*([2] * len(fields(struct.Dungeon)))),
        party=struct.Party(*([2] * len(fields(struct.Party)))),
    )


def __remove_monsters(game: struct.World) -> struct.World:
    return replace(
        game, dungeon=replace(game.dungeon, goblin=0, skeleton=0, ooze=0)
    )


@pytest.fixture(name="randrange")
def _randrange():
    return random.Random(4).randrange


def test_fighter(game):
    game = player.apply(player.Default, game, None, "fighter", "goblin")
    assert game.party.fighter == 1
    assert game.dungeon.goblin == 0

    game = player.apply(player.Default, game, None, "fighter", "ooze")
    assert game.party.fighter == 0
    assert game.dungeon.ooze == 1

    with pytest.raises(error.DrollError):
        player.apply(player.Default, game, None, "fighter", "ooze")


def test_cleric(game, randrange):
    with pytest.raises(error.DrollError):
        player.apply(player.Default, game, None, "cleric", "dragon")

    game = player.apply(player.Default, game, None, "cleric", "skeleton")
    assert game.party.cleric == 1
    assert game.dungeon.skeleton == 0

    game = __remove_monsters(game)  # Required for opening chest
    game = player.apply(player.Default, game, randrange, "cleric", "chest")
    assert game.party.cleric == 0
    assert game.dungeon.chest == 1
    assert sum(struct.field_values(game.treasure)) == 1


def test_mage(game):
    game = player.apply(player.Default, game, None, "mage", "ooze")
    assert game.party.mage == 1
    assert game.dungeon.ooze == 0

    game = player.apply(player.Default, game, None, "mage", "goblin")
    assert game.party.mage == 0
    assert game.dungeon.goblin == 1


def test_thief(game, randrange):
    game = player.apply(player.Default, game, None, "thief", "ooze")
    assert game.party.thief == 1
    assert game.dungeon.ooze == 1

    game = __remove_monsters(game)  # Required for opening chest
    game = player.apply(player.Default, game, randrange, "thief", "chest")
    assert game.party.thief == 0
    assert game.dungeon.chest == 0
    assert sum(struct.field_values(game.treasure)) == 2

    game = replace(
        game, party=replace(game.party, thief=1)
    )  # Add one
    with pytest.raises(error.DrollError):
        player.apply(player.Default, game, None, "thief", "chest")


def test_champion(game):
    game = player.apply(player.Default, game, None, "champion", "goblin")
    assert game.party.champion == 1
    assert game.dungeon.goblin == 0

    game = __remove_monsters(game)  # Required for drinking potion
    game = player.apply(
        player.Default, game, None, "champion", "potion", "cleric", "mage"
    )  # Different
    assert game.party.champion == 0
    assert game.dungeon.potion == 0
    assert game.party.cleric == 3
    assert game.party.mage == 3


def test_scroll_quaff(game):
    with pytest.raises(error.DrollError):
        player.apply(
            player.Default, game, None, "scroll", "potion", "fighter", "fighter"
        )  # Too soon

    game = __remove_monsters(game)  # Required for drinking potions
    game = player.apply(
        player.Default, game, None, "scroll", "potion", "fighter", "fighter"
    )  # Duplicate
    assert game.party.scroll == 1
    assert game.dungeon.potion == 0
    assert game.party.fighter == 4


def test_scroll_reroll(game):
    # Consumed by canned_sequence just below
    sequence = [0, 1, 2]

    def canned_sequence(start, stop):
        return start + sequence.pop(0)

    # Notice scroll causes chests to be re-rolled
    game = player.apply(
        player.Default,
        game,
        canned_sequence,
        "scroll",
        "chest",
        "ooze",
        "chest",
    )
    assert game.party.scroll == 1
    assert game.dungeon == struct.Dungeon(
        goblin=3, skeleton=3, ooze=2, chest=0, potion=2, dragon=2
    )


# Shorthand for testing completions given that method returns unsorted generator
def complete(*args):
    return list(sorted(player.complete(*args)))


def test_complete0(game):
    """Complete available party and treasure in the zeroth position."""
    assert ["fighter"] == complete(game, ("fig",), "fig", 0)
    game = replace(
        game, party=replace(game.party, fighter=0)
    )
    assert [] == complete(game, ("fig",), "fig", 0)  # party
    assert [] == complete(game, ("gob",), "gob", 0)  # dungeon
    assert [] == complete(game, ("bai",), "bai", 0)  # treasure
    game = replace(
        game, treasure=replace(game.treasure, bait=1)
    )
    assert ["bait"] == complete(game, ("bai",), "bai", 0)  # treasure


def test_complete1(game):
    """Complete available party and dungeon in the first position."""
    # Vanilla first position stuff
    assert ["goblin"] == complete(game, ("fig", "gob"), "gob", 1)
    assert ["fighter"] == complete(game, ("fig", "fig"), "fig", 1)  # party
    game = replace(
        game, dungeon=replace(game.dungeon, goblin=0)
    )
    assert [] == complete(game, ("fig", "gob"), "gob", 1)  # dungeon
    game = replace(
        game, party=replace(game.party, fighter=0)
    )
    assert [] == complete(game, ("fig", "fig"), "fig", 1)  # dungeon
    game = replace(
        game, treasure=replace(game.treasure, bait=1)
    )
    assert [] == complete(game, ("fig", "bai"), "fig", 1)  # treasure

    # Special case associated with 'elixir'
    game = replace(game, party=struct.Party(*([0] * len(fields(game.party)))))
    game = replace(
        game, treasure=struct.Treasure(*([0] * len(fields(game.treasure))))
    )
    assert list(sorted(struct.field_names(struct.Party))) == (
        complete(game, ("elixir", ""), "", 1)
    )


def test_complete2(game):
    """Complete all party and dungeon in the second position."""
    game = replace(
        game, party=replace(game.party, fighter=0)
    )
    game = __remove_monsters(game)
    assert ["fighter"] == complete(game, ("X", "Y", "fig"), "fig", 2)
    assert ["goblin"] == complete(game, ("X", "Y", "gob"), "gob", 2)
    assert ["champion", "chest"] == complete(game, ("X", "Y", "ch"), "ch", 2)
