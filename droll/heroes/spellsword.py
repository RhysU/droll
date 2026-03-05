# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Spellsword advancing to Battlemage."""

from dataclasses import replace
from functools import partial

from .. import regular
from ..ability import battlemage_ability, spellsword_ability
from ..player import Default
from ..struct import Dungeon, Party, frozen

__all__ = (
    "Battlemage",
    "Spellsword",
)

# Fighter/mage are interchangeable for dragon defeats
_spellsword_defeat_dragon = partial(
    regular.defeat_dragon,
    hero_validator=partial(
        regular.defeat_dragon_heroes,
        interchangeable=frozenset({Party.FIGHTER, Party.MAGE}),
    ),
)


# Defined in terms of Default, not Spellsword, to permit advance(...) closure
Battlemage = replace(
    Default,
    name="Battlemage",
    ability=battlemage_ability,
    advance=(lambda _: Battlemage),
    party=frozen({
        Party.FIGHTER: frozen({
            **Default.party[Party.FIGHTER],
            Dungeon.DRAGON: _spellsword_defeat_dragon,
            Dungeon.OOZE: Default.party[Party.MAGE][Dungeon.OOZE],
        }),
        Party.CLERIC: frozen({
            **Default.party[Party.CLERIC],
            Dungeon.DRAGON: _spellsword_defeat_dragon,
        }),
        Party.MAGE: frozen({
            **Default.party[Party.MAGE],
            Dungeon.DRAGON: _spellsword_defeat_dragon,
            Dungeon.GOBLIN: Default.party[Party.FIGHTER][Dungeon.GOBLIN],
        }),
        Party.THIEF: frozen({
            **Default.party[Party.THIEF],
            Dungeon.DRAGON: _spellsword_defeat_dragon,
        }),
        Party.CHAMPION: frozen({
            **Default.party[Party.CHAMPION],
            Dungeon.DRAGON: _spellsword_defeat_dragon,
        }),
        Party.SCROLL: frozen({
            **Default.party[Party.SCROLL],
            Dungeon.DRAGON: _spellsword_defeat_dragon,
        }),
    }),
)

# Defined after Battlemage to permit advance(...) closure
Spellsword = replace(
    Default,
    name="Spellsword",
    ability=spellsword_ability,
    advance=(lambda world: Spellsword if world.experience < 5 else Battlemage),
    party=Battlemage.party,
)
