# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with player action mechanics."""

from typing import Optional

from collections import Counter
from collections.abc import Sequence
from dataclasses import replace
from operator import add

from .dice import RandRange, roll_dungeon, roll_party
from .dungeon import (
    defeated_monsters,
    decrement_dungeon,
    eliminate_dungeon,
    increment_dungeon,
)
from .error import DrollError
from .struct import Dungeon, Party, Regroup, World, field_names, field_values
from .treasure import draw_treasure, replace_treasure

__all__ = (
    "bait_dragon",
    "consume_ability",
    "convert_dungeon_to_party",
    "defeat_all",
    "defeat_all_plus_additional",
    "defeat_one_plus_additional",
    "defeat_dragon",
    "defeat_dragon_heroes",
    "defeat_dragon_heroes_interchangeable",
    "defeat_dragon_heroes_wildcard",
    "defeat_one",
    "elixir",
    "increment_party",
    "nop_ability",
    "open_all",
    "open_one",
    "quaff",
    "reroll",
)

_DUNGEON_NAMES = frozenset(field_names(Dungeon))
_PARTY_NAMES = frozenset(field_names(Party))


def defeat_one(
    world: World, randrange: RandRange, hero: str, target: str
) -> World:
    """Update world after hero handles exactly one target."""
    return replace(
        world,
        dungeon=decrement_dungeon(world.dungeon, target),
        party=_decrement_party(world.party, hero),
        regroup=_decrement_regroup(world.regroup, hero),
    )


# Private because it must be used with _decrement_regroup for correctness
def _decrement_party(party: Party, hero: str) -> Party:
    """Decrease the count of the specified hero type by one."""
    if party is None:
        raise DrollError("No party currently active.")
    prior_heroes = getattr(party, hero)
    if not prior_heroes:
        raise DrollError(f"At least 1 {hero} required.")
    return replace(party, **{hero: prior_heroes - 1})


# Private because it must be used with _decrement_party for correctness
def _decrement_regroup(regroup: Regroup, hero: str) -> Regroup:
    """Decrement the regroup discard counter for hero, if positive."""
    prior = getattr(regroup.discard, hero, 0)
    return replace(
        regroup, discard=replace(regroup.discard, **{hero: max(0, prior - 1)})
    )


def increment_party(party: Party, hero: str) -> Party:
    """Increase the count of the specified hero type by one."""
    if party is None:
        raise DrollError("No party currently active.")
    return replace(party, **{hero: getattr(party, hero) + 1})


def defeat_all(
    world: World, randrange: RandRange, hero: str, target: str
) -> World:
    """Update world after hero handles all of one type of target."""
    return replace(
        world,
        dungeon=eliminate_dungeon(world.dungeon, target),
        party=_decrement_party(world.party, hero),
        regroup=_decrement_regroup(world.regroup, hero),
    )


def _defeat_plus_additional(
    world: World,
    randrange: RandRange,
    hero: str,
    additional: tuple,
) -> World:
    """After the initial defeat, optionally defeat one additional monster."""
    if defeated_monsters(world.dungeon):
        if additional:
            raise DrollError(
                f"Additional {additional} given but no monsters left."
            )
        return world

    if not additional:
        raise DrollError("Monsters remain so one additional target required.")
    if len(additional) > 1:
        raise DrollError(
            f"Only one additional target allowed but {len(additional)} provided."
        )

    return defeat_one(
        world=replace(world, party=increment_party(world.party, hero)),
        randrange=randrange,
        hero=hero,
        target=additional[0],
    )


def defeat_all_plus_additional(
    world: World,
    randrange: RandRange,
    hero: str,
    target: str,
    *additional,
) -> World:
    """Update world after hero handles all of one target type plus one more."""
    world = defeat_all(
        world=world, randrange=randrange, hero=hero, target=target
    )
    return _defeat_plus_additional(world, randrange, hero, additional)


