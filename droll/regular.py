# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality for hero-agnostic regular actions."""

from dataclasses import replace
from operator import add
from collections.abc import Sequence, Set
from typing import Optional

from .dice import roll_dungeon, roll_party
from .dungeon import (
    defeated_monsters,
    decrement_dungeon,
    eliminate_dungeon,
)
from .party import decrement_party, decrement_regroup, increment_party
from .struct import (
    DrollError,
    Dungeon,
    Party,
    RandRange,
    World,
    field_names,
    field_values,
)
from .treasure import draw_treasure, replace_treasure

__all__ = (
    "bait_dragon",
    "defeat_all",
    "defeat_dragon",
    "defeat_dragon_heroes",
    "defeat_one",
    "distinct_heroes",
    "elixir",
    "not_reroll",
    "open_all",
    "open_one",
    "quaff",
    "reroll",
)

_DUNGEON_NAMES = frozenset(field_names(Dungeon))
_PARTY_NAMES = frozenset(field_names(Party))


def not_reroll(
    world: World, randrange: RandRange, hero: str, target: str, *additional
) -> World:
    """Scrolls cannot target dungeon dice directly; use 'reroll' instead."""
    raise DrollError(f'Use "reroll {target}" to re-roll with a scroll.')


def defeat_one(
    world: World, randrange: RandRange, hero: str, target: str
) -> World:
    """Update world after hero handles exactly one target."""
    return replace(
        world,
        dungeon=decrement_dungeon(world.dungeon, target),
        party=decrement_party(world.party, hero),
        regroup=decrement_regroup(world.regroup, hero),
    )


def defeat_all(
    world: World, randrange: RandRange, hero: str, target: str
) -> World:
    """Update world after hero handles all of one type of target."""
    return replace(
        world,
        dungeon=eliminate_dungeon(world.dungeon, target),
        party=decrement_party(world.party, hero),
        regroup=decrement_regroup(world.regroup, hero),
    )


def open_one(
    world: World,
    randrange: RandRange,
    hero: str,
    target: str,
    *,
    after_monsters=True,
) -> World:
    """Update world after hero opens exactly one chest."""
    if after_monsters and not defeated_monsters(world.dungeon):
        raise DrollError("Monsters must be defeated before opening.")
    return replace(
        world,
        treasure=draw_treasure(world.treasure, randrange),
        dungeon=decrement_dungeon(world.dungeon, target),
        party=decrement_party(world.party, hero),
        regroup=decrement_regroup(world.regroup, hero),
    )


def open_all(
    world: World,
    randrange: RandRange,
    hero: str,
    target: str,
    *,
    after_monsters=True,
) -> World:
    """Update world after hero opens all chests."""
    if after_monsters and not defeated_monsters(world.dungeon):
        raise DrollError("Monsters must be defeated before opening.")
    howmany = getattr(world.dungeon, target)
    if not howmany:
        raise DrollError(f"At least 1 {target} required.")
    treasure = world.treasure
    for _ in range(howmany):
        treasure = draw_treasure(treasure, randrange)
    return replace(
        world,
        treasure=treasure,
        dungeon=eliminate_dungeon(world.dungeon, target),
        party=decrement_party(world.party, hero),
        regroup=decrement_regroup(world.regroup, hero),
    )


def quaff(
    world: World,
    randrange: RandRange,
    hero: str,
    target: str,
    *revivable,
    after_monsters=True,
) -> World:
    """Update world after hero quaffs all available potions.

    Unlike {defeat,open}_{one,all}(...), heroes to revive are arguments."""
    howmany = getattr(world.dungeon, target)
    if not howmany:
        raise DrollError(f"At least 1 {target} required.")
    if len(revivable) != howmany:
        raise DrollError(f"Exactly {howmany} heroes to revive required.")
    if after_monsters and not defeated_monsters(world.dungeon):
        raise DrollError("Monsters must be defeated before quaffing.")
    party = decrement_party(world.party, hero)
    for revived in revivable:
        party = increment_party(party, revived)
    return replace(
        world,
        dungeon=eliminate_dungeon(world.dungeon, target),
        party=party,
        regroup=decrement_regroup(world.regroup, hero),
    )


def _classify_reroll_targets(
    dungeon_or_party: tuple[str, ...],
    allow_dragon: bool,
) -> tuple[list[str], list[str]]:
    """Classify reroll targets into dungeon and party lists."""
    dungeon_targets = []
    party_targets = []
    for target in dungeon_or_party:
        if not allow_dragon and target == "dragon":
            raise DrollError(f"{target} cannot be re-rolled.")
        if target in _DUNGEON_NAMES:
            dungeon_targets.append(target)
        elif target in _PARTY_NAMES:
            party_targets.append(target)
        else:
            raise DrollError(f"{target} cannot be re-rolled.")
    return dungeon_targets, party_targets


