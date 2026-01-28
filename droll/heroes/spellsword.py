# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Spellsword advancing to Battlemage."""
from dataclasses import replace
import functools
import typing

from .. import action
from .. import dice
from .. import error
from .. import struct
from ..player import Default


def _spellsword_ability(
    game: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: typing.Optional[str] = None,
    *,
    _acceptable_targets: typing.FrozenSet[str] = frozenset({"fighter", "mage"})
) -> struct.World:
    """Spellsword usable as a fighter or a mage, adding one hero to party.

    Optionally, specify 'fighter' or 'mage' to select which to choose."""
    if target is None:
        target = next(iter(sorted(_acceptable_targets)))
    if target not in _acceptable_targets:
        raise error.DrollError(
            "Target {} not one of {}".format(target, _acceptable_targets)
        )
    return action.consume_ability(
        replace(game, party=action.increment_hero(game.party, target))
    )


# Fighter/mage are interchangeable for dragon defeats
_spellsword_defeat_dragon = functools.partial(
    action.defeat_dragon,
    _defeat_dragon_heroes=functools.partial(
        action.defeat_dragon_heroes_interchangeable,
        _interchangeable={"fighter", "mage"},
    ),
)


def _battlemage_ability(
    game: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: typing.Optional[str] = None,
    *,
    _acceptable_targets: typing.FrozenSet[str] = frozenset({"fighter", "mage"})
) -> struct.World:
    """Discard all monsters, chests, potions, and dice in the dragon's lair."""
    if target is not None:
        raise error.DrollError("No targets accepted for {}".format(noun))
    return action.consume_ability(replace(game, dungeon=struct.Dungeon()))


# Defined in terms of Default, not Spellsword, to permit advance(...) closure
Battlemage = replace(
    Default,
    name="Battlemage",
    ability=_battlemage_ability,
    advance=(lambda _: Battlemage),
    party=replace(
        struct.update_party_dragon(Default.party, _spellsword_defeat_dragon),
        fighter=replace(Default.party.fighter, ooze=Default.party.mage.ooze),
        mage=replace(Default.party.mage, goblin=Default.party.fighter.goblin),
    ),
)

# Defined after Battlemage to permit advance(...) closure
Spellsword = replace(
    Default,
    name="Spellsword",
    ability=_spellsword_ability,
    advance=(lambda world: Spellsword if world.experience < 5 else Battlemage),
    party=Battlemage.party,
)
