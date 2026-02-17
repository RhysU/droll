# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with player action mechanics."""

import collections
import collections.abc
from dataclasses import replace
import operator
import typing

from . import dice
from . import error
from . import struct
from .world import defeated_monsters, draw_treasure, replace_treasure

__all__ = (
    "bait_dragon",
    "consume_ability",
    "convert_dungeon_to_party",
    "decrement_dungeon",
    "defeat_all",
    "defeat_all_plus_additional",
    "defeat_one_plus_additional",
    "defeat_dragon",
    "defeat_dragon_heroes",
    "defeat_dragon_heroes_interchangeable",
    "defeat_dragon_heroes_wildcard",
    "defeat_one",
    "elixir",
    "eliminate_dungeon",
    "increment_dungeon",
    "increment_party",
    "nop_ability",
    "open_all",
    "open_one",
    "quaff",
    "reroll",
)


def defeat_one(
    world: struct.World, randrange: dice.RandRange, hero: str, target: str
) -> struct.World:
    """Update world after hero handles exactly one target."""
    return replace(
        world,
        dungeon=decrement_dungeon(world.dungeon, target),
        party=_decrement_party(world.party, hero),
        regroup=_decrement_regroup(world.regroup, hero),
    )


# Private because it must be used with _decrement_regroup for correctness
def _decrement_party(party: struct.Party, hero: str) -> struct.Party:
    """Decrease the count of the specified hero type by one."""
    if party is None:
        raise error.DrollError("No party currently active.")
    prior_heroes = getattr(party, hero)
    if not prior_heroes:
        raise error.DrollError(f"Require at least one hero {hero}.")
    return replace(party, **{hero: prior_heroes - 1})


# Private because it must be used with _decrement_party for correctness
def _decrement_regroup(regroup: struct.Regroup, hero: str) -> struct.Regroup:
    """Decrement the regroup discard counter for hero, if positive."""
    prior = getattr(regroup.discard, hero, 0)
    return replace(
        regroup, discard=replace(regroup.discard, **{hero: max(0, prior - 1)})
    )


def decrement_dungeon(dungeon: struct.Dungeon, target: str) -> struct.Dungeon:
    """Decrease the count of the specified target type by one."""
    if dungeon is None:
        raise error.DrollError("No dungeon currently active.")
    prior_targets = getattr(dungeon, target)
    if not prior_targets:
        raise error.DrollError(f"Require at least one target {target}.")
    return replace(dungeon, **{target: prior_targets - 1})


def increment_party(party: struct.Party, hero: str) -> struct.Party:
    """Increase the count of the specified hero type by one."""
    if party is None:
        raise error.DrollError("No party currently active.")
    return replace(party, **{hero: getattr(party, hero) + 1})


def increment_dungeon(dungeon: struct.Dungeon, target: str) -> struct.Dungeon:
    """Increase the count of the specified target type by one."""
    if dungeon is None:
        raise error.DrollError("No dungeon currently active.")
    prior_targets = getattr(dungeon, target, 0)
    return replace(dungeon, **{target: prior_targets + 1})


def defeat_all(
    world: struct.World, randrange: dice.RandRange, hero: str, target: str
) -> struct.World:
    """Update world after hero handles all of one type of target."""
    return replace(
        world,
        dungeon=eliminate_dungeon(world.dungeon, target),
        party=_decrement_party(world.party, hero),
        regroup=_decrement_regroup(world.regroup, hero),
    )


def _defeat_plus_additional(
    world: struct.World,
    randrange: dice.RandRange,
    hero: str,
    additional: tuple,
) -> struct.World:
    """After the initial defeat, optionally defeat one additional monster."""
    if defeated_monsters(world.dungeon):
        if additional:
            raise error.DrollError(
                f"Additional {additional} given but no monsters left."
            )
        return world

    if not additional:
        raise error.DrollError(
            "Monsters remain so one additional target required."
        )
    if len(additional) > 1:
        raise error.DrollError(
            f"Only one additional target allowed but {len(additional)} provided."
        )

    return defeat_one(
        world=replace(world, party=increment_party(world.party, hero)),
        randrange=randrange,
        hero=hero,
        target=additional[0],
    )


