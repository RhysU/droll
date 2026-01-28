# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Minstrel advancing to Bard."""
from dataclasses import replace
import functools
import typing

from .. import action
from .. import dice
from .. import error
from .. import struct
from ..player import Default


def minstrel_ability(
    game: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: typing.Optional[str] = None,
) -> struct.World:
    """May discard all dragon dice."""
    target = "dragon" if target is None else target
    if target != "dragon":
        raise error.DrollError("Can only discard {} dice".format(target))
    return action.consume_ability(
        replace(game, dungeon=action._eliminate_targets(game.dungeon, target))
    )


# Mage/thief are interchangeable for dragon defeats
_minstrel_defeat_dragon = functools.partial(
    action.defeat_dragon,
    _defeat_dragon_heroes=functools.partial(
        action.defeat_dragon_heroes_interchangeable,
        _interchangeable={"mage", "thief"},
    ),
)

# Building block: dragon defeat + mage/thief interchangeability in combat
_Minstrel_Party = replace(
    struct.update_party_dragon(Default.party, _minstrel_defeat_dragon),
    mage=replace(Default.party.mage, chest=Default.party.thief.chest),
    thief=replace(Default.party.thief, ooze=Default.party.mage.ooze),
)

# Defined in terms of Default, not Minstrel, to permit advance(...) closure
Bard = replace(
    Default,
    name="Bard",
    ability=minstrel_ability,
    advance=(lambda _: Bard),  # Cannot advance further
    party=replace(
        _Minstrel_Party,
        champion=replace(
            _Minstrel_Party.champion,
            # Champions defeat one additional monster when attacking monsters
            goblin=action.defeat_all_plus_additional,
            skeleton=action.defeat_all_plus_additional,
            ooze=action.defeat_all_plus_additional,
        ),
    ),
)

# Defined after Bard to permit advance(...) closure
Minstrel = replace(
    Default,
    name="Minstrel",
    ability=minstrel_ability,
    advance=(lambda world: Minstrel if world.experience < 5 else Bard),
    party=_Minstrel_Party,
)
