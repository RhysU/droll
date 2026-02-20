# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for special module helpers."""

import pytest

from droll import special, struct
from droll.struct import DrollError

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


def test_defeats_all_plus_one_additional():
    """Defeats all of one type plus one additional."""
    w = struct.World(
        dungeon=struct.Dungeon(goblin=2, skeleton=1),
        party=struct.Party(champion=1),
    )
    result = special.defeat_all_plus_additional(
        w, _UNUSED, "champion", "goblin", "skeleton"
    )
    assert result.dungeon.goblin == 0
    assert result.dungeon.skeleton == 0
    assert result.party.champion == 0


def test_defeat_all_no_additional_when_cleared():
    """No additional needed when monsters cleared."""
    w = struct.World(
        dungeon=struct.Dungeon(goblin=2),
        party=struct.Party(champion=1),
    )
    result = special.defeat_all_plus_additional(
        w, _UNUSED, "champion", "goblin"
    )
    assert result.dungeon.goblin == 0


def test_defeat_all_rejects_extra_additional():
    """Rejects more than one additional target."""
    w = struct.World(
        dungeon=struct.Dungeon(goblin=1, skeleton=2),
        party=struct.Party(champion=1),
    )
    with pytest.raises(DrollError):
        special.defeat_all_plus_additional(
            w,
            _UNUSED,
            "champion",
            "goblin",
            "skeleton",
            "skeleton",
        )


def test_defeat_all_requires_additional_when_monsters_remain():
    """Requires additional target when monsters remain."""
    w = struct.World(
        dungeon=struct.Dungeon(goblin=1, skeleton=1),
        party=struct.Party(champion=1),
    )
    with pytest.raises(DrollError):
        special.defeat_all_plus_additional(
            w,
            _UNUSED,
            "champion",
            "goblin",
        )


def test_defeats_one_plus_one_additional():
    """Defeats one of primary target plus one additional."""
    w = struct.World(
        dungeon=struct.Dungeon(goblin=2, skeleton=1),
        party=struct.Party(champion=1),
    )
    result = special.defeat_one_plus_additional(
        w, _UNUSED, "champion", "goblin", "skeleton"
    )
    assert result.dungeon.goblin == 1
    assert result.dungeon.skeleton == 0
    assert result.party.champion == 0


def test_defeat_one_no_additional_when_cleared():
    """No additional needed when all monsters cleared after defeating one."""
    w = struct.World(
        dungeon=struct.Dungeon(goblin=1),
        party=struct.Party(fighter=1),
    )
    result = special.defeat_one_plus_additional(
        w, _UNUSED, "fighter", "goblin"
    )
    assert result.dungeon.goblin == 0
    assert result.party.fighter == 0


def test_defeat_one_rejects_additional_when_cleared():
    """Rejects additional target when all monsters already cleared."""
    w = struct.World(
        dungeon=struct.Dungeon(goblin=1),
        party=struct.Party(fighter=1),
    )
    with pytest.raises(DrollError):
        special.defeat_one_plus_additional(
            w, _UNUSED, "fighter", "goblin", "skeleton"
        )


def test_defeat_one_requires_additional_when_monsters_remain():
    """Requires additional target when monsters remain after defeating one."""
    w = struct.World(
        dungeon=struct.Dungeon(goblin=1, skeleton=1),
        party=struct.Party(fighter=1),
    )
    with pytest.raises(DrollError):
        special.defeat_one_plus_additional(w, _UNUSED, "fighter", "goblin")


def test_defeat_one_rejects_extra_additional():
    """Rejects more than one additional target."""
    w = struct.World(
        dungeon=struct.Dungeon(goblin=1, skeleton=1, ooze=1),
        party=struct.Party(champion=1),
    )
    with pytest.raises(DrollError):
        special.defeat_one_plus_additional(
            w,
            _UNUSED,
            "champion",
            "goblin",
            "skeleton",
            "ooze",
        )


def test_defeat_one_only_decrements_one_of_primary():
    """Defeats only one of the primary target, not all."""
    w = struct.World(
        dungeon=struct.Dungeon(goblin=3, skeleton=1),
        party=struct.Party(champion=1),
    )
    result = special.defeat_one_plus_additional(
        w, _UNUSED, "champion", "goblin", "skeleton"
    )
    assert result.dungeon.goblin == 2
    assert result.dungeon.skeleton == 0
    assert result.party.champion == 0


def test_convert_dungeon_to_party_up_to_max_count():
    """Converts min(available, max_count) dungeon dice to party dice."""
    w = struct.World(
        dungeon=struct.Dungeon(goblin=3),
        party=struct.Party(fighter=1),
    )
    result = special.convert_dungeon_to_party(
        w, source="goblin", destination="thief", max_count=2
    )
    assert result.dungeon.goblin == 1
    assert result.party.thief == 2
    assert result.regroup.discard.thief == 2


def test_convert_dungeon_to_party_fewer_when_limited():
    """Converts only available count when fewer than max_count."""
    w = struct.World(
        dungeon=struct.Dungeon(skeleton=1),
        party=struct.Party(),
    )
    result = special.convert_dungeon_to_party(
        w, source="skeleton", destination="fighter", max_count=2
    )
    assert result.dungeon.skeleton == 0
    assert result.party.fighter == 1
    assert result.regroup.discard.fighter == 1
