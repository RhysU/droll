# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Minstrel advancing to Bard."""
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
    """Minstrel may discard all dragon dice."""
    target = "dragon" if target is None else target
    if target != "dragon":
        raise error.DrollError("Can only discard {} dice".format(target))
    return action.consume_ability(
        game._replace(dungeon=action._eliminate_targets(game.dungeon, target))
    )


# Mage/thief are interchangeable for dragon defeats
_minstrel_defeat_dragon = action.make_defeat_dragon(
    action.make_dragon_validator_interchangeable({"mage", "thief"})
)

# Building block: dragon defeat + mage/thief interchangeability in combat
_Minstrel_Party = action.update_party_dragon(
    Default.party, _minstrel_defeat_dragon
)._replace(
    mage=Default.party.mage._replace(
        chest=Default.party.thief.chest,  # Mages open all chests like thieves
        dragon=_minstrel_defeat_dragon,
    ),
    thief=Default.party.thief._replace(
        ooze=Default.party.mage.ooze,  # Thieves defeat all oozes like mages
        dragon=_minstrel_defeat_dragon,
    ),
)

# Defined in terms of Default, not Minstrel, to permit advance(...) closure
Bard = Default._replace(
    name="Bard",
    ability=minstrel_ability,
    advance=(lambda _: Bard),  # Cannot advance further
    party=_Minstrel_Party._replace(
        champion=_Minstrel_Party.champion._replace(
            # Champions defeat one additional monster when attacking monsters
            goblin=action.defeat_all_plus_additional,
            skeleton=action.defeat_all_plus_additional,
            ooze=action.defeat_all_plus_additional,
        )
    ),
)

# Defined after Bard to permit advance(...) closure
Minstrel = Default._replace(
    name="Minstrel",
    ability=minstrel_ability,
    advance=(lambda world: Minstrel if world.experience < 5 else Bard),
    party=_Minstrel_Party,
)
