# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Knight/DragonSlayer hero abilities."""

import random

from droll import struct
from droll.heroes.knight import Knight, DragonSlayer, _knight_roll_party
from droll.struct import Action, Artifact, Dungeon, Party, make_dungeon, make_party, make_artifacts

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


def test_knight_roll_party_converts_scrolls():
    """Knight converts scrolls to champions when rolling party."""
    randrange = random.Random(4).randrange
    party, regroup = _knight_roll_party(7, randrange)
    assert party[Party.SCROLL] == 0
    assert sum(party.values()) == 7
    assert regroup == struct.Regroup()


def test_knight_ability_baits_dragon():
    """Knight ability converts monsters to dragons without treasure."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=2, skeleton=1),
        party=make_party(fighter=2, champion=1),
    )
    result = Knight.ability(world, _UNUSED, Action.ABILITY)
    assert result.dungeon[Dungeon.DRAGON] == 3
    assert result.dungeon[Dungeon.GOBLIN] == 0
    assert result.dungeon[Dungeon.SKELETON] == 0
    assert not result.ability


def test_dragonslayer_defeats_dragon_with_two_heroes():
    """DragonSlayer defeats a dragon with only 2 distinct heroes."""
    randrange = random.Random(4).randrange
    world = struct.World(
        delve=1,
        depth=1,
        dungeon=make_dungeon(dragon=3),
        party=make_party(fighter=1, mage=1),
        treasure=struct.Treasure(
            own=make_artifacts(),
            box=make_artifacts(scale=6),
        ),
    )
    result = DragonSlayer.party[Party.FIGHTER][Dungeon.DRAGON](
        world, randrange, Party.FIGHTER, (Dungeon.DRAGON, Party.MAGE)
    )
    assert result.dungeon[Dungeon.DRAGON] == 0
    assert result.experience == 1


def test_dragonslayer_advance():
    """Knight advances to DragonSlayer advances to DragonSlayer."""
    low_xp = struct.World(experience=2)
    mid_xp = struct.World(experience=7)
    high_xp = struct.World(experience=15)
    assert Knight.advance(low_xp) == Knight
    assert Knight.advance(mid_xp) == DragonSlayer
    assert DragonSlayer.advance(high_xp) == DragonSlayer
