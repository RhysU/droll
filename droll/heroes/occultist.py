# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Occultist advancing to Necromancer."""
from dataclasses import replace
import functools
import typing

from .. import action
from .. import dice
from .. import error
from .. import struct
from ..player import Default


def _occultist_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: typing.Optional[str] = None,
) -> struct.World:
    """Transform 1 skeleton into 1 fighter, discarding it at next regroup."""
    # Assume target is skeleton when not provided
    if target and target != "skeleton":
        raise error.DrollError("Ability can only target 1 skeleton")

    # Change 1 skeleton into 1 fighter
    dungeon = action.decrement_dungeon(world.dungeon, "skeleton")
    party = action.increment_party(world.party, "fighter")

    # Discarding if unused at the next regroup phase
    regroup = world.regroup
    discard = regroup.discard
    discard = replace(discard, fighter=discard.fighter + 1)
    regroup = replace(regroup, discard=discard)

    world = replace(world, dungeon=dungeon, party=party, regroup=regroup)
    return action.consume_ability(world)


def _necromancer_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: typing.Optional[str] = None,
    *extra_targets: str,
) -> struct.World:
    """Transform 2 skeletons into fighters, discarding them at next regroup."""
    # Assume targets are skeletons when not provided
    if target and target != "skeleton":
        raise error.DrollError("Ability can only target skeletons")
    if extra_targets and extra_targets[0] != "skeleton":
        raise error.DrollError("Ability can only target skeletons")
    if len(extra_targets) > 1:
        raise error.DrollError("At most 2 targets can be changed.")

    dungeon = world.dungeon
    party = world.party
    regroup = world.regroup
    discard = regroup.discard

    # Always transform 2 when 2 are available
    if dungeon.skeleton >= 2:
        dungeon = action.decrement_dungeon(dungeon, "skeleton")
        dungeon = action.decrement_dungeon(dungeon, "skeleton")
        party = action.increment_party(party, "fighter")
        party = action.increment_party(party, "fighter")
        discard = replace(discard, fighter=discard.fighter + 2)
    else:
        dungeon = action.decrement_dungeon(dungeon, "skeleton")
        party = action.increment_party(party, "fighter")
        discard = replace(discard, fighter=discard.fighter + 1)

    regroup = replace(regroup, discard=discard)
    world = replace(world, dungeon=dungeon, party=party, regroup=regroup)
    return action.consume_ability(world)


# Cleric/mage are interchangeable for dragon defeats
_occultist_defeat_dragon = functools.partial(
    action.defeat_dragon,
    _defeat_dragon_heroes=functools.partial(
        action.defeat_dragon_heroes_interchangeable,
        _interchangeable=frozenset({"cleric", "mage"}),
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
