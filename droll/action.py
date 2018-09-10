# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with player action mechanics."""

import operator
import typing

from .error import DrollError
from .world import (Dungeon, RandRange, Party, World,
                    defeated_monsters, blocking_dragon, apply_ring,
                    draw_treasure, next_dungeon, replace_treasure, roll_dungeon)


def defeat_one(
        world: World, randrange: RandRange, hero: str, target: str
) -> World:
    """Update world after hero handles exactly one target."""
    return world._replace(
        party=__decrement_hero(world.party, hero),
        dungeon=__decrement_target(world.dungeon, target)
    )


def __decrement_hero(party: Party, hero: str) -> Party:
    prior_heroes = getattr(party, hero)
    if not prior_heroes:
        raise DrollError("Require at least one hero {}".format(hero))
    return party._replace(**{hero: prior_heroes - 1})


def __increment_hero(party: Party, hero: str) -> Party:
    return party._replace(**{hero: getattr(party, hero) + 1})


def __decrement_target(dungeon: Dungeon, target: str) -> Dungeon:
    prior_targets = getattr(dungeon, target)
    if not prior_targets:
        raise ValueError("Require at least one target {}".format(target))
    return dungeon._replace(**{target: prior_targets - 1})


def defeat_all(
        world: World, randrange: RandRange, hero: str, target: str
) -> World:
    """Update world after hero handles all of one type of target."""
    return world._replace(
        party=__decrement_hero(world.party, hero),
        dungeon=__eliminate_targets(world.dungeon, target)
    )


def __eliminate_targets(dungeon: Dungeon, target: str) -> Dungeon:
    prior_targets = getattr(dungeon, target)
    if not prior_targets:
        raise DrollError("Require at least one target {}".format(target))
    return dungeon._replace(**{target: 0})


def open_one(
        world: World, randrange: RandRange, hero: str, target: str,
        after_monsters=True,
) -> World:
    """Update world after hero opens exactly one chest."""
    if after_monsters and not defeated_monsters(world.dungeon):
        raise DrollError("Monsters must be defeated before opening.")
    return draw_treasure(world, randrange)._replace(
        party=__decrement_hero(world.party, hero),
        dungeon=__decrement_target(world.dungeon, target)
    )


def open_all(
        world: World, randrange: RandRange, hero: str, target: str,
        after_monsters=True,
) -> World:
    """Update world after hero opens all chests."""
    if after_monsters and not defeated_monsters(world.dungeon):
        raise DrollError("Monsters must be defeated before opening.")
    howmany = getattr(world.dungeon, target)
    if not howmany:
        raise DrollError("At least 1 {} required".format(target))
    for _ in range(howmany):
        world = draw_treasure(world, randrange)
    return world._replace(
        party=__decrement_hero(world.party, hero),
        dungeon=__eliminate_targets(world.dungeon, target),
    )


def quaff(
        world: World, randrange: RandRange, hero: str, target: str, *revivable,
        after_monsters=True
) -> World:
    """Update world after hero quaffs all available potions.

    Unlike {defend,open}_{one,all}(...), heroes to revive are arguments."""
    howmany = getattr(world.dungeon, target)
    if not howmany:
        raise DrollError("At least 1 {} required".format(target))
    if len(revivable) != howmany:
        raise DrollError("Require exactly {} to revive".format(howmany))
    if after_monsters and not defeated_monsters(world.dungeon):
        raise DrollError("Monsters must be defeated before quaffing.")
    party = __decrement_hero(world.party, hero)
    for revived in revivable:
        party = __increment_hero(party, revived)
    return world._replace(
        party=party,
        dungeon=__eliminate_targets(world.dungeon, target)
    )


def reroll(
        world: World, randrange: RandRange, hero: str, *targets
) -> World:
    """Update world after hero rerolls some number of targets."""
    if not targets:
        raise DrollError('At least one target must be re-rolled.')

    # Remove requested target from the dungeon
    reduced = world.dungeon
    for target in targets:
        if target in {'potion', 'dragon'}:
            raise DrollError("{} cannot be rerolled".format(target))
        reduced = __decrement_target(reduced, target)

    # Re-roll the necessary number of dice then add to anything left fixed
    increased = roll_dungeon(dice=len(targets), randrange=randrange)
    return world._replace(
        party=__decrement_hero(world.party, hero),
        dungeon=Dungeon(*tuple(map(operator.add, reduced, increased)))
    )


def defeat_dragon(
        world: World, randrange: RandRange, hero: str, target: str, *others,
        disallowed_heroes: typing.Iterable[str] = ('scroll'),
        min_length: int = 3,
        min_heroes: int = 3
) -> World:
    """Update world after hero handles a dragon using multiple distinct heroes.

    Additional required heroes are specified within variable-length others."""
    # Simple prerequisites for attempting to defeat the dragon
    if world.dungeon.dragon < min_length:
        raise DrollError("Enemy {} only comes at length {}"
                         .format(target, min_length))
    if not defeated_monsters(world.dungeon):
        raise DrollError("Enemy {} only comes after all others defeated."
                         .format(target))
    if len(others) != min_heroes - 1:
        raise DrollError("A total of {} heroes must be specified."
                         .format(min_heroes))

    # Confirm required number of distinct heroes available
    party = __decrement_hero(world.party, hero)
    distinct_heroes = {hero}
    for other in others:
        party = __decrement_hero(party, other)
        distinct_heroes.add(other)
    if len(distinct_heroes) != min_heroes:
        raise DrollError("The {} heroes must all be distinct")
    if distinct_heroes & set(disallowed_heroes):
        raise DrollError("Heroes {} cannot defeat {}"
                         .format(disallowed_heroes, target))

    # Attempt was successful, so update experience and treasure
    return draw_treasure(world, randrange)._replace(
        experience=world.experience + 1,
        party=party,
        dungeon=__eliminate_targets(world.dungeon, target)
    )


def bait_dragon(
        world: World, randrange: RandRange, noun: str,
        target: typing.Optional[str] = None,
        *,
        enemies: typing.Sequence[str] = ('goblin', 'skeleton', 'ooze')
) -> World:
    """Convert all monster faces into dragon dice."""
    # Confirm well-formed request optionally containing a target
    target = 'dragon' if target is None else target
    if target != 'dragon':
        raise DrollError('Cannot {} a {}'.format(noun, target))
    world = replace_treasure(world, noun)

    # Compute how many new dragons will be produced and remove sources
    new_targets = 0
    dungeon = world.dungeon
    for enemy in enemies:
        new_targets += getattr(world.dungeon, enemy)
        dungeon = dungeon._replace(**{enemy: 0})
    if not new_targets:
        raise DrollError("At least one of {} required for '{}'"
                         .format(enemies, noun))

    # Increment the number of targets (i.e. dragons)
    return world._replace(
        dungeon=dungeon._replace(
            **{target: getattr(dungeon, target) + new_targets})
    )


def ring(
        world: World, randrange: RandRange, noun: str,
        target: typing.Optional[str] = None,
) -> World:
    """Use a ring of invisibility to sneak past a dragon."""
    target = 'dragon' if target is None else target
    if target != 'dragon':
        raise DrollError('Cannot {} a {}'.format(noun, target))
    return apply_ring(world=world, noun=noun)


def elixir(
        world: World, randrange: RandRange, noun: str, target: str
) -> World:
    """Add one hero die of any requested type."""
    return replace_treasure(world, noun)._replace(
        party=__increment_hero(world.party, target)
    )
