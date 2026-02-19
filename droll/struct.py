# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Type definitions, generally of the struct-like variety."""

import collections.abc
import dataclasses
from typing import Any, Optional

__all__ = (
    "Artifacts",
    "Dungeon",
    "Party",
    "Player",
    "Regroup",
    "Roll",
    "Treasure",
    "World",
    "brief",
    "field_items",
    "field_names",
    "field_values",
)


def field_names(cls_or_instance: Any) -> collections.abc.Iterator[str]:
    """Yield field names for a dataclass or instance thereof."""
    return (f.name for f in dataclasses.fields(cls_or_instance))


def field_values(instance: Any) -> collections.abc.Iterator[Any]:
    """Yield field values for a dataclass instance."""
    return (getattr(instance, f.name) for f in dataclasses.fields(instance))


def field_items(
    instance: Any,
) -> collections.abc.Iterator[tuple[str, Any]]:
    """Yield (name, value) pairs for a dataclass instance."""
    return (
        (f.name, getattr(instance, f.name))
        for f in dataclasses.fields(instance)
    )


@dataclasses.dataclass(frozen=True)
class Dungeon:
    goblin: Any = 0
    skeleton: Any = 0
    ooze: Any = 0
    chest: Any = 0
    potion: Any = 0
    dragon: Any = 0


@dataclasses.dataclass(frozen=True)
class Party:
    fighter: Any = 0
    cleric: Any = 0
    mage: Any = 0
    thief: Any = 0
    champion: Any = 0
    scroll: Any = 0


@dataclasses.dataclass(frozen=True)
class Roll:
    dungeon: Optional[collections.abc.Callable] = None
    party: Optional[collections.abc.Callable] = None


@dataclasses.dataclass(frozen=True)
class Player:
    name: Optional[str] = None
    ability: Optional[collections.abc.Callable] = None
    advance: Optional[collections.abc.Callable] = None
    bait: Optional[collections.abc.Callable] = None
    elixir: Optional[collections.abc.Callable] = None
    roll: Optional[Roll] = None
    artifacts: Optional[Party] = None
    party: Optional[Party] = None


@dataclasses.dataclass(frozen=True)
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


@dataclasses.dataclass(frozen=True)
class Treasure:
    own: Artifacts = Artifacts()
    box: Artifacts = Artifacts()


# Bookkeeping for operations performed during the regroup phase
@dataclasses.dataclass(frozen=True)
class Regroup:
    discard: Party = Party()  # Discard N party dice in regroup phase


@dataclasses.dataclass(frozen=True)
class World:
    delve: int = 0
    depth: Optional[int] = None
    experience: int = 0
    dungeon: Optional[Dungeon] = None
    party: Optional[Party] = None
    ability: Optional[bool] = None
    regroup: Regroup = Regroup()
    treasure: Treasure = Treasure()


# Strictly speaking, "box" is genuine world state and tricky to deduce.
# Only for historical reasons is it omitted below.
def brief(
    o: Any,
    *,
    omitted: collections.abc.Set[str] = frozenset({"box"}),
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
            keyvalues.append(f"{field}={brief(value)}")
    return f"({', '.join(keyvalues)})"