def defeat_all_plus_additional(
    world: struct.World,
    randrange: dice.RandRange,
    hero: str,
    target: str,
    *additional,
) -> struct.World:
    """Update world after hero handles all of one target type plus one more."""
    world = defeat_all(
        world=world, randrange=randrange, hero=hero, target=target
    )
    return _defeat_plus_additional(world, randrange, hero, additional)


def defeat_one_plus_additional(
    world: struct.World,
    randrange: dice.RandRange,
    hero: str,
    target: str,
    *additional,
) -> struct.World:
    """Update world after hero handles one target plus one more."""
    world = defeat_one(
        world=world, randrange=randrange, hero=hero, target=target
    )
    return _defeat_plus_additional(world, randrange, hero, additional)


def eliminate_dungeon(dungeon: struct.Dungeon, target: str) -> struct.Dungeon:
    """Remove all targets of the specified type from the dungeon."""
    if dungeon is None:
        raise error.DrollError("No dungeon currently active.")
    prior_targets = getattr(dungeon, target)
    if not prior_targets:
        raise error.DrollError(f"Require at least 1 target {target}.")
    return replace(dungeon, **{target: 0})


def open_one(
    world: struct.World,
    randrange: dice.RandRange,
    hero: str,
    target: str,
    *,
    _after_monsters=True,
) -> struct.World:
    """Update world after hero opens exactly one chest."""
    if _after_monsters and not defeated_monsters(world.dungeon):
        raise error.DrollError("Monsters must be defeated before opening.")
    return replace(
        draw_treasure(world, randrange),
        dungeon=decrement_dungeon(world.dungeon, target),
        party=_decrement_party(world.party, hero),
        regroup=_decrement_regroup(world.regroup, hero),
    )


def open_all(
    world: struct.World,
    randrange: dice.RandRange,
    hero: str,
    target: str,
    *,
    _after_monsters=True,
) -> struct.World:
    """Update world after hero opens all chests."""
    if _after_monsters and not defeated_monsters(world.dungeon):
        raise error.DrollError("Monsters must be defeated before opening.")
    howmany = getattr(world.dungeon, target)
    if not howmany:
        raise error.DrollError(f"At least 1 {target} required.")
    for _ in range(howmany):
        world = draw_treasure(world, randrange)
    return replace(
        world,
        dungeon=eliminate_dungeon(world.dungeon, target),
        party=_decrement_party(world.party, hero),
        regroup=_decrement_regroup(world.regroup, hero),
    )


def quaff(
    world: struct.World,
    randrange: dice.RandRange,
    hero: str,
    target: str,
    *revivable,
    _after_monsters=True,
) -> struct.World:
    """Update world after hero quaffs all available potions.

    Unlike {defend,open}_{one,all}(...), heroes to revive are arguments."""
    howmany = getattr(world.dungeon, target)
    if not howmany:
        raise error.DrollError(f"At least 1 {target} required.")
    if len(revivable) != howmany:
        raise error.DrollError(f"Require exactly {howmany} to revive.")
    if _after_monsters and not defeated_monsters(world.dungeon):
        raise error.DrollError("Monsters must be defeated before quaffing.")
    party = _decrement_party(world.party, hero)
    for revived in revivable:
        party = increment_party(party, revived)
    return replace(
        world,
        dungeon=eliminate_dungeon(world.dungeon, target),
        party=party,
        regroup=_decrement_regroup(world.regroup, hero),
    )


