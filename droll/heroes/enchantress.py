# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Beguiler advancing to Enchantress."""
import functools
import typing

from .. import action
from .. import dice
from .. import error
from .. import struct
from .. import world
from ..player import Default


def enchantress_ability(
    game: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: typing.Optional[str] = None,
) -> struct.World:
    """Transform exactly 1 monster into 1 potion."""
    dungeon = game.dungeon
    dungeon = action.__decrement_target(dungeon, target)
    dungeon = action.__increment_target(dungeon, "potion")
    return action.consume_ability(game._replace(dungeon=dungeon))


def beguiler_ability(
    game: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: typing.Optional[str] = None,
    *extra_targets: str,
) -> struct.World:
    """Transform at most 2 monsters into 1 potion.

    Requires transforming 2 monsters when 2+ monsters available."""
    dungeon = game.dungeon
    dungeon = action.__decrement_target(dungeon, target)
    if len(extra_targets) > 1:
        raise error.DrollError("At most 2 targets can be transformed.")
    elif len(extra_targets) == 1:
        dungeon = action.__decrement_target(dungeon, extra_targets[0])
    elif not world.defeated_monsters(dungeon):
        assert len(extra_targets) == 0
        raise error.DrollError("Require 2 targets when 2+ available.")
    else:
        pass
    dungeon = action.__increment_target(dungeon, "potion")
    return action.consume_ability(game._replace(dungeon=dungeon))


@functools.wraps(action.defeat_dragon)
def beguiler_defeat_dragon(*args, **kwargs):
    return action.defeat_dragon(
        *args, **kwargs, _defeat_dragon_heroes=beguiler_defeat_dragon_heroes
    )


@functools.wraps(action.defeat_dragon_heroes_interchangeable)
def beguiler_defeat_dragon_heroes(*args, **kwargs):
    return action.defeat_dragon_heroes_wildcard(
        *args, **kwargs, _wildcard={"scroll"}
    )


# Defined in terms of Default, not Crusader, to permit advance(...) closure
Beguiler = Default._replace(
    name="Beguiler",
    ability=beguiler_ability,
    advance=(lambda _: Beguiler),  # Cannot advance further
    party=Default.party._replace(
        # Scrolls may be used as any companion so assume "offensive" usage
        # That is, assumes user wants to defeat enemies not re-roll them
        scroll=struct.Dungeon(
            goblin=action.defeat_all,
            skeleton=action.defeat_all,
            ooze=action.defeat_all,
            chest=action.open_all,
            potion=action.quaff,
            dragon=beguiler_defeat_dragon,
        ),
    ),
)

# Defined after Beguiler to permit advance(...) closure
Enchantress = Default._replace(
    name="Enchantress",
    ability=enchantress_ability,
    advance=(lambda world: Enchantress if world.experience < 5 else Beguiler),
    party=Beguiler.party,
)
