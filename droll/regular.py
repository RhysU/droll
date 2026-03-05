# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality for hero-agnostic regular actions."""

from dataclasses import replace
from operator import add
from collections.abc import Callable, Sequence, Set
from .dice import roll_dungeon, roll_party
from .dungeon import (
    DRAGON_BLOCKING_THRESHOLD,
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
    frozen,
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


def not_reroll(
    world: World, randrange: RandRange, hero: Party, targets: tuple[Dungeon | Party, ...]
) -> World:
    """Scrolls cannot target dungeon dice directly; use 'reroll' instead."""
    raise DrollError(f'Use "reroll {targets[0].value}" to re-roll with a scroll.')


def defeat_one(
    world: World, randrange: RandRange, hero: Party, targets: tuple[Dungeon, ...]
) -> World:
    """Update world after hero handles exactly one target."""
    if len(targets) != 1:
        raise DrollError(f"Exactly 1 target required but {len(targets)} given.")
    return replace(
        world,
        dungeon=decrement_dungeon(world.dungeon, targets[0]),
        party=decrement_party(world.party, hero),
        regroup=decrement_regroup(world.regroup, hero),
    )


def defeat_all(
    world: World, randrange: RandRange, hero: Party, targets: tuple[Dungeon, ...]
) -> World:
    """Update world after hero handles all of one type of target."""
    if len(targets) != 1:
        raise DrollError(f"Exactly 1 target required but {len(targets)} given.")
    return replace(
        world,
        dungeon=eliminate_dungeon(world.dungeon, targets[0]),
        party=decrement_party(world.party, hero),
        regroup=decrement_regroup(world.regroup, hero),
    )


def open_one(
    world: World,
    randrange: RandRange,
    hero: Party,
    targets: tuple[Dungeon, ...],
    *,
    after_monsters=True,
) -> World:
    """Update world after hero opens exactly one chest."""
    if len(targets) != 1:
        raise DrollError(f"Exactly 1 target required but {len(targets)} given.")
    if after_monsters and not defeated_monsters(world.dungeon):
        raise DrollError("Monsters must be defeated before opening.")
    return replace(
        world,
        treasure=draw_treasure(world.treasure, randrange),
        dungeon=decrement_dungeon(world.dungeon, targets[0]),
        party=decrement_party(world.party, hero),
        regroup=decrement_regroup(world.regroup, hero),
    )


def open_all(
    world: World,
    randrange: RandRange,
    hero: Party,
    targets: tuple[Dungeon, ...],
    *,
    after_monsters=True,
) -> World:
    """Update world after hero opens all chests."""
    if len(targets) != 1:
        raise DrollError(f"Exactly 1 target required but {len(targets)} given.")
    if after_monsters and not defeated_monsters(world.dungeon):
        raise DrollError("Monsters must be defeated before opening.")
    howmany = world.dungeon[targets[0]]
    if not howmany:
        raise DrollError(f"At least 1 {targets[0].value} required.")
    treasure = world.treasure
    for _ in range(howmany):
        treasure = draw_treasure(treasure, randrange)
    return replace(
        world,
        treasure=treasure,
        dungeon=eliminate_dungeon(world.dungeon, targets[0]),
        party=decrement_party(world.party, hero),
        regroup=decrement_regroup(world.regroup, hero),
    )


def quaff(
    world: World,
    randrange: RandRange,
    hero: Party,
    targets: tuple[Dungeon | Party, ...],
    *,
    after_monsters=True,
) -> World:
    """Update world after hero quaffs all available potions.

    Unlike {defeat,open}_{one,all}(...), heroes to revive are arguments."""
    if not targets:
        raise DrollError("At least 1 target required.")
    howmany = world.dungeon[targets[0]]
    if not howmany:
        raise DrollError(f"At least 1 {targets[0].value} required.")
    if len(targets) - 1 != howmany:
        raise DrollError(f"Specify exactly {howmany} to revive after 'potion'.")
    if after_monsters and not defeated_monsters(world.dungeon):
        raise DrollError("Monsters must be defeated before quaffing.")
    party = decrement_party(world.party, hero)
    for revived in targets[1:]:
        party = increment_party(party, revived)
    return replace(
        world,
        dungeon=eliminate_dungeon(world.dungeon, targets[0]),
        party=party,
        regroup=decrement_regroup(world.regroup, hero),
    )


def _classify_reroll_targets(
    dungeon_or_party: tuple[Dungeon | Party, ...],
    allow_dragon: bool,
) -> tuple[list[Dungeon], list[Party]]:
    """Classify reroll targets into dungeon and party lists."""
    dungeon_targets = []
    party_targets = []
    for target in dungeon_or_party:
        if isinstance(target, Dungeon):
            if not allow_dragon and target is Dungeon.DRAGON:
                raise DrollError(f"{target.value} cannot be re-rolled.")
            dungeon_targets.append(target)
        elif isinstance(target, Party):
            party_targets.append(target)
        else:
            raise DrollError(f"{target} cannot be re-rolled.")
    return dungeon_targets, party_targets


def reroll(
    world: World,
    randrange: RandRange,
    hero: Party,
    targets: tuple[Dungeon | Party, ...],
    *,
    allow_dragon: bool = False,
) -> World:
    """Update world after hero re-rolls dungeon or party dice."""
    if not targets:
        raise DrollError("At least 1 reroll target required.")

    dungeon_targets, party_targets = _classify_reroll_targets(
        targets, allow_dragon
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
        dungeon = frozen({
            d: dungeon[d] + increased[d] for d in Dungeon
        })

    if party_targets:
        for target in party_targets:
            party = decrement_party(party, target)
        increased, _ = roll_party(dice=len(party_targets), randrange=randrange)
        party = frozen({
            p: party[p] + increased[p] for p in Party
        })

    return replace(
        world,
        dungeon=dungeon,
        party=party,
        regroup=regroup,
    )


def distinct_heroes(
    heroes: Sequence[Party],
    *,
    wildcard: Set[Party] = frozenset(),
    interchangeable: Set[Party] = frozenset(),
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
    *heroes: Party,
    disallowed_heroes: Set[Party] = frozenset({Party.SCROLL}),
    required: int = 3,
    wildcard: Set[Party] = frozenset(),
    interchangeable: Set[Party] = frozenset(),
) -> None:
    """Validate sufficiently many distinct heroes to slay a dragon.

    Supports strict distinctness, wildcard heroes (fungible for any other),
    and interchangeable heroes (may substitute for one another).
    Raises DrollError if validation fails.
    """
    hero_set = {*heroes}
    if hero_set & {*disallowed_heroes}:
        raise DrollError(
            f"A {', '.join(sorted(h.value for h in disallowed_heroes))} cannot defeat a dragon."
        )
    if len(heroes) != required:
        raise DrollError(f"Exactly {required} heroes required.")
    n_distinct = distinct_heroes(
        heroes, wildcard=wildcard, interchangeable=interchangeable
    )
    if n_distinct != required:
        raise DrollError(
            f"Exactly {required} distinct heroes required"
            f" but '{', '.join(h.value for h in heroes)}' has only {n_distinct}."
        )


def defeat_dragon(
    world: World,
    randrange: RandRange,
    hero: Party,
    targets: tuple[Dungeon | Party, ...],
    *,
    hero_validator: Callable[..., None] = defeat_dragon_heroes,
    _min_dragon_count: int = DRAGON_BLOCKING_THRESHOLD,
) -> World:
    """Update world after hero handles a dragon using multiple distinct heroes.

    Additional required heroes are specified within the targets tuple."""
    if not targets:
        raise DrollError("At least 1 target required.")
    # Simple prerequisites for attempting to defeat the dragon
    if world.dungeon[Dungeon.DRAGON] < _min_dragon_count:
        raise DrollError(
            f"At least {_min_dragon_count} dragon dice required to fight."
        )
    if not defeated_monsters(world.dungeon):
        raise DrollError(
            f"Enemy {targets[0].value} only comes after all others defeated."
        )

    # Confirm required number of distinct heroes available
    party = decrement_party(world.party, hero)
    regroup = decrement_regroup(world.regroup, hero)
    heroes = [hero]
    for other in targets[1:]:
        party = decrement_party(party, other)
        regroup = decrement_regroup(regroup, other)
        heroes.append(other)
    hero_validator(*heroes)

    # Attempt was successful, so update experience and treasure
    return replace(
        world,
        treasure=draw_treasure(world.treasure, randrange),
        experience=world.experience + 1,
        party=party,
        dungeon=eliminate_dungeon(world.dungeon, targets[0]),
        regroup=regroup,
    )


def bait_dragon(
    world: World,
    randrange: RandRange,
    command: Dungeon | Party,
    targets: tuple[Dungeon | Party, ...] = (),
    *,
    _enemies: Sequence[Dungeon] = (Dungeon.GOBLIN, Dungeon.SKELETON, Dungeon.OOZE),
    require_treasure: bool = True,
) -> World:
    """Consume dragon bait to convert all monsters into dragon dice."""
    # Confirm well-formed request optionally containing a target
    if any(t is not Dungeon.DRAGON for t in targets):
        raise DrollError(f"Can only {command.value if hasattr(command, 'value') else command} dragon dice.")
    if require_treasure:
        from .struct import Artifact
        world = replace(world, treasure=replace_treasure(world.treasure, Artifact(command.value if hasattr(command, 'value') else command)))

    # Compute how many new dragons will be produced and remove sources
    dungeon = world.dungeon
    new_dragons = (
        sum(dungeon[enemy] for enemy in _enemies)
        if dungeon is not None
        else 0
    )
    if not new_dragons:
        raise DrollError(
            f"At least 1 monster ({', '.join(e.value for e in _enemies)}) required for '{command.value if hasattr(command, 'value') else command}'."
        )

    # Zero all enemy sources and increment the number of dragons
    return replace(
        world,
        dungeon=frozen({
            **dungeon,
            **{enemy: 0 for enemy in _enemies},
            Dungeon.DRAGON: dungeon[Dungeon.DRAGON] + new_dragons,
        }),
    )


def elixir(
    world: World, randrange: RandRange, command: Dungeon | Party, targets: tuple[Dungeon | Party, ...] = ()
) -> World:
    """Consume an elixir to add one hero die of any type."""
    if not targets:
        raise DrollError(f"Hero required for {command.value if hasattr(command, 'value') else command}.")
    from .struct import Artifact
    return replace(
        world,
        treasure=replace_treasure(world.treasure, Artifact(command.value if hasattr(command, 'value') else command)),
        party=increment_party(world.party, targets[0]),
    )