def reroll(
    world: struct.World,
    randrange: dice.RandRange,
    hero: str,
    *dungeon_or_party,
    allow_dragon: bool = False,
) -> struct.World:
    """Update world after hero re-rolls some number of dungeon or party dice."""
    if not dungeon_or_party:
        raise error.DrollError("At least one target must be re-rolled.")

    # Classify each target as either a dungeon or party die
    dungeon_names = frozenset(struct.field_names(struct.Dungeon))
    party_names = frozenset(struct.field_names(struct.Party))
    dungeon_targets = []
    party_targets = []
    for target in dungeon_or_party:
        if not allow_dragon and target == "dragon":
            raise error.DrollError(f"{target} cannot be re-rolled")
        if target in dungeon_names:
            dungeon_targets.append(target)
        elif target in party_names:
            party_targets.append(target)
        else:
            raise error.DrollError(f"{target} cannot be re-rolled")

    # Remove requested targets from the dungeon
    dungeon = world.dungeon
    for target in dungeon_targets:
        dungeon = decrement_dungeon(dungeon, target)

    # Re-roll dungeon dice and add to anything left fixed
    if dungeon_targets:
        increased = dice.roll_dungeon(dice=len(dungeon_targets), randrange=randrange)
        dungeon = struct.Dungeon(
            *map(
                operator.add,
                struct.field_values(dungeon),
                struct.field_values(increased),
            )
        )

    # Remove requested targets from the party
    party = world.party
    for target in party_targets:
        party = _decrement_party(party, target)

    # Re-roll party dice and add to anything left fixed
    if party_targets:
        increased, _ = dice.roll_party(dice=len(party_targets), randrange=randrange)
        party = struct.Party(
            *map(
                operator.add,
                struct.field_values(party),
                struct.field_values(increased),
            )
        )

    # Consume the hero and update regroup
    return replace(
        world,
        dungeon=dungeon,
        party=_decrement_party(party, hero),
        regroup=_decrement_regroup(world.regroup, hero),
    )


def defeat_dragon_heroes(
    *heroes,
    _disallowed_heroes: collections.abc.Sequence[str] = ("scroll",),
    _distinct_heroes: int = 3,
) -> bool:
    """Have sufficiently many distinct heroes been provided to slay dragon?

    Specifically, in the case when all heroes must be distinct.
    """
    hero_set = {*heroes}
    if hero_set & {*_disallowed_heroes}:
        raise error.DrollError(
            f"Heroes {_disallowed_heroes} cannot defeat a dragon."
        )
    if len(heroes) != _distinct_heroes:
        raise error.DrollError(
            f"Exactly {_distinct_heroes} heroes must be specified."
        )
    if len(hero_set) != _distinct_heroes:
        raise error.DrollError(
            f"The {_distinct_heroes} heroes must all be distinct."
        )
    return True


def defeat_dragon_heroes_wildcard(
    *heroes,
    _wildcard: collections.abc.Sequence[str] = ("scroll",),
    _distinct_heroes: int = 3,
) -> bool:
    """Have sufficiently many distinct heroes been provided to slay dragon?

    Specifically, in the case when some hero is fungible for all others.
    """
    distinct_heroes = _distinct_heroes  # Allow mutation saving original
    if len(heroes) != distinct_heroes:
        raise error.DrollError(
            f"Exactly {distinct_heroes} heroes must be specified."
        )

    # Account for wildcards by having each wildcard reduce the distinct count
    non_wildcards = [hero for hero in heroes if hero not in _wildcard]
    distinct_heroes -= len(heroes) - len(non_wildcards)
    heroes = non_wildcards

    if len({*heroes}) != distinct_heroes:
        raise error.DrollError(  # Error message uses original count
            f"The {_distinct_heroes} heroes must all be distinct."
        )
    return True


def defeat_dragon_heroes_interchangeable(
    *heroes,
    _interchangeable: set[str],
    _disallowed_heroes: collections.abc.Sequence[str] = ("scroll",),
    _required_heroes: int = 3,
) -> bool:
    """Have sufficiently many heroes been provided to slay dragon?

    Specifically, in the case when 'A may be used as B and B may be used as A'.
    """
    if {*heroes} & {*_disallowed_heroes}:
        raise error.DrollError(
            f"Heroes {_disallowed_heroes} cannot defeat a dragon."
        )
    if len(heroes) != _required_heroes:
        raise error.DrollError(
            f"Exactly {_required_heroes} heroes must be specified."
        )

    # Count all heroes, accumulating all _interchangable into just one hero
    counter = collections.Counter(heroes)
    interchangeable = sorted(_interchangeable)
    assert len(interchangeable) > 0, "At least one interchangeable required."
    while len(interchangeable) > 1:
        counter[interchangeable[0]] += counter.pop(interchangeable.pop(), 0)

    # Permit no more than number of distinct interchangeable heroes.
    # For example, 'fighter fighter mage' is only two distinct types
    # even when fighters and mages are interchangeable.
    counter[interchangeable[0]] = min(
        counter[interchangeable[0]], len(_interchangeable)
    )

    # Sum the number of distinct heroes observed after these coercions.
    distinct_heroes = sum(counter.values())
    if distinct_heroes != _required_heroes:
        raise error.DrollError(f"Heroes {heroes} not sufficiently distinct.")

    return True


