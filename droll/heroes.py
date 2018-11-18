# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions."""
import collections
import functools
import typing

from . import action
from . import dice
from . import error
from . import struct
from .player import Default


# TODO Implement the following initial characters
# Spellsword -> Battlemage
# Crusader -> Paladin
# Mercenary -> Commander
# Enchantress -> Beguiler
# Occultist -> Necromancer
# Minstrel -> Bard
# Half-goblin -> Chieftan


def knight_roll_party(count: int, randrange: dice.RandRange) -> struct.Party:
    """Roll a new Party, changing all Scrolls into Champions."""
    default = dice.roll_party(dice=count, randrange=randrange)
    return default._replace(
        scroll=0,
        champion=default.champion + default.scroll
    )


@functools.wraps(action.bait_dragon)
def knight_bait_dragon(*args, **kwargs):
    return action.consume_ability(
        action.bait_dragon(*args, _require_treasure=False, **kwargs))


@functools.wraps(action.defeat_dragon_heroes)
def dragonslayer_defeat_dragon_heroes(*args, **kwargs):
    return action.defeat_dragon_heroes(*args, **kwargs, _distinct_heroes=2)


@functools.wraps(action.defeat_dragon)
def dragonslayer_defeat_dragon(*args, **kwargs):
    return action.defeat_dragon(
        *args,
        **kwargs,
        _defeat_dragon_heroes=dragonslayer_defeat_dragon_heroes)


# Defined in terms of Default, not Knight, to permit advance(...) closure
DragonSlayer = Default._replace(
    ability=knight_bait_dragon,
    advance=(lambda _: DragonSlayer),  # Cannot advance further
    roll=Default.roll._replace(
        party=knight_roll_party,
    ),
    party=Default.party._replace(
        fighter=Default.party.fighter._replace(
            dragon=dragonslayer_defeat_dragon,
        ),
        cleric=Default.party.cleric._replace(
            dragon=dragonslayer_defeat_dragon,
        ),
        mage=Default.party.mage._replace(
            dragon=dragonslayer_defeat_dragon,
        ),
        thief=Default.party.thief._replace(
            dragon=dragonslayer_defeat_dragon,
        ),
        champion=Default.party.champion._replace(
            dragon=dragonslayer_defeat_dragon,
        ),
        scroll=Default.party.scroll._replace(
            dragon=dragonslayer_defeat_dragon,
        ),
    )
)

# Defined after DragonSlayer to permit advance(...) closure
Knight = Default._replace(
    ability=knight_bait_dragon,
    advance=(lambda world: Knight if world.experience < 5 else DragonSlayer),
    roll=Default.roll._replace(
        party=knight_roll_party,
    )
)


def spellsword_ability(
        game: struct.World, randrange: dice.RandRange, noun: str,
        target: typing.Optional[str] = None,
        *,
        _acceptable_targets: typing.Set[str] = {'fighter', 'mage'}
) -> struct.World:
    """Spellsword usable as a fighter or a mage, adding one hero to party."""
    if target is None:
        target = next(sorted(_acceptable_targets))
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
    """Discard all monsters, chests, potions, and dice in the dragon's lair.."""
    if target is not None:
        raise error.DrollError('No targets accepted for {}'.format(noun))
    return action.consume_ability(game._replace(
        dungeon=game.dungeon._replace([0] * len(struct.Dungeon._fields))
    ))


# Defined in terms of Default, not Spellsword, to permit advance(...) closure
Battlemage = Default._replace(
    ability=battlemage_ability,
    advance=(lambda _: Battlemage),  # Cannot advance further
    party=Default.party._replace(
        fighter=Default.party.fighter._replace(
            ooze=Default.party.mage.ooze,  # Fighters used as mages
            dragon=spellsword_defeat_dragon,
        ),
        cleric=Default.party.cleric._replace(
            dragon=spellsword_defeat_dragon,
        ),
        mage=Default.party.mage._replace(
            skeleton=Default.party.fighter.skeleton,  # Mages used as fighters
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

KNOWN = collections.OrderedDict([
    ('Default', Default),
    ('Knight', Knight),
])
