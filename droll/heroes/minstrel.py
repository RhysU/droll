# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Minstrel advancing to Bard."""
import functools
import typing

from .. import action
from .. import dice
from .. import error
from .. import struct
from ..player import Default


def minstrel_ability(
        game: struct.World, randrange: dice.RandRange, noun: str,
        target: typing.Optional[str] = None,
        *,
        _acceptable_targets: typing.Set[str] = {'fighter', 'mage'}
) -> struct.World:
    """Minstrel may discard all dragon dice."""
    target = 'dragon' if target is None else target
    if target is not 'dragon':
        raise error.DrollError('Can only discard {} dice'
                               .format(target))
    return action.consume_ability(game._replace(
        dungeon=action.__eliminate_targets(game.dungeon, target)
    ))


@functools.wraps(action.defeat_dragon)
def minstrel_defeat_dragon(*args, **kwargs):
    return action.defeat_dragon(
        *args,
        **kwargs,
        _defeat_dragon_heroes=minstrel_defeat_dragon_heroes)


@functools.wraps(action.defeat_dragon_heroes_interchangeable)
def minstrel_defeat_dragon_heroes(*args, **kwargs):
    return action.defeat_dragon_heroes_interchangeable(
        *args,
        **kwargs,
        _interchangeable={'mage', 'thief'})


# Building block common to both Bard and Minstrel
_Minstrel_Party = Default.party._replace(
    fighter=Default.party.fighter._replace(
        dragon=minstrel_defeat_dragon,
    ),
    cleric=Default.party.cleric._replace(
        dragon=minstrel_defeat_dragon,
    ),
    mage=Default.party.mage._replace(
        # Mages usable as thieves implies mage.chest as if a thief
        chest=Default.party.thief.chest,
        dragon=minstrel_defeat_dragon,
    ),
    thief=Default.party.thief._replace(
        # Thieves usable as mages implies thief.ooze as if a mage
        ooze=Default.party.mage.ooze,
        dragon=minstrel_defeat_dragon,
    ),
    champion=Default.party.champion._replace(
        dragon=minstrel_defeat_dragon,
    ),
    scroll=Default.party.scroll._replace(
        dragon=minstrel_defeat_dragon,
    ),
)

# Defined in terms of Default, not Minstrel, to permit advance(...) closure
Bard = Default._replace(
    ability=minstrel_ability,
    advance=(lambda _: Bard),  # Cannot advance further
    party=_Minstrel_Party._replace(
        champion=_Minstrel_Party.champion._replace(
            # Champions defeat one additional monster when attacking monsters
            goblin=action.defeat_all_plus_additional,
            skeleton=action.defeat_all_plus_additional,
            ooze=action.defeat_all_plus_additional,
        ),
    )
)

# Defined after Bard to permit advance(...) closure
Minstrel = Default._replace(
    ability=minstrel_ability,
    advance=(lambda world: Minstrel if world.experience < 5 else Bard),
    party=_Minstrel_Party,
)