def defeat_dragon(
    world: struct.World,
    randrange: dice.RandRange,
    hero: str,
    target: str,
    *others,
    _defeat_dragon_heroes=defeat_dragon_heroes,  # What type hint?
    _min_dragon_length: int = 3,
) -> struct.World:
    """Update world after hero handles a dragon using multiple distinct heroes.

    Additional required heroes are specified within variable-length others."""
    # Simple prerequisites for attempting to defeat the dragon
    if world.dungeon.dragon < _min_dragon_length:
        raise error.DrollError(
            f"Enemy {target} only comes at length {_min_dragon_length}."
        )
    if not defeated_monsters(world.dungeon):
        raise error.DrollError(
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
    if not _defeat_dragon_heroes(*heroes):
        raise RuntimeError("Unexpected result from _defeat_dragon_heroes")

    # Attempt was successful, so update experience and treasure
    return replace(
        draw_treasure(world, randrange),
        experience=world.experience + 1,
        party=party,
        dungeon=eliminate_dungeon(world.dungeon, target),
        regroup=regroup,
    )


def bait_dragon(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: typing.Optional[str] = None,
    *,
    _enemies: collections.abc.Sequence[str] = ("goblin", "skeleton", "ooze"),
    _require_treasure: bool = True,
) -> struct.World:
    """Convert all monster faces into dragon dice."""
    # Confirm well-formed request optionally containing a target
    target = "dragon" if target is None else target
    if target != "dragon":
        raise error.DrollError(f"Cannot {noun} a {target}.")
    if _require_treasure:
        world = replace_treasure(world, noun)

    # Compute how many new dragons will be produced and remove sources
    new_targets = 0
    dungeon = world.dungeon
    if dungeon is not None:
        for enemy in _enemies:
            new_targets += getattr(world.dungeon, enemy)
            dungeon = replace(dungeon, **{enemy: 0})
    if not new_targets:
        raise error.DrollError(
            f"At least one of {_enemies} required for '{noun}'."
        )

    # Increment the number of targets (i.e. dragons)
    return replace(
        world,
        dungeon=replace(
            dungeon, **{target: getattr(dungeon, target) + new_targets}
        ),
    )


def elixir(
    world: struct.World, randrange: dice.RandRange, noun: str, target: str
) -> struct.World:
    """Add one hero die of any requested type."""
    return replace(
        replace_treasure(world, noun),
        party=increment_party(world.party, target),
    )


def convert_dungeon_to_party(
    world: struct.World,
    source: str,
    destination: str,
    max_count: int,
) -> struct.World:
    """Convert up to max_count dungeon dice into party dice with regroup discard.

    Converts min(available, max_count) of source into destination."""
    dungeon = world.dungeon
    party = world.party
    discard = world.regroup.discard
    available = getattr(dungeon, source)
    count = min(available, max_count)
    for _ in range(count):
        dungeon = decrement_dungeon(dungeon, source)
        party = increment_party(party, destination)
    discard = replace(
        discard, **{destination: getattr(discard, destination) + count}
    )
    return replace(
        world,
        dungeon=dungeon,
        party=party,
        regroup=replace(world.regroup, discard=discard),
    )


def consume_ability(world: struct.World):
    """Mark the hero's special ability as used."""
    if not world.ability:
        raise error.DrollError("Ability not available for use.")
    return replace(world, ability=False)


def nop_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: typing.Optional[str] = None,
) -> struct.World:
    """No special ability available (though its consumption is tracked)"""
    if target is not None:
        raise error.DrollError(f"No targets accepted for {noun}.")
    return consume_ability(world)
