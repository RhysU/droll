# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for HalfGoblin/Chieftain hero abilities."""

import random
import pytest

from droll import struct
from droll.ability import chieftain_ability, halfgoblin_ability
from droll.heroes.halfgoblin import Chieftain, HalfGoblin
from droll.struct import Action, Artifact, Dungeon, Party, make_dungeon, make_party, make_artifacts

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


def test_halfgoblin_transforms_goblin_to_thief():
    """HalfGoblin transforms 1 goblin into 1 thief."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=2, skeleton=1),
        party=make_party(fighter=1),
    )
    result = halfgoblin_ability(world, _UNUSED, Action.ABILITY, (Dungeon.GOBLIN,))
    # Discard during subsequent regroup phase tested elsewhere
    assert result.dungeon[Dungeon.GOBLIN] == 1
    assert result.party[Party.THIEF] == 1
    assert not result.ability


def test_chieftain_transforms_two_monsters():
    """Chieftain transforms 2 goblins into 2 thieves when available."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=2, skeleton=1),
        party=make_party(fighter=1),
    )
    result = chieftain_ability(world, _UNUSED, Action.ABILITY, (Dungeon.GOBLIN, Dungeon.GOBLIN))
    # Discard during subsequent regroup phase tested elsewhere
    assert result.dungeon[Dungeon.GOBLIN] == 0
    assert result.dungeon[Dungeon.SKELETON] == 1
    assert result.party[Party.THIEF] == 2


def test_chieftain_transforms_one_monster():
    """Chieftain transforms 1 goblin into 1 thief when 1 available."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=1, skeleton=1),
        party=make_party(fighter=1),
    )
    result = chieftain_ability(
        world,
        _UNUSED,
        Action.ABILITY,
        (Dungeon.GOBLIN,),
    )
    # Discard during subsequent regroup phase tested elsewhere
    assert result.dungeon[Dungeon.GOBLIN] == 0
    assert result.dungeon[Dungeon.SKELETON] == 1
    assert result.party[Party.THIEF] == 1


def test_halfgoblin_rejects_non_goblin():
    """HalfGoblin ability rejects non-goblin targets."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=1, skeleton=1),
        party=make_party(fighter=1),
    )
    with pytest.raises(struct.DrollError):
        halfgoblin_ability(world, _UNUSED, Action.ABILITY, (Dungeon.SKELETON,))


def test_chieftain_rejects_non_goblin_targets():
    """Chieftain rejects non-goblin, extra, and excess targets."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=2, skeleton=1),
        party=make_party(fighter=1),
    )
    with pytest.raises(struct.DrollError):
        chieftain_ability(world, _UNUSED, Action.ABILITY, (Dungeon.SKELETON,))
    with pytest.raises(struct.DrollError):
        chieftain_ability(world, _UNUSED, Action.ABILITY, (Dungeon.GOBLIN, Dungeon.SKELETON))
    with pytest.raises(struct.DrollError):
        chieftain_ability(
            world, _UNUSED, Action.ABILITY, (Dungeon.GOBLIN, Dungeon.GOBLIN, Dungeon.GOBLIN)
        )


def test_halfgoblin_advances_to_chieftain():
    """HalfGoblin advances to Chieftain at 5+ experience."""
    low_xp = struct.World(experience=4)
    high_xp = struct.World(experience=5)
    assert HalfGoblin.advance(low_xp) == HalfGoblin
    assert HalfGoblin.advance(high_xp) == Chieftain


def test_halfgoblin_fighter_chests_potions():
    """HalfGoblin opens chests and quaff portions when monsters present."""
    randrange = random.Random(4).randrange
    world = struct.World(
        delve=1,
        depth=1,
        ability=True,
        dungeon=make_dungeon(goblin=1, chest=1, potion=1),
        party=make_party(fighter=5),
        treasure=struct.Treasure(
            own=make_artifacts(),
            box=make_artifacts(scale=1),
        ),
    )

    result1 = HalfGoblin.party[Party.FIGHTER][Dungeon.CHEST](
        world, randrange, Party.FIGHTER, (Dungeon.CHEST,)
    )
    assert result1.dungeon[Dungeon.CHEST] == 0
    assert result1.dungeon[Dungeon.GOBLIN] == 1
    assert result1.party[Party.FIGHTER] == 4
    assert result1.treasure.own[Artifact.SCALE] == 1

    result2 = HalfGoblin.party[Party.FIGHTER][Dungeon.POTION](
        world, randrange, Party.FIGHTER, (Dungeon.POTION, Party.MAGE)
    )
    assert result2.dungeon[Dungeon.GOBLIN] == 1
    assert result2.dungeon[Dungeon.POTION] == 0
    assert result2.party[Party.FIGHTER] == 4
    assert result2.party[Party.MAGE] == 1
