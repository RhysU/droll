# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for special module helpers."""

import pytest

from droll import special, struct
from droll.struct import Dungeon, DrollError, Party, make_dungeon, make_party

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


def test_defeats_all_plus_one_additional():
    """Defeats all of one type plus one additional."""
    w = struct.World(
        dungeon=make_dungeon(goblin=2, skeleton=1),
        party=make_party(champion=1),
    )
    result = special.defeat_all_plus_additional(
        w, _UNUSED, Party.CHAMPION, (Dungeon.GOBLIN, Dungeon.SKELETON)
    )
    assert result.dungeon[Dungeon.GOBLIN] == 0
    assert result.dungeon[Dungeon.SKELETON] == 0
    assert result.party[Party.CHAMPION] == 0


def test_defeat_all_no_additional_when_cleared():
    """No additional needed when monsters cleared."""
    w = struct.World(
        dungeon=make_dungeon(goblin=2),
        party=make_party(champion=1),
    )
    result = special.defeat_all_plus_additional(
        w, _UNUSED, Party.CHAMPION, (Dungeon.GOBLIN,)
    )
    assert result.dungeon[Dungeon.GOBLIN] == 0


def test_defeat_all_rejects_extra_additional():
    """Rejects more than one additional target."""
    w = struct.World(
        dungeon=make_dungeon(goblin=1, skeleton=2),
        party=make_party(champion=1),
    )
    with pytest.raises(DrollError):
        special.defeat_all_plus_additional(
            w,
            _UNUSED,
            Party.CHAMPION,
            (Dungeon.GOBLIN, Dungeon.SKELETON, Dungeon.SKELETON),
        )


def test_defeat_all_requires_additional_when_monsters_remain():
    """Requires additional target when monsters remain."""
    w = struct.World(
        dungeon=make_dungeon(goblin=1, skeleton=1),
        party=make_party(champion=1),
    )
    with pytest.raises(DrollError):
        special.defeat_all_plus_additional(
            w,
            _UNUSED,
            Party.CHAMPION,
            (Dungeon.GOBLIN,),
        )


def test_defeats_one_plus_one_additional():
    """Defeats one of primary target plus one additional."""
    w = struct.World(
        dungeon=make_dungeon(goblin=2, skeleton=1),
        party=make_party(champion=1),
    )
    result = special.defeat_one_plus_additional(
        w, _UNUSED, Party.CHAMPION, (Dungeon.GOBLIN, Dungeon.SKELETON)
    )
    assert result.dungeon[Dungeon.GOBLIN] == 1
    assert result.dungeon[Dungeon.SKELETON] == 0
    assert result.party[Party.CHAMPION] == 0


def test_defeat_one_no_additional_when_cleared():
    """No additional needed when all monsters cleared after defeating one."""
    w = struct.World(
        dungeon=make_dungeon(goblin=1),
        party=make_party(fighter=1),
    )
    result = special.defeat_one_plus_additional(
        w, _UNUSED, Party.FIGHTER, (Dungeon.GOBLIN,)
    )
    assert result.dungeon[Dungeon.GOBLIN] == 0
    assert result.party[Party.FIGHTER] == 0


def test_defeat_one_rejects_additional_when_cleared():
    """Rejects additional target when all monsters already cleared."""
    w = struct.World(
        dungeon=make_dungeon(goblin=1),
        party=make_party(fighter=1),
    )
    with pytest.raises(DrollError):
        special.defeat_one_plus_additional(
            w, _UNUSED, Party.FIGHTER, (Dungeon.GOBLIN, Dungeon.SKELETON)
        )


def test_defeat_one_requires_additional_when_monsters_remain():
    """Requires additional target when monsters remain after defeating one."""
    w = struct.World(
        dungeon=make_dungeon(goblin=1, skeleton=1),
        party=make_party(fighter=1),
    )
    with pytest.raises(DrollError):
        special.defeat_one_plus_additional(w, _UNUSED, Party.FIGHTER, (Dungeon.GOBLIN,))


def test_defeat_one_rejects_extra_additional():
    """Rejects more than one additional target."""
    w = struct.World(
        dungeon=make_dungeon(goblin=1, skeleton=1, ooze=1),
        party=make_party(champion=1),
    )
    with pytest.raises(DrollError):
        special.defeat_one_plus_additional(
            w,
            _UNUSED,
            Party.CHAMPION,
            (Dungeon.GOBLIN, Dungeon.SKELETON, Dungeon.OOZE),
        )


def test_defeat_one_only_decrements_one_of_primary():
    """Defeats only one of the primary target, not all."""
    w = struct.World(
        dungeon=make_dungeon(goblin=3, skeleton=1),
        party=make_party(champion=1),
    )
    result = special.defeat_one_plus_additional(
        w, _UNUSED, Party.CHAMPION, (Dungeon.GOBLIN, Dungeon.SKELETON)
    )
    assert result.dungeon[Dungeon.GOBLIN] == 2
    assert result.dungeon[Dungeon.SKELETON] == 0
    assert result.party[Party.CHAMPION] == 0


def test_convert_dungeon_to_party_up_to_max_count():
    """Converts min(available, max_count) dungeon dice to party dice."""
    w = struct.World(
        dungeon=make_dungeon(goblin=3),
        party=make_party(fighter=1),
    )
    result = special.convert_dungeon_to_party(
        w, source=Dungeon.GOBLIN, destination=Party.THIEF, max_count=2
    )
    assert result.dungeon[Dungeon.GOBLIN] == 1
    assert result.party[Party.THIEF] == 2
    assert result.regroup.discard[Party.THIEF] == 2


def test_convert_dungeon_to_party_zero_source_raises():
    """Raises DrollError when zero of the requested source exist in dungeon."""
    w = struct.World(
        dungeon=make_dungeon(skeleton=2),
        party=make_party(),
    )
    with pytest.raises(DrollError):
        special.convert_dungeon_to_party(
            w, source=Dungeon.GOBLIN, destination=Party.THIEF, max_count=1
        )


def test_convert_dungeon_to_party_fewer_when_limited():
    """Converts only available count when fewer than max_count."""
    w = struct.World(
        dungeon=make_dungeon(skeleton=1),
        party=make_party(),
    )
    result = special.convert_dungeon_to_party(
        w, source=Dungeon.SKELETON, destination=Party.FIGHTER, max_count=2
    )
    assert result.dungeon[Dungeon.SKELETON] == 0
    assert result.party[Party.FIGHTER] == 1
    assert result.regroup.discard[Party.FIGHTER] == 1
