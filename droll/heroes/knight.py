# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Knight advancing to DragonSlayer."""

from dataclasses import replace
from functools import partial

from .. import dice, regular, struct
from ..ability import knight_ability
from ..player import Default

__all__ = (
    "DragonSlayer",
    "Knight",
)


def _knight_roll_party(
    count: int, randrange: struct.RandRange
) -> tuple[struct.Party, struct.Regroup]:
    """Roll a new Party, changing all Scrolls into Champions."""
    default, regroup = dice.roll_party(dice=count, randrange=randrange)
    return (
        replace(default, scroll=0, champion=default.champion + default.scroll),
        regroup,
    )


# DragonSlayer only needs 2 distinct heroes instead of 3
_dragonslayer_defeat_dragon = partial(
    regular.defeat_dragon,
    defeat_dragon_heroes=partial(regular.defeat_dragon_heroes, required=2),
)

# Defined in terms of Default, not Knight, to permit advance(...) closure
DragonSlayer = replace(
    Default,
    name="DragonSlayer",
    ability=knight_ability,
    advance=(lambda _: DragonSlayer),
    roll=replace(Default.roll, party=_knight_roll_party),
    party=struct.Party(
        fighter=replace(
            Default.party.fighter,
            dragon=_dragonslayer_defeat_dragon,
        ),
        cleric=replace(
            Default.party.cleric,
            dragon=_dragonslayer_defeat_dragon,
        ),
        mage=replace(
            Default.party.mage,
            dragon=_dragonslayer_defeat_dragon,
        ),
        thief=replace(
            Default.party.thief,
            dragon=_dragonslayer_defeat_dragon,
        ),
        champion=replace(
            Default.party.champion,
            dragon=_dragonslayer_defeat_dragon,
        ),
        scroll=replace(
            Default.party.scroll,
            dragon=_dragonslayer_defeat_dragon,
        ),
    ),
)

# Defined after DragonSlayer to permit advance(...) closure
Knight = replace(
    Default,
    name="Knight",
    ability=knight_ability,
    advance=(lambda world: Knight if world.experience < 5 else DragonSlayer),
    roll=replace(Default.roll, party=_knight_roll_party),
)
