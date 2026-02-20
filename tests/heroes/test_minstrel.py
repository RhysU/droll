# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Minstrel/Bard hero abilities."""

import pytest

from droll import struct
from droll.ability import minstrel_ability
from droll.heroes.minstrel import Bard, Minstrel

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


def testminstrel_ability_discards_dragons():
    """Minstrel/Bard ability discards all dragon dice."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(goblin=1, dragon=3),
        party=struct.Party(fighter=1),
    )
    result = minstrel_ability(world, _UNUSED, "ability")
    assert result.dungeon.dragon == 0
    assert result.dungeon.goblin == 1
    assert not result.ability


def testminstrel_ability_rejects_non_dragon():
    """Minstrel/Bard ability only works on dragons."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(goblin=1, dragon=3),
        party=struct.Party(fighter=1),
    )
    with pytest.raises(struct.DrollError):
        minstrel_ability(world, _UNUSED, "ability", "goblin")


def test_bard_champion_defeats_all_plus_additional():
    """Bard champion defeats all of one type plus one additional."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(goblin=2, skeleton=1),
        party=struct.Party(champion=1),
    )
    result = Bard.party.champion.goblin(
        world, _UNUSED, "champion", "goblin", "skeleton"
    )
    assert result.dungeon.goblin == 0
    assert result.dungeon.skeleton == 0
    assert result.party.champion == 0


def test_minstrel_advances_to_bard():
    """Minstrel advances to Bard at 5+ experience."""
    low_xp = struct.World(experience=4)
    high_xp = struct.World(experience=5)
    assert Minstrel.advance(low_xp) == Minstrel
    assert Minstrel.advance(high_xp) == Bard
