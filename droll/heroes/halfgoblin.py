# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Half-Goblin advancing to Chieftain."""
from dataclasses import replace
import functools
import typing

from .. import action
from .. import dice
from .. import error
from .. import struct
from .. import world
from ..player import Default


def _halfgoblin_ability(
    game: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: typing.Optional[str] = None,
) -> struct.World:
    """Transform 1 goblin into 1 thief, discarding it at next regroup."""
    # Assume target is goblin when not provided
    if target and target != "goblin":
        raise error.DrollError("Ability can only target 1 goblin")

    # Change 1 goblin into 1 thief
    dungeon = action.decrement_target(game.dungeon, "goblin")
    party = action.increment_target(game.party, "thief")

    # Discarding if unused at the next regroup phase
    regroup = game.regroup
    discard = regroup.discard
    discard = replace(discard, thief=getattr(discard, "thief", 0) + 1)
    regroup = replace(regroup, discard=discard)

    game = replace(game, dungeon=dungeon, party=party, regroup=regroup)
    return action.consume_ability(game)


def _chieftain_ability(
    game: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: typing.Optional[str] = None,
    *extra_targets: str,
) -> struct.World:
    """Transform 2 goblins into thieves, discarding them at next regroup."""
    # Assume targets are goblins when not provided
    if target and target != "goblin":
        raise error.DrollError("Ability can only target goblins")
    if extra_targets and extra_targets[0] != "goblin":
        raise error.DrollError("Ability can only target goblins")
    if len(extra_targets) > 1:
        raise error.DrollError("At most 2 targets can be changed.")

    dungeon = game.dungeon
    party = game.party
    regroup = game.regroup
    discard = regroup.discard

    # Always transform 2 when 2 are available
    if dungeon.goblin >= 2:
        dungeon = action.decrement_target(dungeon, "goblin")
        dungeon = action.decrement_target(dungeon, "goblin")
        party = action.increment_target(party, "thief")
        party = action.increment_target(party, "thief")
        discard = replace(discard, thief=getattr(discard, "thief", 0) + 2)
    else:
        dungeon = action.decrement_target(dungeon, "goblin")
        party = action.increment_target(party, "thief")
        discard = replace(discard, thief=getattr(discard, "thief", 0) + 1)

    regroup = replace(regroup, discard=discard)
    game = replace(game, dungeon=dungeon, party=party, regroup=regroup)
    return action.consume_ability(game)


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
