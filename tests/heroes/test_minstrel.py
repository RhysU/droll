# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Minstrel/Bard hero abilities."""

import pytest

from droll import struct
from droll.ability import minstrel_ability
from droll.heroes.minstrel import Bard, Minstrel
from droll.struct import Action, Dungeon, Party, make_dungeon, make_party

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


def test_minstrel_ability_discards_dragons():
    """Minstrel/Bard ability discards all dragon dice."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=1, dragon=3),
        party=make_party(fighter=1),
    )
    result = minstrel_ability(world, _UNUSED, Action.ABILITY)
    assert result.dungeon[Dungeon.DRAGON] == 0
    assert result.dungeon[Dungeon.GOBLIN] == 1
    assert not result.ability


def test_minstrel_ability_rejects_non_dragon():
    """Minstrel/Bard ability only works on dragons."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=1, dragon=3),
        party=make_party(fighter=1),
    )
    with pytest.raises(struct.DrollError):
        minstrel_ability(world, _UNUSED, Action.ABILITY, (Dungeon.GOBLIN,))


def test_bard_champion_defeats_all_plus_additional():
    """Bard champion defeats all of one type plus one additional."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=2, skeleton=1),
        party=make_party(champion=1),
    )
    result = Bard.party[Party.CHAMPION][Dungeon.GOBLIN](
        world, _UNUSED, Party.CHAMPION, (Dungeon.GOBLIN, Dungeon.SKELETON)
    )
    assert result.dungeon[Dungeon.GOBLIN] == 0
    assert result.dungeon[Dungeon.SKELETON] == 0
    assert result.party[Party.CHAMPION] == 0


def test_minstrel_advances_to_bard():
    """Minstrel advances to Bard at 5+ experience."""
    low_xp = struct.World(experience=4)
    high_xp = struct.World(experience=5)
    assert Minstrel.advance(low_xp) == Minstrel
    assert Minstrel.advance(high_xp) == Bard
