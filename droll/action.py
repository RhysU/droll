# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with player action mechanics."""

import operator
import typing

from . import dice
from . import error
from . import struct
from . import world


def defeat_one(
        game: struct.World, randrange: dice.RandRange, hero: str, target: str
) -> struct.World:
    """Update game after hero handles exactly one target."""
    return game._replace(
        party=__decrement_hero(game.party, hero),
        dungeon=__decrement_target(game.dungeon, target)
    )


def __decrement_hero(party: struct.Party, hero: str) -> struct.Party:
    prior_heroes = getattr(party, hero)
    if not prior_heroes:
        raise error.DrollError("Require at least one hero {}".format(hero))
    return party._replace(**{hero: prior_heroes - 1})


def __increment_hero(party: struct.Party, hero: str) -> struct.Party:
    return party._replace(**{hero: getattr(party, hero) + 1})


def __decrement_target(dungeon: struct.Dungeon, target: str) -> struct.Dungeon:
    prior_targets = getattr(dungeon, target)
    if not prior_targets:
        raise ValueError("Require at least one target {}".format(target))
    return dungeon._replace(**{target: prior_targets - 1})


def defeat_all(
        game: struct.World, randrange: dice.RandRange, hero: str, target: str
) -> struct.World:
    """Update game after hero handles all of one type of target."""
    return game._replace(
        party=__decrement_hero(game.party, hero),
        dungeon=__eliminate_targets(game.dungeon, target)
    )


def __eliminate_targets(
        dungeon: struct.Dungeon, target: str
) -> struct.Dungeon:
    prior_targets = getattr(dungeon, target)
    if not prior_targets:
        raise error.DrollError("Require at least one target {}".format(target))
    return dungeon._replace(**{target: 0})


def open_one(
        game: struct.World, randrange: dice.RandRange, hero: str, target: str,
        *, _after_monsters=True
) -> struct.World:
    """Update game after hero opens exactly one chest."""
    if _after_monsters and not world.defeated_monsters(game.dungeon):
        raise error.DrollError("Monsters must be defeated before opening.")
    return world.draw_treasure(game, randrange)._replace(
        party=__decrement_hero(game.party, hero),
        dungeon=__decrement_target(game.dungeon, target)
    )


def open_all(
        game: struct.World, randrange: dice.RandRange, hero: str, target: str,
        *, _after_monsters=True
) -> struct.World:
    """Update game after hero opens all chests."""
    if _after_monsters and not world.defeated_monsters(game.dungeon):
        raise error.DrollError("Monsters must be defeated before opening.")
    howmany = getattr(game.dungeon, target)
    if not howmany:
        raise error.DrollError("At least 1 {} required".format(target))
    for _ in range(howmany):
        game = world.draw_treasure(game, randrange)
    return game._replace(
        party=__decrement_hero(game.party, hero),
        dungeon=__eliminate_targets(game.dungeon, target),
    )


def quaff(
        game: struct.World, randrange: dice.RandRange, hero: str, target: str,
        *revivable, _after_monsters=True
) -> struct.World:
    """Update game after hero quaffs all available potions.

    Unlike {defend,open}_{one,all}(...), heroes to revive are arguments."""
    howmany = getattr(game.dungeon, target)
    if not howmany:
        raise error.DrollError("At least 1 {} required".format(target))
    if len(revivable) != howmany:
        raise error.DrollError("Require exactly {} to revive".format(howmany))
    if _after_monsters and not world.defeated_monsters(game.dungeon):
        raise error.DrollError("Monsters must be defeated before quaffing.")
    party = __decrement_hero(game.party, hero)
    for revived in revivable:
        party = __increment_hero(party, revived)
    return game._replace(
        party=party,
        dungeon=__eliminate_targets(game.dungeon, target)
    )


def reroll(
        game: struct.World, randrange: dice.RandRange, hero: str, *targets
) -> struct.World:
    """Update game after hero rerolls some number of targets."""
    if not targets:
        raise error.DrollError('At least one target must be re-rolled.')

    # Remove requested target from the dungeon
    reduced = game.dungeon
    for target in targets:
        if target in {'potion', 'dragon'}:
            raise error.DrollError("{} cannot be rerolled".format(target))
        reduced = __decrement_target(reduced, target)

    # Re-roll the necessary number of dice then add to anything left fixed
    increased = dice.roll_dungeon(dice=len(targets), randrange=randrange)
    return game._replace(
        party=__decrement_hero(game.party, hero),
        dungeon=struct.Dungeon(*tuple(map(operator.add, reduced, increased)))
    )


