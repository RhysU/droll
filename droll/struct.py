# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Type definitions, generally of the struct-like variety."""

import enum
from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import Any, Optional

__all__ = (
    "Action",
    "Advance",
    "Artifact",
    "ArtifactCounts",
    "ArtifactMapping",
    "Command",
    "DrollError",
    "Dungeon",
    "DungeonState",
    "HeroActions",
    "Party",
    "PartyActions",
    "PartyState",
    "Player",
    "RandRange",
    "Regroup",
    "Roll",
    "RollDungeon",
    "RollParty",
    "Treasure",
    "World",
    "brief",
    "empty_artifact_counts",
    "empty_dungeon",
    "empty_party",
    "field_items",
    "field_names",
    "field_values",
    "frozen",
)


class DrollError(Exception):
    """Indicates attempts to take impossible actions."""


# ── Enums ──────────────────────────────────────────────────────────────

class Dungeon(enum.Enum):
    GOBLIN = "goblin"
    SKELETON = "skeleton"
    OOZE = "ooze"
    CHEST = "chest"
    POTION = "potion"
    DRAGON = "dragon"


class Party(enum.Enum):
    FIGHTER = "fighter"
    CLERIC = "cleric"
    MAGE = "mage"
    THIEF = "thief"
    CHAMPION = "champion"
    SCROLL = "scroll"


class Artifact(enum.Enum):
    SWORD = "sword"
    TALISMAN = "talisman"
    SCEPTRE = "sceptre"
    TOOLS = "tools"
    SCROLL = "scroll"
    ELIXIR = "elixir"
    BAIT = "bait"
    PORTAL = "portal"
    RING = "ring"
    SCALE = "scale"


class Action(enum.Enum):
    ABILITY = "ability"
    BAIT = "bait"
    ELIXIR = "elixir"
    REROLL = "reroll"


# ── Helpers ────────────────────────────────────────────────────────────

def frozen(d: dict) -> MappingProxyType:
    """Return an immutable mapping from d."""
    return MappingProxyType(d)


def empty_dungeon() -> MappingProxyType:
    """A DungeonState with all counts zero."""
    return frozen({d: 0 for d in Dungeon})


def empty_party() -> MappingProxyType:
    """A PartyState with all counts zero."""
    return frozen({p: 0 for p in Party})


def empty_artifact_counts() -> MappingProxyType:
    """An ArtifactCounts with all counts zero."""
    return frozen({a: 0 for a in Artifact})


def make_dungeon(**kwargs: int) -> MappingProxyType:
    """Build a DungeonState from keyword arguments using value names."""
    base = {d: 0 for d in Dungeon}
    for name, val in kwargs.items():
        base[Dungeon(name)] = val
    return frozen(base)


def make_party(**kwargs: int) -> MappingProxyType:
    """Build a PartyState from keyword arguments using value names."""
    base = {p: 0 for p in Party}
    for name, val in kwargs.items():
        base[Party(name)] = val
    return frozen(base)


def make_artifacts(**kwargs: int) -> MappingProxyType:
    """Build an ArtifactCounts from keyword arguments using value names."""
    base = {a: 0 for a in Artifact}
    for name, val in kwargs.items():
        base[Artifact(name)] = val
    return frozen(base)


def all_dungeon(value: int) -> MappingProxyType:
    """Build a DungeonState with all faces set to value."""
    return frozen({d: value for d in Dungeon})


def all_party(value: int) -> MappingProxyType:
    """Build a PartyState with all faces set to value."""
    return frozen({p: value for p in Party})


# ── Type aliases (annotation-time: Mapping; runtime: MappingProxyType) ─

DungeonState = Mapping[Dungeon, int]
PartyState = Mapping[Party, int]
ArtifactCounts = Mapping[Artifact, int]

RandRange = Callable[[int, int], int]

Command = Callable[["World", RandRange, "Party", "tuple[Dungeon | Party, ...]"], "World"]

HeroActions = Mapping[Dungeon, Command]
PartyActions = Mapping[Party, HeroActions]
ArtifactMapping = Mapping[Party, Optional[Artifact]]


RollDungeon = Callable[[int, RandRange], DungeonState]
RollParty = Callable[[int, RandRange], "tuple[PartyState, Regroup]"]


# ── Surviving dataclasses ──────────────────────────────────────────────

@dataclass(frozen=True)
class Regroup:
    discard: PartyState = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.discard is None:
            object.__setattr__(self, "discard", empty_party())


@dataclass(frozen=True)
class Roll:
    dungeon: RollDungeon
    party: RollParty


@dataclass(frozen=True)
class Treasure:
    own: ArtifactCounts = None  # type: ignore[assignment]
    box: ArtifactCounts = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.own is None:
            object.__setattr__(self, "own", empty_artifact_counts())
        if self.box is None:
            object.__setattr__(self, "box", empty_artifact_counts())


@dataclass(frozen=True)
class World:
    delve: int = 0
    depth: int = 0
    experience: int = 0
    dungeon: Optional[DungeonState] = None
    party: PartyState = None  # type: ignore[assignment]
    ability: bool = False
    regroup: Regroup = None  # type: ignore[assignment]
    treasure: Treasure = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.party is None:
            object.__setattr__(self, "party", empty_party())
        if self.regroup is None:
            object.__setattr__(self, "regroup", Regroup())
        if self.treasure is None:
            object.__setattr__(self, "treasure", Treasure())


@dataclass(frozen=True)
class Player:
    name: str
    ability: Command
    advance: "Advance"
    bait: Command
    elixir: Command
    roll: Roll
    artifacts: ArtifactMapping
    party: PartyActions


Advance = Callable[[World], Player]


# ── Dataclass introspection helpers (for surviving dataclasses) ────────

def field_names(cls_or_instance: Any) -> tuple[str, ...]:
    """Return field names for a dataclass or instance thereof."""
    return tuple(f.name for f in fields(cls_or_instance))


def field_values(instance: Any) -> tuple[Any, ...]:
    """Return field values for a dataclass instance."""
    return tuple(getattr(instance, f.name) for f in fields(instance))


def field_items(
    instance: Any,
) -> tuple[tuple[str, Any], ...]:
    """Return (name, value) pairs for a dataclass instance."""
    return tuple((f.name, getattr(instance, f.name)) for f in fields(instance))


# ── Display helper ─────────────────────────────────────────────────────

def brief(o: Any) -> str:
    """A __str__(...) variant suppressing False fields within dataclasses."""
    if isinstance(o, Mapping):
        kv = [f"{k.value}={brief(v)}" for k, v in o.items() if v]
        return f"({', '.join(kv)})"
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
