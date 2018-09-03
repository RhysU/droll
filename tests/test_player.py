# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import random

import pytest

import droll.action as action
import droll.player as player
import droll.world as world


@pytest.fixture(name='game')
def _game():
    return world.new_game()._replace(
        level=world.Level(*([2] * len(world.Level._fields))),
        party=world.Party(*([2] * len(world.Party._fields))),
    )


def __remove_monsters(game: world.World) -> world.World:
    return game._replace(
        level=game.level._replace(goblin=0, skeleton=0, ooze=0)
    )


@pytest.fixture(name='randrange')
def _randrange():
    return random.Random(4).randrange


def test_fighter(game):
    game = player.apply(player.DEFAULT, game, None, 'fighter', 'goblin')
    assert game.party.fighter == 1
    assert game.level.goblin == 0

    game = player.apply(player.DEFAULT, game, None, 'fighter', 'ooze')
    assert game.party.fighter == 0
    assert game.level.ooze == 1

    with pytest.raises(action.ActionError):
        player.apply(player.DEFAULT, game, None, 'fighter', 'ooze')


def test_cleric(game, randrange):
    with pytest.raises(action.ActionError):
        player.apply(player.DEFAULT, game, None, 'cleric', 'dragon')

    game = player.apply(player.DEFAULT, game, None, 'cleric', 'skeleton')
    assert game.party.cleric == 1
    assert game.level.skeleton == 0

    game = __remove_monsters(game)  # Required for opening chest
    game = player.apply(player.DEFAULT, game, randrange, 'cleric', 'chest')
    assert game.party.cleric == 0
    assert game.level.chest == 1
    assert sum(game.treasure) == 1


def test_mage(game):
    game = player.apply(player.DEFAULT, game, None, 'mage', 'ooze')
    assert game.party.mage == 1
    assert game.level.ooze == 0

    game = player.apply(player.DEFAULT, game, None, 'mage', 'goblin')
    assert game.party.mage == 0
    assert game.level.goblin == 1


def test_thief(game, randrange):
    game = player.apply(player.DEFAULT, game, None, 'thief', 'ooze')
    assert game.party.thief == 1
    assert game.level.ooze == 1

    game = __remove_monsters(game)  # Required for opening chest
    game = player.apply(player.DEFAULT, game, randrange, 'thief', 'chest')
    assert game.party.thief == 0
    assert game.level.chest == 0
    assert sum(game.treasure) == 2

    game = game._replace(party=game.party._replace(thief=1))  # Add one
    with pytest.raises(action.ActionError):
        player.apply(player.DEFAULT, game, None, 'thief', 'chest')


def test_champion(game):
    game = player.apply(player.DEFAULT, game, None, 'champion', 'goblin')
    assert game.party.champion == 1
    assert game.level.goblin == 0

    game = __remove_monsters(game)  # Required for drinking potion
    game = player.apply(player.DEFAULT, game, None,
                        'champion', 'potion', 'cleric', 'mage')  # Different
    assert game.party.champion == 0
    assert game.level.potion == 0
    assert game.party.cleric == 3
    assert game.party.mage == 3


def test_scroll_quaff(game):
    with pytest.raises(action.ActionError):
        player.apply(player.DEFAULT, game, None,
                     'scroll', 'potion', 'fighter', 'fighter')  # Too soon

    game = __remove_monsters(game)  # Required for drinking potions
    game = player.apply(player.DEFAULT, game, None,
                        'scroll', 'potion', 'fighter', 'fighter')  # Duplicate
    assert game.party.scroll == 1
    assert game.level.potion == 0
    assert game.party.fighter == 4


def test_scroll_reroll(game):
    # Consumed by canned_sequence just below
    sequence = [0, 1, 2]

    def canned_sequence(start, stop):
        return start + sequence.pop(0)

    game = player.apply(player.DEFAULT, game, canned_sequence,
                        'scroll', 'chest', 'ooze', 'chest')
    assert game.party.scroll == 1
    assert game.level == world.Level(
        goblin=3,
        skeleton=3,
        ooze=2,
        chest=0,
        potion=2,
        dragon=2,
    )
