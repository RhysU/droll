# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Testing of basic world-to-world transitions."""

import random

import pytest

import droll.dice
import droll.error
import droll.struct
import droll.world


@pytest.fixture(name='state')
def _state():
    return random.Random(4)


def test_game_initial():
    game = droll.world.new_world()
    assert 0 == game.experience
    assert 0 == sum(game.treasure)
    assert (6 * 3) + (4 * 3) + 6 == sum(game.reserve)


def test_delve_initial(state):
    game = droll.world.new_world()
    game = droll.world.next_delve(game, droll.dice.roll_party, state.randrange)
    assert 0 == game.depth
    assert game.ability is True
    assert 7 == sum(game.party)


def test_dungeon_initial(state):
    game = droll.world.new_world()
    game = droll.world.next_delve(game, droll.dice.roll_party,
                                  state.randrange)
    game = droll.world.next_dungeon(game, droll.dice.roll_dungeon,
                                    state.randrange)
    assert 1 == game.depth
    assert 1 == sum(game.dungeon)


def test_draw_treasure(state):
    pre = droll.world.new_world()
    post = droll.world.draw_treasure(pre, state.randrange)
    assert sum(pre.treasure) == 0
    assert sum(post.treasure) == 1
    assert sum(pre.reserve) - sum(post.reserve) == 1


def test_replace_treasure():
    pre = droll.world.new_world()
    pre = pre._replace(treasure=pre.treasure._replace(elixir=1))
    post = droll.world.replace_treasure(pre, 'elixir')
    assert sum(pre.treasure) == 1
    assert sum(post.treasure) == 0
    assert sum(post.reserve) - sum(pre.reserve) == 1


def test_retire_simple(state):
    pre = droll.world.new_world()
    pre = droll.world.next_delve(pre, droll.dice.roll_party, state.randrange)
    pre = pre._replace(
        depth=3,
        dungeon=droll.struct.Dungeon(
            goblin=0,
            skeleton=0,
            ooze=0,
            chest=2,
            potion=5,
            dragon=0),
    )
    assert pre.depth > 0
    post = droll.world.retire(pre)
    assert post.experience == pre.depth + pre.experience


def test_retire_monsters(state):
    pre = droll.world.new_world()
    pre = droll.world.next_delve(pre, droll.dice.roll_party, state.randrange)
    pre = pre._replace(
        depth=3,
        dungeon=droll.struct.Dungeon(
            goblin=0,
            skeleton=1,
            ooze=0,
            chest=2,
            potion=5,
            dragon=0),
    )
    assert pre.depth > 0

    # Neither town portal nor ring of invisibility
    with pytest.raises(droll.error.DrollError):
        droll.world.retire(pre)

    # Ring of invisibility
    pre = pre._replace(treasure=pre.treasure._replace(ring=1))
    with pytest.raises(droll.error.DrollError):
        droll.world.retire(pre)

    # Town portal
    pre = pre._replace(treasure=pre.treasure._replace(portal=1))
    post = droll.world.retire(pre)
    assert post.experience == pre.depth + pre.experience
    assert post.treasure.portal == 0


def test_retire_dragon(state):
    pre = droll.world.new_world()
    pre = droll.world.next_delve(pre, droll.dice.roll_party, state.randrange)
    pre = pre._replace(
        depth=3,
        dungeon=droll.struct.Dungeon(
            goblin=0,
            skeleton=0,
            ooze=0,
            chest=2,
            potion=5,
            dragon=3),
    )
    assert pre.depth > 0

    # Neither town portal nor ring of invisibility
    with pytest.raises(droll.error.DrollError):
        droll.world.retire(pre)

    # Ring of invisibility
    pre = pre._replace(treasure=pre.treasure._replace(ring=1, portal=0))
    post1 = droll.world.retire(pre)
    assert post1.experience == pre.depth + pre.experience
    assert post1.treasure.ring == 0
    assert post1.treasure.portal == 0

    # Town portal
    pre = pre._replace(treasure=pre.treasure._replace(ring=0, portal=1))
    post2 = droll.world.retire(pre)
    assert post2.experience == pre.depth + pre.experience
    assert post2.treasure.ring == 0
    assert post2.treasure.portal == 0

    # Both should consume the ring of invisibility first
    pre = pre._replace(treasure=pre.treasure._replace(ring=1, portal=1))
    post3 = droll.world.retire(pre)
    assert post3.experience == pre.depth + pre.experience
    assert post3.treasure.ring == 0
    assert post3.treasure.portal == 1


