# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Type definitions, generally of the struct-like variety."""
import collections
from dataclasses import dataclass, replace
import typing


@dataclass(frozen=True)
class Dungeon:
    goblin: typing.Any = 0
    skeleton: typing.Any = 0
    ooze: typing.Any = 0
    chest: typing.Any = 0
    potion: typing.Any = 0
    dragon: typing.Any = 0

    _fields = ("goblin", "skeleton", "ooze", "chest", "potion", "dragon")

    def __iter__(self):
        return iter((self.goblin, self.skeleton, self.ooze, self.chest,
                     self.potion, self.dragon))

    def __len__(self):
        return 6


@dataclass(frozen=True)
class Party:
    fighter: typing.Any = 0
    cleric: typing.Any = 0
    mage: typing.Any = 0
    thief: typing.Any = 0
    champion: typing.Any = 0
    scroll: typing.Any = 0

    _fields = ("fighter", "cleric", "mage", "thief", "champion", "scroll")

    def __iter__(self):
        return iter((self.fighter, self.cleric, self.mage, self.thief,
                     self.champion, self.scroll))

    def __len__(self):
        return 6

@dataclass(frozen=True)
class Roll:
    dungeon: typing.Any = None
    party: typing.Any = None

    _fields = ("dungeon", "party")

    def __iter__(self):
        return iter((self.dungeon, self.party))

    def __len__(self):
        return 2

@dataclass(frozen=True)
class Player:
    name: typing.Any = None
    ability: typing.Any = None
    advance: typing.Any = None
    bait: typing.Any = None
    elixir: typing.Any = None
    roll: typing.Any = None
    artifacts: typing.Any = None
    party: typing.Any = None

    _fields = ("name", "ability", "advance", "bait", "elixir", "roll",
               "artifacts", "party")

    def __iter__(self):
        return iter((self.name, self.ability, self.advance, self.bait,
                     self.elixir, self.roll, self.artifacts, self.party))

    def __len__(self):
        return 8

_RESERVE = collections.OrderedDict(
    (
        ("sword", 3),
        ("talisman", 3),
        ("sceptre", 3),
        ("tools", 3),
        ("scroll", 3),
        ("elixir", 3),
        ("bait", 4),
        ("portal", 4),
        ("ring", 4),
        ("scale", 6),
    )
)

@dataclass(frozen=True)
class Treasure:
    sword: typing.Any = 0
    talisman: typing.Any = 0
    sceptre: typing.Any = 0
    tools: typing.Any = 0
    scroll: typing.Any = 0
    elixir: typing.Any = 0
    bait: typing.Any = 0
    portal: typing.Any = 0
    ring: typing.Any = 0
    scale: typing.Any = 0

    _fields = ("sword", "talisman", "sceptre", "tools", "scroll", "elixir",
               "bait", "portal", "ring", "scale")

    def __iter__(self):
        return iter((self.sword, self.talisman, self.sceptre, self.tools,
                     self.scroll, self.elixir, self.bait, self.portal,
                     self.ring, self.scale))

    def __len__(self):
        return 10

RESERVE_INITIAL = Treasure(*_RESERVE.values())

TREASURE_INITIAL = Treasure(*([0] * len(_RESERVE)))

@dataclass(frozen=True)
class World:
    delve: typing.Any = None
    depth: typing.Any = None
    experience: typing.Any = None
    dungeon: typing.Any = None
    party: typing.Any = None
    ability: typing.Any = None
    treasure: typing.Any = None
    reserve: typing.Any = None

    _fields = ("delve", "depth", "experience", "dungeon", "party", "ability",
               "treasure", "reserve")

    def __iter__(self):
        return iter((self.delve, self.depth, self.experience, self.dungeon,
                     self.party, self.ability, self.treasure, self.reserve))

    def __len__(self):
        return 8


def update_party_dragon(party: Party, dragon_func) -> Party:
    """Update all heroes in a party to use a custom dragon defeat function."""
    return Party(*(
        replace(hero_dungeon, dragon=dragon_func)
        for hero_dungeon in party
    ))


def brief(o: typing.Any, *, omitted: typing.Set[str] = {"reserve"}) -> str:
    """A __str__(...) variant suppressing False fields within namedtuples."""
    fields = getattr(o, "_fields", None)
    if fields is None:
        return str(o)

    keyvalues = []
    for field, value in zip(fields, o):
        if value and field not in omitted:
            keyvalues.append("{}={}".format(field, brief(value)))
    return "({})".format(", ".join(keyvalues))