def defeat_one_plus_additional(
    world: World,
    randrange: RandRange,
    hero: str,
    target: str,
    *additional,
) -> World:
    """Update world after hero handles one target plus one more."""
    world = defeat_one(
        world=world, randrange=randrange, hero=hero, target=target
    )
    return _defeat_plus_additional(world, randrange, hero, additional)


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
        party=_decrement_party(world.party, hero),
        regroup=_decrement_regroup(world.regroup, hero),
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
        party=_decrement_party(world.party, hero),
        regroup=_decrement_regroup(world.regroup, hero),
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

    Unlike {defend,open}_{one,all}(...), heroes to revive are arguments."""
    howmany = getattr(world.dungeon, target)
    if not howmany:
        raise DrollError(f"At least 1 {target} required.")
    if len(revivable) != howmany:
        raise DrollError(f"Exactly {howmany} heroes to revive required.")
    if after_monsters and not defeated_monsters(world.dungeon):
        raise DrollError("Monsters must be defeated before quaffing.")
    party = _decrement_party(world.party, hero)
    for revived in revivable:
        party = increment_party(party, revived)
    return replace(
        world,
        dungeon=eliminate_dungeon(world.dungeon, target),
        party=party,
        regroup=_decrement_regroup(world.regroup, hero),
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
    """Update world after hero re-rolls some number of dungeon or party dice."""
    if not dungeon_or_party:
        raise DrollError("At least 1 reroll target required.")

    dungeon_targets, party_targets = _classify_reroll_targets(
        dungeon_or_party, allow_dragon
    )

    # Decrement hero and regroup BEFORE any dice are rolled to prevent
    # stochastic exploitation: a rolled result cannot be immediately spent.
    party = _decrement_party(world.party, hero)
    regroup = _decrement_regroup(world.regroup, hero)

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
            party = _decrement_party(party, target)
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


def defeat_dragon_heroes(
    *heroes,
    _disallowed_heroes: Sequence[str] = ("scroll",),
    distinct_heroes: int = 3,
) -> bool:
    """Have sufficiently many distinct heroes been provided to slay dragon?

    Specifically, in the case when all heroes must be distinct.
    """
    hero_set = {*heroes}
    if hero_set & {*_disallowed_heroes}:
        raise DrollError(
            f"Heroes {_disallowed_heroes} cannot defeat a dragon."
        )
    if len(heroes) != distinct_heroes:
        raise DrollError(f"Exactly {distinct_heroes} heroes required.")
    if len(hero_set) != distinct_heroes:
        raise DrollError(
            f"The {distinct_heroes} heroes must all be distinct."
        )
    return True


def defeat_dragon_heroes_wildcard(
    *heroes,
    wildcard: Sequence[str] = ("scroll",),
    distinct_heroes: int = 3,
) -> bool:
    """Have sufficiently many distinct heroes been provided to slay dragon?

    Specifically, in the case when some hero is fungible for all others.
    """
    n_required = distinct_heroes  # Allow mutation saving original
    if len(heroes) != n_required:
        raise DrollError(f"Exactly {n_required} heroes required.")

    # Account for wildcards by having each wildcard reduce the distinct count
    non_wildcards = [hero for hero in heroes if hero not in wildcard]
    n_required -= len(heroes) - len(non_wildcards)
    heroes = non_wildcards

    if len({*heroes}) != n_required:
        raise DrollError(  # Error message uses original count
            f"The {distinct_heroes} heroes must all be distinct."
        )
    return True


def defeat_dragon_heroes_interchangeable(
    *heroes,
    interchangeable: set[str],
    _disallowed_heroes: Sequence[str] = ("scroll",),
    _required_heroes: int = 3,
) -> bool:
    """Have sufficiently many heroes been provided to slay dragon?

    Specifically, in the case when 'A may be used as B and B may be used as A'.
    """
    if {*heroes} & {*_disallowed_heroes}:
        raise DrollError(
            f"Heroes {_disallowed_heroes} cannot defeat a dragon."
        )
    if len(heroes) != _required_heroes:
        raise DrollError(f"Exactly {_required_heroes} heroes required.")

    # Count all heroes, accumulating all interchangeable into just one hero
    counter = Counter(heroes)
    ordered = sorted(interchangeable)
    assert len(ordered) > 0, "At least one interchangeable required."
    while len(ordered) > 1:
        counter[ordered[0]] += counter.pop(ordered.pop(), 0)

    # Permit no more than number of distinct interchangeable heroes.
    # For example, 'fighter fighter mage' is only two distinct types
    # even when fighters and mages are interchangeable.
    counter[ordered[0]] = min(
        counter[ordered[0]], len(interchangeable)
    )

    # Sum the number of distinct heroes observed after these coercions.
    distinct_heroes = sum(counter.values())
    if distinct_heroes != _required_heroes:
        raise DrollError(f"Heroes {heroes} not sufficiently distinct.")

    return True


def defeat_dragon(
    world: World,
    randrange: RandRange,
    hero: str,
    target: str,
    *others,
    defeat_dragon_heroes=defeat_dragon_heroes,  # What type hint?
    _min_dragon_length: int = 3,
) -> World:
    """Update world after hero handles a dragon using multiple distinct heroes.

    Additional required heroes are specified within variable-length others."""
    # Simple prerequisites for attempting to defeat the dragon
    if world.dungeon.dragon < _min_dragon_length:
        raise DrollError(
            f"Enemy {target} only comes at length {_min_dragon_length}."
        )
    if not defeated_monsters(world.dungeon):
        raise DrollError(
            f"Enemy {target} only comes after all others defeated."
        )

    # Confirm required number of distinct heroes available
    party = _decrement_party(world.party, hero)
    regroup = _decrement_regroup(world.regroup, hero)
    heroes = [hero]
    for other in others:
        party = _decrement_party(party, other)
        regroup = _decrement_regroup(regroup, other)
        heroes.append(other)
    if not defeat_dragon_heroes(*heroes):
        raise RuntimeError("Unexpected result from defeat_dragon_heroes")

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
    """Convert all monster faces into dragon dice."""
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
    world: World, randrange: RandRange, noun: str, target: str
) -> World:
    """Add one hero die of any requested type."""
    return replace(
        world,
        treasure=replace_treasure(world.treasure, noun),
        party=increment_party(world.party, target),
    )


def convert_dungeon_to_party(
    world: World,
    source: str,
    destination: str,
    max_count: int,
) -> World:
    """Convert up to max_count dungeon dice into party dice with regroup discard.

    Converts min(available, max_count) of source into destination."""
    count = min(getattr(world.dungeon, source), max_count)
    return replace(
        world,
        dungeon=replace(
            world.dungeon,
            **{source: getattr(world.dungeon, source) - count},
        ),
        party=replace(
            world.party,
            **{destination: getattr(world.party, destination) + count},
        ),
        regroup=replace(
            world.regroup,
            discard=replace(
                world.regroup.discard,
                **{
                    destination: getattr(world.regroup.discard, destination)
                    + count
                },
            ),
        ),
    )


def consume_ability(world: World):
    """Mark the hero's special ability as used."""
    if not world.ability:
        raise DrollError("Ability not available.")
    return replace(world, ability=False)


def nop_ability(
    world: World,
    randrange: RandRange,
    noun: str,
    target: Optional[str] = None,
) -> World:
    """No special ability available (though its consumption is tracked)"""
    if target is not None:
        raise DrollError(f"No targets accepted for {noun}.")
    return consume_ability(world)
