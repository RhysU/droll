# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Knight advancing to DragonSlayer."""

from dataclasses import replace
from functools import partial

from .. import dice, regular
from ..ability import dragonslayer_ability, knight_ability
from ..player import Default
from ..struct import Dungeon, Party, RandRange, PartyState, Regroup, frozen

__all__ = (
    "DragonSlayer",
    "Knight",
)


def _knight_roll_party(
    count: int, randrange: RandRange
) -> tuple[PartyState, Regroup]:
    """Roll a new Party, changing all Scrolls into Champions."""
    default, regroup = dice.roll_party(dice=count, randrange=randrange)
    return (
        frozen({**default, Party.SCROLL: 0, Party.CHAMPION: default[Party.CHAMPION] + default[Party.SCROLL]}),
        regroup,
    )


# DragonSlayer only needs 2 distinct heroes instead of 3
_dragonslayer_defeat_dragon = partial(
    regular.defeat_dragon,
    hero_validator=partial(regular.defeat_dragon_heroes, required=2),
)

# Defined in terms of Default, not Knight, to permit advance(...) closure
DragonSlayer = replace(
    Default,
    name="DragonSlayer",
    ability=dragonslayer_ability,
    advance=(lambda _: DragonSlayer),
    roll=replace(Default.roll, party=_knight_roll_party),
    party=frozen({
        Party.FIGHTER: frozen({
            **Default.party[Party.FIGHTER],
            Dungeon.DRAGON: _dragonslayer_defeat_dragon,
        }),
        Party.CLERIC: frozen({
            **Default.party[Party.CLERIC],
            Dungeon.DRAGON: _dragonslayer_defeat_dragon,
        }),
        Party.MAGE: frozen({
            **Default.party[Party.MAGE],
            Dungeon.DRAGON: _dragonslayer_defeat_dragon,
        }),
        Party.THIEF: frozen({
            **Default.party[Party.THIEF],
            Dungeon.DRAGON: _dragonslayer_defeat_dragon,
        }),
        Party.CHAMPION: frozen({
            **Default.party[Party.CHAMPION],
            Dungeon.DRAGON: _dragonslayer_defeat_dragon,
        }),
        Party.SCROLL: frozen({
            **Default.party[Party.SCROLL],
            Dungeon.DRAGON: _dragonslayer_defeat_dragon,
        }),
    }),
)

# Defined after DragonSlayer to permit advance(...) closure
Knight = replace(
    Default,
    name="Knight",
    ability=knight_ability,
    advance=(lambda world: Knight if world.experience < 5 else DragonSlayer),
    roll=replace(Default.roll, party=_knight_roll_party),
)
