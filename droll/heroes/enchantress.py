# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Beguiler advancing to Enchantress."""
from dataclasses import replace
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
    dungeon = action.decrement_target(dungeon, target)
    dungeon = action.increment_target(dungeon, "potion")
    return action.consume_ability(replace(game, dungeon=dungeon))


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
    dungeon = action.decrement_target(dungeon, target)
    if len(extra_targets) > 1:
        raise error.DrollError("At most 2 targets can be transformed.")
    elif len(extra_targets) == 1:
        dungeon = action.decrement_target(dungeon, extra_targets[0])
    elif not world.defeated_monsters(dungeon):
        assert len(extra_targets) == 0
        raise error.DrollError("Require 2 targets when 2+ available.")
    else:
        pass
    dungeon = action.increment_target(dungeon, "potion")
    return action.consume_ability(replace(game, dungeon=dungeon))


# Scrolls act as wildcards for dragon defeats
_beguiler_defeat_dragon = functools.partial(
    action.defeat_dragon,
    _defeat_dragon_heroes=functools.partial(
        action.defeat_dragon_heroes_wildcard, _wildcard={"scroll"}
    ),
)

# Defined in terms of Default, not Enchantress, to permit advance(...) closure
Beguiler = replace(
    Default,
    name="Beguiler",
    ability=beguiler_ability,
    advance=(lambda _: Beguiler),
    party=replace(
        Default.party,
        # Scrolls act offensively (defeat enemies, not re-roll)
        scroll=struct.Dungeon(
            goblin=action.defeat_all,
            skeleton=action.defeat_all,
            ooze=action.defeat_all,
            chest=action.open_all,
            potion=action.quaff,
            dragon=_beguiler_defeat_dragon,
        ),
    ),
)

# Defined after Beguiler to permit advance(...) closure
Enchantress = replace(
    Default,
    name="Enchantress",
    ability=enchantress_ability,
    advance=(lambda world: Enchantress if world.experience < 5 else Beguiler),
    party=Beguiler.party,
)