def defeat_dragon(
        game: struct.World, randrange: dice.RandRange, hero: str, target: str,
        *others,
        _disallowed_heroes: typing.Iterable[str] = ('scroll'),
        _min_length: int = 3,
        _min_heroes: int = 3
) -> struct.World:
    """Update game after hero handles a dragon using multiple distinct heroes.

    Additional required heroes are specified within variable-length others."""
    # Simple prerequisites for attempting to defeat the dragon
    if game.dungeon.dragon < _min_length:
        raise error.DrollError("Enemy {} only comes at length {}"
                               .format(target, _min_length))
    if not world.defeated_monsters(game.dungeon):
        raise error.DrollError("Enemy {} only comes after all others defeated."
                               .format(target))
    if len(others) != _min_heroes - 1:
        raise error.DrollError("A total of {} heroes must be specified."
                               .format(_min_heroes))

    # Confirm required number of distinct heroes available
    party = __decrement_hero(game.party, hero)
    distinct_heroes = {hero}
    for other in others:
        party = __decrement_hero(party, other)
        distinct_heroes.add(other)
    if len(distinct_heroes) != _min_heroes:
        raise error.DrollError("The {} heroes must all be distinct")
    if distinct_heroes & set(_disallowed_heroes):
        raise error.DrollError("Heroes {} cannot defeat {}"
                               .format(_disallowed_heroes, target))

    # Attempt was successful, so update experience and treasure
    return world.draw_treasure(game, randrange)._replace(
        experience=game.experience + 1,
        party=party,
        dungeon=__eliminate_targets(game.dungeon, target)
    )


def bait_dragon(
        game: struct.World, randrange: dice.RandRange, noun: str,
        target: typing.Optional[str] = None,
        *,
        _enemies: typing.Sequence[str] = ('goblin', 'skeleton', 'ooze'),
        _require_treasure: bool = True
) -> struct.World:
    """Convert all monster faces into dragon dice."""
    # Confirm well-formed request optionally containing a target
    target = 'dragon' if target is None else target
    if target != 'dragon':
        raise error.DrollError('Cannot {} a {}'.format(noun, target))
    if _require_treasure:
        game = world.replace_treasure(game, noun)

    # Compute how many new dragons will be produced and remove sources
    new_targets = 0
    dungeon = game.dungeon
    if dungeon is not None:
        for enemy in _enemies:
            new_targets += getattr(game.dungeon, enemy)
            dungeon = dungeon._replace(**{enemy: 0})
    if not new_targets:
        raise error.DrollError("At least one of {} required for '{}'"
                               .format(_enemies, noun))

    # Increment the number of targets (i.e. dragons)
    return game._replace(
        dungeon=dungeon._replace(
            **{target: getattr(dungeon, target) + new_targets})
    )


def ring(
        game: struct.World, randrange: dice.RandRange, noun: str,
        target: typing.Optional[str] = None,
) -> struct.World:
    """Use a ring of invisibility to sneak past a dragon."""
    target = 'dragon' if target is None else target
    if target != 'dragon':
        raise error.DrollError('Cannot {} a {}'.format(noun, target))
    return world.apply_ring(world=game, noun=noun)


def portal(
        game: struct.World, randrange: dice.RandRange, noun: str,
        target: typing.Optional[str] = None,
) -> struct.World:
    """Use a town portal towards retiring to town.

    Automatically starts a new delve, if possible."""
    if target is not None:
        raise error.DrollError('No targets accepted for {}'.format(noun))
    game = world.retire(world.apply_portal(world=game, noun=noun))
    try:
        game = world.next_delve(world=game, randrange=randrange)
    except error.DrollError:
        pass
    return game


def elixir(
        game: struct.World, randrange: dice.RandRange, noun: str, target: str
) -> struct.World:
    """Add one hero die of any requested type."""
    return world.replace_treasure(game, noun)._replace(
        party=__increment_hero(game.party, target)
    )


def __consume_ability(game: struct.World):
    if not game.ability:
        raise error.DrollError("Ability not available for use.")
    return game._replace(ability=False)


def nop_ability(
        game: struct.World, randrange: dice.RandRange, noun: str,
        target: typing.Optional[str] = None,
) -> struct.World:
    """No special ability available (though its consumption is tracked)"""
    if target is not None:
        raise error.DrollError('No targets accepted for {}'.format(noun))
    return __consume_ability(game)
