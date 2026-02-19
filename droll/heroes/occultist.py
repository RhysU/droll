# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Occultist advancing to Necromancer."""

from dataclasses import replace
import functools
from typing import Optional

from .. import action
from .. import dice
from ..error import DrollError
from .. import struct
from ..player import Default

__all__ = (
    "Necromancer",
    "Occultist",
)


def _occultist_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: Optional[str] = None,
) -> struct.World:
    """Transform 1 skeleton into 1 fighter, discarding it at next regroup."""
    if target and target != "skeleton":
        raise DrollError("Ability can only target 1 skeleton.")
    world = action.convert_dungeon_to_party(
        world, source="skeleton", destination="fighter", max_count=1
    )
    return action.consume_ability(world)


def _necromancer_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: Optional[str] = None,
    *extra_targets: str,
) -> struct.World:
    """Transform 2 skeletons into fighters, discarding them at next regroup."""
    if target and target != "skeleton":
        raise DrollError("Ability can only target skeletons.")
    if extra_targets and extra_targets[0] != "skeleton":
        raise DrollError("Ability can only target skeletons.")
    if len(extra_targets) > 1:
        raise DrollError("At most 2 targets can be changed.")
    world = action.convert_dungeon_to_party(
        world, source="skeleton", destination="fighter", max_count=2
    )
    return action.consume_ability(world)


# Cleric/mage are interchangeable for dragon defeats
_occultist_defeat_dragon = functools.partial(
    action.defeat_dragon,
    defeat_dragon_heroes=functools.partial(
        action.defeat_dragon_heroes_interchangeable,
        interchangeable=frozenset({"cleric", "mage"}),
    ),
)

# Defined in terms of Default, not Occultist, to permit advance(...) closure
Necromancer = replace(
    Default,
    name="Necromancer",
    ability=_necromancer_ability,
    advance=(lambda _: Necromancer),
    party=replace(
        Default.party,
        fighter=replace(
            Default.party.fighter,
            dragon=_occultist_defeat_dragon,
        ),
        cleric=replace(
            Default.party.cleric,
            dragon=_occultist_defeat_dragon,
            ooze=Default.party.mage.ooze,
        ),
        mage=replace(
            Default.party.mage,
            dragon=_occultist_defeat_dragon,
            skeleton=Default.party.cleric.skeleton,
        ),
        thief=replace(
            Default.party.thief,
            dragon=_occultist_defeat_dragon,
        ),
        champion=replace(
            Default.party.champion,
            dragon=_occultist_defeat_dragon,
        ),
        scroll=replace(
            Default.party.scroll,
            dragon=_occultist_defeat_dragon,
        ),
    ),
)

# Defined after Necromancer to permit advance(...) closure
Occultist = replace(
    Default,
    name="Occultist",
    ability=_occultist_ability,
    advance=(lambda world: Occultist if world.experience < 5 else Necromancer),
    party=Necromancer.party,
)
