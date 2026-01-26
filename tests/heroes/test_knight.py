# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Knight/DragonSlayer hero abilities."""

import random

import droll.dice
import droll.struct
from droll.heroes.knight import Knight, DragonSlayer, knight_roll_party


def test_knight_roll_party_converts_scrolls():
    """Knight converts scrolls to champions when rolling party."""
    state = random.Random(4)
    party = knight_roll_party(7, state.randrange)
    assert party.scroll == 0
    assert sum(droll.struct.field_values(party)) == 7


def test_knight_ability_baits_dragon():
    """Knight ability converts monsters to dragons without treasure."""
    state = random.Random(4)
    world = droll.struct.World(
        delve=1, depth=1, experience=0, ability=True,
        dungeon=droll.struct.Dungeon(goblin=2, skeleton=1),
        party=droll.struct.Party(fighter=2, champion=1),
        treasure=droll.struct.Treasure(), reserve=droll.struct.Treasure(),
    )
    result = Knight.ability(world, state.randrange, "ability")
    assert result.dungeon.dragon == 3
    assert result.dungeon.goblin == 0
    assert result.dungeon.skeleton == 0
    assert result.ability is False


def test_dragonslayer_advance():
    """DragonSlayer stays DragonSlayer after advancing."""
    world = droll.struct.World(
        delve=1, depth=0, experience=10, ability=True,
        dungeon=None, party=None, treasure=droll.struct.Treasure(),
        reserve=droll.struct.Treasure(),
    )
    assert DragonSlayer.advance(world) == DragonSlayer