def test_next_dungeon_simple(state):
    pre = droll.world.new_world()
    pre = droll.world.next_delve(pre, droll.dice.roll_party, state.randrange)
    pre = pre._replace(
        depth=3,
        dungeon=droll.struct.Dungeon(
            goblin=0,
            skeleton=0,
            ooze=0,
            chest=2,
            potion=5,
            dragon=0),
    )
    post = droll.world.next_dungeon(pre, droll.dice.roll_dungeon,
                                    state.randrange)
    assert post.depth == pre.depth + 1


def test_next_dungeon_monsters(state):
    pre = droll.world.new_world()
    pre = droll.world.next_delve(pre, droll.dice.roll_party, state.randrange)
    pre = pre._replace(
        depth=3,
        dungeon=droll.struct.Dungeon(
            goblin=0,
            skeleton=1,
            ooze=0,
            chest=2,
            potion=5,
            dragon=1),
    )
    assert pre.depth > 0

    # Neither town portal nor ring of invisibility
    with pytest.raises(droll.error.DrollError):
        droll.world.next_dungeon(pre, droll.dice.roll_dungeon, state.randrange)

    # Ring of invisibility
    pre = pre._replace(treasure=pre.treasure._replace(ring=1, portal=0))
    with pytest.raises(droll.error.DrollError):
        droll.world.next_dungeon(pre, droll.dice.roll_dungeon, state.randrange)

    # Town portal
    pre = pre._replace(treasure=pre.treasure._replace(ring=1, portal=0))
    with pytest.raises(droll.error.DrollError):
        droll.world.next_dungeon(pre, droll.dice.roll_dungeon, state.randrange)


def test_next_dungeon_dragon(state):
    pre = droll.world.new_world()
    pre = droll.world.next_delve(pre, droll.dice.roll_party, state.randrange)
    pre = pre._replace(
        depth=3,
        dungeon=droll.struct.Dungeon(
            goblin=0,
            skeleton=0,
            ooze=0,
            chest=2,
            potion=5,
            dragon=3),
    )
    assert pre.depth > 0

    # Neither town portal nor ring of invisibility
    with pytest.raises(droll.error.DrollError):
        droll.world.next_dungeon(pre, droll.dice.roll_dungeon, state.randrange)

    # Ring of invisibility
    pre = pre._replace(treasure=pre.treasure._replace(ring=1, portal=0))
    post1 = droll.world.next_dungeon(pre, droll.dice.roll_dungeon,
                                     state.randrange)
    assert post1.depth == pre.depth + 1
    assert post1.treasure.ring == 0
    assert post1.treasure.portal == 0

    # Town portal
    pre = pre._replace(treasure=pre.treasure._replace(ring=0, portal=1))
    with pytest.raises(droll.error.DrollError):
        droll.world.next_dungeon(pre, droll.dice.roll_dungeon, state.randrange)

    # Both should consume the ring of invisibility
    pre = pre._replace(treasure=pre.treasure._replace(ring=1, portal=1))
    post3 = droll.world.next_dungeon(pre, droll.dice.roll_dungeon,
                                     state.randrange)
    assert post3.depth == pre.depth + 1
    assert post3.treasure.ring == 0
    assert post3.treasure.portal == 1


def test_score():
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
