# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Half-Goblin advancing to Chieftain."""
from __future__ import annotations

from dataclasses import replace
import functools

from .. import action
from .. import dice
from ..error import DrollError
from .. import struct
from .. import world
from ..player import Default

__all__ = (
    "Chieftain",
    "HalfGoblin",
)


def _halfgoblin_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: str | None = None,
) -> struct.World:
    """Transform 1 goblin into 1 thief, discarding it at next regroup."""
    if target and target != "goblin":
        raise DrollError("Ability can only target 1 goblin.")
    world = action.convert_dungeon_to_party(
        world, source="goblin", destination="thief", max_count=1
    )
    return action.consume_ability(world)


def _chieftain_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: str | None = None,
    *extra_targets: str,
) -> struct.World:
    """Transform 2 goblins into thieves, discarding them at next regroup."""
    if target and target != "goblin":
        raise DrollError("Ability can only target goblins.")
    if extra_targets and extra_targets[0] != "goblin":
        raise DrollError("Ability can only target goblins.")
    if len(extra_targets) > 1:
        raise DrollError("At most 2 targets can be changed.")
    world = action.convert_dungeon_to_party(
        world, source="goblin", destination="thief", max_count=2
    )
    return action.consume_ability(world)


# You may open chests and quaff potions at any time during the monster phase
_halfgoblin_open_one = functools.partial(
    action.open_one,
    _after_monsters=False,
)
_halfgoblin_open_all = functools.partial(
    action.open_all,
    _after_monsters=False,
)
_halfgoblin_quaff = functools.partial(
    action.quaff,
    _after_monsters=False,
)

# Defined in terms of Default, not Half-Goblin, to permit advance(...) closure
Chieftain = replace(
    Default,
    name="Chieftain",
    ability=_chieftain_ability,
    advance=(lambda _: Chieftain),
    party=replace(
        Default.party,
        fighter=replace(
            Default.party.fighter,
            chest=_halfgoblin_open_one,
            potion=_halfgoblin_quaff,
        ),
        cleric=replace(
            Default.party.cleric,
            chest=_halfgoblin_open_one,
            potion=_halfgoblin_quaff,
        ),
        mage=replace(
            Default.party.mage,
            chest=_halfgoblin_open_one,
            potion=_halfgoblin_quaff,
        ),
        thief=replace(
            Default.party.thief,
            chest=_halfgoblin_open_all,
            potion=_halfgoblin_quaff,
        ),
        champion=replace(
            Default.party.champion,
            chest=_halfgoblin_open_all,
            potion=_halfgoblin_quaff,
        ),
        scroll=replace(
            Default.party.scroll,
            potion=_halfgoblin_quaff,
        ),
    ),
)

# Defined after Chieftain to permit advance(...) closure
HalfGoblin = replace(
    Default,
    name="HalfGoblin",
    ability=_halfgoblin_ability,
    advance=(lambda world: HalfGoblin if world.experience < 5 else Chieftain),
    party=Chieftain.party,
)
