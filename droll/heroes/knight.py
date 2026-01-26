# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Knight advancing to DragonSlayer."""
import functools

from .. import action
from .. import dice
from .. import struct
from ..player import Default


def knight_roll_party(count: int, randrange: dice.RandRange) -> struct.Party:
    """Roll a new Party, changing all Scrolls into Champions."""
    default = dice.roll_party(dice=count, randrange=randrange)
    return default._replace(
        scroll=0, champion=default.champion + default.scroll
    )


def knight_bait_dragon(*args, **kwargs):
    """Convert all monster faces into dragon dice."""
    return action.consume_ability(
        action.bait_dragon(*args, _require_treasure=False, **kwargs)
    )


# DragonSlayer only needs 2 distinct heroes instead of 3
_dragonslayer_defeat_dragon = functools.partial(
    action.defeat_dragon,
    _defeat_dragon_heroes=functools.partial(
        action.defeat_dragon_heroes, _distinct_heroes=2
    ),
)

# Defined in terms of Default, not Knight, to permit advance(...) closure
DragonSlayer = Default._replace(
    name="DragonSlayer",
    ability=knight_bait_dragon,
    advance=(lambda _: DragonSlayer),
    roll=Default.roll._replace(party=knight_roll_party),
    party=struct.update_party_dragon(
        Default.party, _dragonslayer_defeat_dragon
    ),
)

# Defined after DragonSlayer to permit advance(...) closure
Knight = Default._replace(
    name="Knight",
    ability=knight_bait_dragon,
    advance=(lambda world: Knight if world.experience < 5 else DragonSlayer),
    roll=Default.roll._replace(party=knight_roll_party),
)
