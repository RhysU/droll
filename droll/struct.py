# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Type definitions, generally of the struct-like variety."""

from collections.abc import Callable
from dataclasses import dataclass, fields
from typing import Any, Iterator, Optional

__all__ = (
    "Ability",
    "Advance",
    "Artifacts",
    "DrollError",
    "Dungeon",
    "Party",
    "Player",
    "RandRange",
    "Regroup",
    "Roll",
    "RollDungeon",
    "RollParty",
    "Treasure",
    "World",
    "brief",
    "field_items",
    "field_names",
    "field_values",
)


class DrollError(Exception):
    """Indicates attempts to take impossible actions."""


def field_names(cls_or_instance: Any) -> Iterator[str]:
    """Yield field names for a dataclass or instance thereof."""
    return (f.name for f in fields(cls_or_instance))


def field_values(instance: Any) -> Iterator[Any]:
    """Yield field values for a dataclass instance."""
    return (getattr(instance, f.name) for f in fields(instance))


def field_items(
    instance: Any,
) -> Iterator[tuple[str, Any]]:
    """Yield (name, value) pairs for a dataclass instance."""
    return ((f.name, getattr(instance, f.name)) for f in fields(instance))


RandRange = Callable[[int, int], int]


@dataclass(frozen=True)
class Dungeon:
    goblin: Any = 0
    skeleton: Any = 0
    ooze: Any = 0
    chest: Any = 0
    potion: Any = 0
    dragon: Any = 0


RollDungeon = Callable[[int, RandRange], Dungeon]


@dataclass(frozen=True)
class Party:
    fighter: Any = 0
    cleric: Any = 0
    mage: Any = 0
    thief: Any = 0
    champion: Any = 0
    scroll: Any = 0


# Bookkeeping for operations performed during the regroup phase
@dataclass(frozen=True)
class Regroup:
    discard: Party = Party()  # Discard N party dice in regroup phase


RollParty = Callable[[int, RandRange], tuple[Party, Regroup]]


@dataclass(frozen=True)
class Roll:
    dungeon: Optional[RollDungeon] = None
    party: Optional[RollParty] = None


@dataclass(frozen=True)
class Artifacts:
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


@dataclass(frozen=True)
class Treasure:
    own: Artifacts = Artifacts()
    box: Artifacts = Artifacts()


@dataclass(frozen=True)
class World:
    delve: int = 0
    depth: int = 0
    experience: int = 0
    dungeon: Optional[Dungeon] = None
    party: Optional[Party] = None
    ability: Optional[bool] = None
    regroup: Regroup = Regroup()
    treasure: Treasure = Treasure()


Ability = Callable[..., World]


@dataclass(frozen=True)
class Player:
    name: Optional[str] = None
    ability: Optional[Ability] = None
    advance: Optional["Advance"] = None
    bait: Optional[Ability] = None
    elixir: Optional[Ability] = None
    roll: Optional[Roll] = None
    artifacts: Optional[Party] = None
    party: Optional[Party] = None


Advance = Callable[[World], Player]


def brief(o: Any) -> str:
    """A __str__(...) variant suppressing False fields within dataclasses."""
    try:
        names = field_names(o)
        values = field_values(o)
    except TypeError:
        return str(o)

    keyvalues = []
    for field, value in zip(names, values):
        if value:
            keyvalues.append(f"{field}={brief(value)}")
    return f"({', '.join(keyvalues)})"
