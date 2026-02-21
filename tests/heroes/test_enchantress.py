# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Enchantress/Beguiler hero abilities."""

import pytest

from droll import struct
from droll.ability import beguiler_ability, enchantress_ability
from droll.heroes.enchantress import Beguiler, Enchantress

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


def test_enchantress_transforms_monster_to_potion():
    """Enchantress transforms 1 monster into 1 potion."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(goblin=2, skeleton=1),
        party=struct.Party(fighter=1),
    )
    result = enchantress_ability(world, _UNUSED, "ability", ("goblin",))
    assert result.dungeon.goblin == 1
    assert result.dungeon.potion == 1
    assert not result.ability


def test_beguiler_transforms_two_monsters():
    """Beguiler transforms 2 monsters into 1 potion when available."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(goblin=2, skeleton=1),
        party=struct.Party(fighter=1),
    )
    result = beguiler_ability(world, _UNUSED, "ability", ("goblin", "skeleton"))
    assert result.dungeon.goblin == 1
    assert result.dungeon.skeleton == 0
    assert result.dungeon.potion == 1


def test_beguiler_requires_two_when_available():
    """Beguiler must transform 2 monsters when 2+ available."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(goblin=2, skeleton=1),
        party=struct.Party(fighter=1),
    )
    with pytest.raises(struct.DrollError):
        beguiler_ability(world, _UNUSED, "ability", ("goblin",))


def test_beguiler_rejects_too_many_targets():
    """Beguiler rejects more than 2 targets."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(goblin=2, skeleton=1),
        party=struct.Party(fighter=1),
    )
    with pytest.raises(struct.DrollError):
        beguiler_ability(
            world, _UNUSED, "ability", ("goblin", "skeleton", "goblin")
        )


def test_enchantress_advances_to_beguiler():
    """Enchantress advances to Beguiler at 5+ experience."""
    low_xp = struct.World(experience=4)
    high_xp = struct.World(experience=5)
    assert Enchantress.advance(low_xp) == Enchantress
    assert Enchantress.advance(high_xp) == Beguiler
