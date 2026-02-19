# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for HalfGoblin/Chieftain hero abilities."""

import random
import pytest

import droll.error
import droll.struct
from droll.heroes.halfgoblin import (
    Chieftain,
    HalfGoblin,
    _chieftain_ability,
    _halfgoblin_ability,
)

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


def test_halfgoblin_transforms_goblin_to_thief():
    """HalfGoblin transforms 1 goblin into 1 thief."""
    world = droll.struct.World(
        ability=True,
        dungeon=droll.struct.Dungeon(goblin=2, skeleton=1),
        party=droll.struct.Party(fighter=1),
    )
    result = _halfgoblin_ability(world, _UNUSED, "ability", "goblin")
    # Discard during subsequent regroup phase tested elsewhere
    assert result.dungeon.goblin == 1
    assert result.party.thief == 1
    assert not result.ability


def test_chieftain_transforms_two_monsters():
    """Chieftain transforms 2 goblins into 2 thieves when available."""
    world = droll.struct.World(
        ability=True,
        dungeon=droll.struct.Dungeon(goblin=2, skeleton=1),
        party=droll.struct.Party(fighter=1),
    )
    result = _chieftain_ability(world, _UNUSED, "ability", "goblin", "goblin")
    # Discard during subsequent regroup phase tested elsewhere
    assert result.dungeon.goblin == 0
    assert result.dungeon.skeleton == 1
    assert result.party.thief == 2


def test_chieftain_transforms_one_monster():
    """Chieftain transforms 1 goblin into 1 thief when 1 available."""
    world = droll.struct.World(
        ability=True,
        dungeon=droll.struct.Dungeon(goblin=1, skeleton=1),
        party=droll.struct.Party(fighter=1),
    )
    result = _chieftain_ability(
        world,
        _UNUSED,
        "ability",
        "goblin",
    )
    # Discard during subsequent regroup phase tested elsewhere
    assert result.dungeon.goblin == 0
    assert result.dungeon.skeleton == 1
    assert result.party.thief == 1


def test_halfgoblin_rejects_non_goblin():
    """HalfGoblin ability rejects non-goblin targets."""
    world = droll.struct.World(
        ability=True,
        dungeon=droll.struct.Dungeon(goblin=1, skeleton=1),
        party=droll.struct.Party(fighter=1),
    )
    with pytest.raises(droll.error.DrollError):
        _halfgoblin_ability(world, _UNUSED, "ability", "skeleton")


def test_chieftain_rejects_non_goblin_targets():
    """Chieftain rejects non-goblin target, extra target, and excess targets."""
    world = droll.struct.World(
        ability=True,
        dungeon=droll.struct.Dungeon(goblin=2, skeleton=1),
        party=droll.struct.Party(fighter=1),
    )
    with pytest.raises(droll.error.DrollError):
        _chieftain_ability(world, _UNUSED, "ability", "skeleton")
    with pytest.raises(droll.error.DrollError):
        _chieftain_ability(world, _UNUSED, "ability", "goblin", "skeleton")
    with pytest.raises(droll.error.DrollError):
        _chieftain_ability(
            world, _UNUSED, "ability", "goblin", "goblin", "goblin"
        )


def test_halfgoblin_advances_to_chieftain():
    """HalfGoblin advances to Chieftain at 5+ experience."""
    low_xp = droll.struct.World(experience=4)
    high_xp = droll.struct.World(experience=5)
    assert HalfGoblin.advance(low_xp) == HalfGoblin
    assert HalfGoblin.advance(high_xp) == Chieftain


def test_halfgoblin_fighter_chests_potions():
    """HalfGoblin opens chests and quaff portions when monsters present."""
    randrange = random.Random(4).randrange
    world = droll.struct.World(
        delve=1,
        depth=1,
        ability=True,
        dungeon=droll.struct.Dungeon(goblin=1, chest=1, potion=1),
        party=droll.struct.Party(fighter=5),
        treasure=droll.struct.Treasure(
            own=droll.struct.Artifacts(),
            box=droll.struct.Artifacts(scale=1),
        ),
    )

    result1 = HalfGoblin.party.fighter.chest(
        world, randrange, "fighter", "chest"
    )
    assert result1.dungeon.chest == 0
    assert result1.dungeon.goblin == 1
    assert result1.party.fighter == 4
    assert result1.treasure.own.scale == 1

    result2 = HalfGoblin.party.fighter.potion(
        world, randrange, "fighter", "potion", "mage"
    )
    assert result2.dungeon.goblin == 1
    assert result2.dungeon.potion == 0
    assert result2.party.fighter == 4
    assert result2.party.mage == 1
