# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Enchantress/Beguiler hero abilities."""

import pytest

from droll import struct
from droll.ability import beguiler_ability, enchantress_ability
from droll.heroes.enchantress import Beguiler, Enchantress
from droll.struct import Action, Dungeon, Party, make_dungeon, make_party

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


def test_enchantress_transforms_monster_to_potion():
    """Enchantress transforms 1 monster into 1 potion."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=2, skeleton=1),
        party=make_party(fighter=1),
    )
    result = enchantress_ability(world, _UNUSED, Action.ABILITY, (Dungeon.GOBLIN,))
    assert result.dungeon[Dungeon.GOBLIN] == 1
    assert result.dungeon[Dungeon.POTION] == 1
    assert not result.ability


def test_beguiler_transforms_two_monsters():
    """Beguiler transforms 2 monsters into 1 potion when available."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=2, skeleton=1),
        party=make_party(fighter=1),
    )
    result = beguiler_ability(world, _UNUSED, Action.ABILITY, (Dungeon.GOBLIN, Dungeon.SKELETON))
    assert result.dungeon[Dungeon.GOBLIN] == 1
    assert result.dungeon[Dungeon.SKELETON] == 0
    assert result.dungeon[Dungeon.POTION] == 1


def test_beguiler_requires_two_when_available():
    """Beguiler must transform 2 monsters when 2+ available."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=2, skeleton=1),
        party=make_party(fighter=1),
    )
    with pytest.raises(struct.DrollError):
        beguiler_ability(world, _UNUSED, Action.ABILITY, (Dungeon.GOBLIN,))


def test_beguiler_rejects_too_many_targets():
    """Beguiler rejects more than 2 targets."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=2, skeleton=1),
        party=make_party(fighter=1),
    )
    with pytest.raises(struct.DrollError):
        beguiler_ability(
            world, _UNUSED, Action.ABILITY, (Dungeon.GOBLIN, Dungeon.SKELETON, Dungeon.GOBLIN)
        )


def test_enchantress_message_without_target():
    """Enchantress fails gracefully when no targets supplied."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=2, skeleton=1),
        party=make_party(fighter=1),
    )
    with pytest.raises(struct.DrollError):
        result = enchantress_ability(world, _UNUSED, Action.ABILITY)


def test_beguiler_message_without_target():
    """Beguiler fails gracefully when no targets supplied."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=2, skeleton=1),
        party=make_party(fighter=1),
    )
    with pytest.raises(struct.DrollError):
        result = beguiler_ability(world, _UNUSED, Action.ABILITY)


def test_enchantress_advances_to_beguiler():
    """Enchantress advances to Beguiler at 5+ experience."""
    low_xp = struct.World(experience=4)
    high_xp = struct.World(experience=5)
    assert Enchantress.advance(low_xp) == Enchantress
    assert Enchantress.advance(high_xp) == Beguiler