def reroll(
    world: World,
    randrange: RandRange,
    hero: str,
    *dungeon_or_party,
    allow_dragon: bool = False,
) -> World:
    """Update world after hero re-rolls dungeon or party dice."""
    if not dungeon_or_party:
        raise DrollError("At least 1 reroll target required.")

    dungeon_targets, party_targets = _classify_reroll_targets(
        dungeon_or_party, allow_dragon
    )

    # Decrement hero and regroup BEFORE any dice are rolled to prevent
    # stochastic exploitation: a rolled result cannot be immediately spent.
    party = decrement_party(world.party, hero)
    regroup = decrement_regroup(world.regroup, hero)

    dungeon = world.dungeon
    if dungeon_targets:
        for target in dungeon_targets:
            dungeon = decrement_dungeon(dungeon, target)
        increased = roll_dungeon(
            dice=len(dungeon_targets), randrange=randrange
        )
        dungeon = Dungeon(
            *map(
                add,
                field_values(dungeon),
                field_values(increased),
            )
        )

    if party_targets:
        for target in party_targets:
            party = decrement_party(party, target)
        increased, _ = roll_party(dice=len(party_targets), randrange=randrange)
        party = Party(
            *map(
                add,
                field_values(party),
                field_values(increased),
            )
        )

    return replace(
        world,
        dungeon=dungeon,
        party=party,
        regroup=regroup,
    )


def distinct_heroes(
    heroes: Sequence[str],
    *,
    wildcard: Set[str] = frozenset(),
    interchangeable: Set[str] = frozenset(),
) -> int:
    """How many distinct heroes does the given list represent?

    Wildcards are fungible for any other hero type.
    Interchangeable heroes may substitute for one another.
    """
    n_wildcard = sum(1 for h in heroes if h in wildcard)
    inter = [h for h in heroes if h not in wildcard and h in interchangeable]
    regular = [
        h for h in heroes if h not in wildcard and h not in interchangeable
    ]
    return (
        len(set(regular)) + min(len(inter), len(interchangeable)) + n_wildcard
    )


def defeat_dragon_heroes(
    *heroes,
    disallowed_heroes: Set[str] = frozenset({"scroll"}),
    required: int = 3,
    wildcard: Set[str] = frozenset(),
    interchangeable: Set[str] = frozenset(),
) -> None:
    """Validate sufficiently many distinct heroes to slay a dragon.

    Supports strict distinctness, wildcard heroes (fungible for any other),
    and interchangeable heroes (may substitute for one another).
    Raises DrollError if validation fails.
    """
    hero_set = {*heroes}
    if hero_set & {*disallowed_heroes}:
        raise DrollError(f"Heroes {disallowed_heroes} cannot defeat a dragon.")
    if len(heroes) != required:
        raise DrollError(f"Exactly {required} heroes required.")
    n_distinct = distinct_heroes(
        heroes, wildcard=wildcard, interchangeable=interchangeable
    )
    if n_distinct != required:
        raise DrollError(
            f"Exactly {required} distinct heroes not in {', '.join(heroes)}"
        )


def defeat_dragon(
    world: World,
    randrange: RandRange,
    hero: str,
    target: str,
    *others,
    defeat_dragon_heroes=defeat_dragon_heroes,  # What type hint?
    _min_dragon_count: int = 3,
) -> World:
    """Update world after hero handles a dragon using multiple distinct heroes.

    Additional required heroes are specified within variable-length others."""
    # Simple prerequisites for attempting to defeat the dragon
    if world.dungeon.dragon < _min_dragon_count:
        raise DrollError(
            f"Enemy {target} only comes at length {_min_dragon_count}."
        )
    if not defeated_monsters(world.dungeon):
        raise DrollError(
            f"Enemy {target} only comes after all others defeated."
        )

    # Confirm required number of distinct heroes available
    party = decrement_party(world.party, hero)
    regroup = decrement_regroup(world.regroup, hero)
    heroes = [hero]
    for other in others:
        party = decrement_party(party, other)
        regroup = decrement_regroup(regroup, other)
        heroes.append(other)
    defeat_dragon_heroes(*heroes)

    # Attempt was successful, so update experience and treasure
    return replace(
        world,
        treasure=draw_treasure(world.treasure, randrange),
        experience=world.experience + 1,
        party=party,
        dungeon=eliminate_dungeon(world.dungeon, target),
        regroup=regroup,
    )


def bait_dragon(
    world: World,
    randrange: RandRange,
    noun: str,
    target: Optional[str] = None,
    *,
    _enemies: Sequence[str] = ("goblin", "skeleton", "ooze"),
    require_treasure: bool = True,
) -> World:
    """Consume dragon bait to convert all monsters into dragon dice."""
    # Confirm well-formed request optionally containing a target
    target = "dragon" if target is None else target
    if target != "dragon":
        raise DrollError(f"Cannot {noun} a {target}.")
    if require_treasure:
        world = replace(world, treasure=replace_treasure(world.treasure, noun))

    # Compute how many new dragons will be produced and remove sources
    dungeon = world.dungeon
    new_targets = (
        sum(getattr(dungeon, enemy) for enemy in _enemies)
        if dungeon is not None
        else 0
    )
    if not new_targets:
        raise DrollError(f"At least 1 of {_enemies} required for '{noun}'.")

    # Zero all enemy sources and increment the number of dragons
    return replace(
        world,
        dungeon=replace(
            dungeon,
            **{enemy: 0 for enemy in _enemies},
            **{target: getattr(dungeon, target) + new_targets},
        ),
    )


def elixir(
    world: World, randrange: RandRange, noun: str, target: Optional[str] = None
) -> World:
    """Consume an elixir to add one hero die of any type."""
    if target is None:
        raise DrollError(f"Hero required for {noun}.")
    return replace(
        world,
        treasure=replace_treasure(world.treasure, noun),
        party=increment_party(world.party, target),
    )
