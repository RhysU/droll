# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Type definitions, generally of the struct-like variety."""
import dataclasses
import typing


def field_names(cls_or_instance: typing.Any) -> typing.Iterator[str]:
    """Yield field names for a dataclass or instance thereof."""
    return (f.name for f in dataclasses.fields(cls_or_instance))


def field_values(instance: typing.Any) -> typing.Iterator[typing.Any]:
    """Yield field values for a dataclass instance."""
    return (getattr(instance, f.name) for f in dataclasses.fields(instance))


def field_items(
    instance: typing.Any,
) -> typing.Iterator[typing.Tuple[str, typing.Any]]:
    """Yield (name, value) pairs for a dataclass instance."""
    return (
        (f.name, getattr(instance, f.name))
        for f in dataclasses.fields(instance)
    )


@dataclasses.dataclass(frozen=True)
class Dungeon:
    goblin: typing.Any = 0
    skeleton: typing.Any = 0
    ooze: typing.Any = 0
    chest: typing.Any = 0
    potion: typing.Any = 0
    dragon: typing.Any = 0


@dataclasses.dataclass(frozen=True)
class Party:
    fighter: typing.Any = 0
    cleric: typing.Any = 0
    mage: typing.Any = 0
    thief: typing.Any = 0
    champion: typing.Any = 0
    scroll: typing.Any = 0


@dataclasses.dataclass(frozen=True)
class Roll:
    dungeon: typing.Any = None
    party: typing.Any = None


@dataclasses.dataclass(frozen=True)
class Player:
    name: typing.Any = None
    ability: typing.Any = None
    advance: typing.Any = None
    bait: typing.Any = None
    elixir: typing.Any = None
    roll: typing.Any = None
    artifacts: typing.Any = None
    party: typing.Any = None


@dataclasses.dataclass(frozen=True)
class Treasure:
    sword: int = 0
    talisman: int = 0
    sceptre: int = 0
    tools: int = 0
    scroll: int = 0
    elixir: int = 0
    bait: int = 0
    portal: int = 0
    ring: int = 0
    scale: int = 0


# Bookkeeping for operations performed during the regroup phase
@dataclasses.dataclass(frozen=True)
class Regroup:
    discard: Party = Party()  # Discard N party dice in regroup phase


@dataclasses.dataclass(frozen=True)
class World:
    delve: int = 0
    depth: typing.Optional[int] = None
    experience: int = 0
    dungeon: typing.Optional[Dungeon] = None
    party: typing.Optional[Party] = None
    ability: typing.Optional[bool] = None
    regroup: Regroup = Regroup()
    treasure: Treasure = Treasure()
    reserve: Treasure = Treasure()


# Strictly speaking, "reserve" is genuine world state and tricky to deduce.
# Only for historical reasons is it omitted below.
def brief(
    o: typing.Any, *, omitted: typing.AbstractSet[str] = frozenset({"reserve"})
) -> str:
    """A __str__(...) variant suppressing False fields within dataclasses."""
    try:
        names = field_names(o)
        values = field_values(o)
    except TypeError:
        return str(o)

    keyvalues = []
    for field, value in zip(names, values):
        if value and field not in omitted:
            keyvalues.append("{}={}".format(field, brief(value)))
    return "({})".format(", ".join(keyvalues))
