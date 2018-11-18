# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Spellsword advancing to Battlemage."""
import functools
import typing

from .. import action
from .. import dice
from .. import error
from .. import struct
from ..player import Default


def spellsword_ability(
        game: struct.World, randrange: dice.RandRange, noun: str,
        target: typing.Optional[str] = None,
        *,
        _acceptable_targets: typing.Set[str] = {'fighter', 'mage'}
) -> struct.World:
    """Spellsword usable as a fighter or a mage, adding one hero to party.

    Optionally, specify 'fighter' or 'mage' to select which to choose."""
    if target is None:
        target = next(iter(sorted(_acceptable_targets)))
    if target not in _acceptable_targets:
        raise error.DrollError('Target {} not one of {}'
                               .format(target, _acceptable_targets))
    return action.consume_ability(game._replace(
        party=action.__increment_hero(game.party, target)
    ))


@functools.wraps(action.defeat_dragon)
def spellsword_defeat_dragon(*args, **kwargs):
    return action.defeat_dragon(
        *args,
        **kwargs,
        _defeat_dragon_heroes=spellsword_defeat_dragon_heroes)


@functools.wraps(action.defeat_dragon_heroes_interchangeable)
def spellsword_defeat_dragon_heroes(*args, **kwargs):
    return action.defeat_dragon_heroes_interchangeable(
        *args,
        **kwargs,
        _interchangeable={'fighter', 'mage'})


def battlemage_ability(
        game: struct.World, randrange: dice.RandRange, noun: str,
        target: typing.Optional[str] = None,
        *,
        _acceptable_targets: typing.Set[str] = {'fighter', 'mage'}
) -> struct.World:
    """Discard all monsters, chests, potions, and dice in the dragon's lair."""
    if target is not None:
        raise error.DrollError('No targets accepted for {}'.format(noun))
    return action.consume_ability(game._replace(
        dungeon=struct.Dungeon(*([0] * len(struct.Dungeon._fields))),
    ))


# Defined in terms of Default, not Spellsword, to permit advance(...) closure
Battlemage = Default._replace(
    ability=battlemage_ability,
    advance=(lambda _: Battlemage),  # Cannot advance further
    party=Default.party._replace(
        fighter=Default.party.fighter._replace(
            # Fighters usable as mages implies fighter.ooze as if a mage
            ooze=Default.party.mage.ooze,
            dragon=spellsword_defeat_dragon,
        ),
        cleric=Default.party.cleric._replace(
            dragon=spellsword_defeat_dragon,
        ),
        mage=Default.party.mage._replace(
            # Mages usable as fighters implies mage.goblin as if a fighter
            goblin=Default.party.fighter.goblin,
            dragon=spellsword_defeat_dragon,
        ),
        thief=Default.party.thief._replace(
            dragon=spellsword_defeat_dragon,
        ),
        champion=Default.party.champion._replace(
            dragon=spellsword_defeat_dragon,
        ),
        scroll=Default.party.scroll._replace(
            dragon=spellsword_defeat_dragon,
        ),
    )
)

# Defined after Battlemage to permit advance(...) closure
Spellsword = Default._replace(
    ability=spellsword_ability,
    advance=(lambda world: Spellsword if world.experience < 5 else Battlemage),
    party=Battlemage.party,
)
