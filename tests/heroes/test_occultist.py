# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Occultist/Necromancer hero abilities."""

import pytest

from droll import struct
from droll.ability import necromancer_ability, occultist_ability
from droll.heroes.occultist import Necromancer, Occultist

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


def test_occultist_transforms_skeleton_to_fighter():
    """Occultist transforms 1 skeleton into 1 fighter."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(goblin=1, skeleton=2),
        party=struct.Party(cleric=1),
    )
    result = occultist_ability(world, _UNUSED, "ability", ("skeleton",))
    # Discard during subsequent regroup phase tested elsewhere
    assert result.dungeon.skeleton == 1
    assert result.party.fighter == 1
    assert not result.ability


def test_occultist_rejects_non_skeleton_target():
    """Occultist ability rejects non-skeleton targets."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(goblin=1, skeleton=1),
        party=struct.Party(cleric=1),
    )
    with pytest.raises(struct.DrollError):
        occultist_ability(world, _UNUSED, "ability", ("goblin",))


def test_occultist_sets_regroup_discard():
    """Occultist marks the created fighter for regroup discard."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(skeleton=1),
        party=struct.Party(cleric=1),
    )
    result = occultist_ability(world, _UNUSED, "ability", ("skeleton",))
    assert result.regroup.discard.fighter == 1


def test_necromancer_transforms_two_skeletons():
    """Necromancer transforms 2 skeletons into 2 fighters when available."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(goblin=1, skeleton=2),
        party=struct.Party(cleric=1),
    )
    result = necromancer_ability(
        world, _UNUSED, "ability", ("skeleton", "skeleton")
    )
    # Discard during subsequent regroup phase tested elsewhere
    assert result.dungeon.skeleton == 0
    assert result.dungeon.goblin == 1
    assert result.party.fighter == 2


def test_necromancer_transforms_one_skeleton():
    """Necromancer transforms 1 skeleton into 1 fighter when 1 available."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(goblin=1, skeleton=1),
        party=struct.Party(cleric=1),
    )
    result = necromancer_ability(
        world,
        _UNUSED,
        "ability",
        ("skeleton",),
    )
    # Discard during subsequent regroup phase tested elsewhere
    assert result.dungeon.skeleton == 0
    assert result.dungeon.goblin == 1
    assert result.party.fighter == 1


def test_necromancer_sets_regroup_discard():
    """Necromancer marks created fighters for regroup discard."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(skeleton=2),
        party=struct.Party(cleric=1),
    )
    result = necromancer_ability(
        world, _UNUSED, "ability", ("skeleton", "skeleton")
    )
    assert result.regroup.discard.fighter == 2


def test_necromancer_rejects_non_skeleton_target():
    """Necromancer ability rejects non-skeleton targets."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(goblin=1, skeleton=2),
        party=struct.Party(cleric=1),
    )
    with pytest.raises(struct.DrollError):
        necromancer_ability(world, _UNUSED, "ability", ("goblin",))


def test_necromancer_rejects_non_skeleton_extra_target():
    """Necromancer ability rejects non-skeleton extra targets."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(goblin=1, skeleton=2),
        party=struct.Party(cleric=1),
    )
    with pytest.raises(struct.DrollError):
        necromancer_ability(world, _UNUSED, "ability", ("skeleton", "goblin"))


def test_necromancer_rejects_too_many_targets():
    """Necromancer rejects more than 2 targets."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(skeleton=3),
        party=struct.Party(cleric=1),
    )
    with pytest.raises(struct.DrollError):
        necromancer_ability(
            world, _UNUSED, "ability", ("skeleton", "skeleton", "skeleton")
        )


def test_occultist_advances_to_necromancer():
    """Occultist advances to Necromancer at 5+ experience."""
    low_xp = struct.World(experience=4)
    high_xp = struct.World(experience=5)
    assert Occultist.advance(low_xp) == Occultist
    assert Occultist.advance(high_xp) == Necromancer


def test_necromancer_does_not_advance():
    """Necromancer does not advance further."""
    high_xp = struct.World(experience=10)
    assert Necromancer.advance(high_xp) == Necromancer
