# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions."""
import collections
import functools

from . import action
from . import dice
from . import player
from . import struct


# TODO Implement the following initial characters
# TODO Implement promotion after 5 experience points
# Spellsword -> Battlemage
# Crusader -> Paladin
# Knight -> Dragon Slayer
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


Knight = player.Default._replace(
    ability=knight_bait_dragon,
    roll=player.Default.roll._replace(
        party=knight_roll_party,
    )
)


@functools.wraps(action.defeat_dragon_heroes)
def dragonslayer_defeat_dragon_heroes(*args, **kwargs):
    return action.defeat_dragon_heroes(*args, **kwargs, _distinct_heroes=2)


@functools.wraps(action.defeat_dragon)
def dragonslayer_defeat_dragon(*args, **kwargs):
    return action.defeat_dragon(
        *args,
        **kwargs,
        _defeat_dragon_heroes=dragonslayer_defeat_dragon_heroes)


DragonSlayer = Knight._replace(
    party=Knight.party._replace(
        fighter=Knight.party.fighter._replace(
            dragon=dragonslayer_defeat_dragon,
        ),
        cleric=Knight.party.cleric._replace(
            dragon=dragonslayer_defeat_dragon,
        ),
        mage=Knight.party.mage._replace(
            dragon=dragonslayer_defeat_dragon,
        ),
        thief=Knight.party.thief._replace(
            dragon=dragonslayer_defeat_dragon,
        ),
        champion=Knight.party.champion._replace(
            dragon=dragonslayer_defeat_dragon,
        ),
        scroll=Knight.party.scroll._replace(
            dragon=dragonslayer_defeat_dragon,
        ),
    )

)

KNOWN = collections.OrderedDict([
    ('Default', player.Default),
    ('Knight', Knight),
])
