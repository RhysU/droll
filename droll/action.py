# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with player action mechanics."""

import collections
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
        dungeon=__decrement_target(game.dungeon, target),
    )


def __decrement_hero(party: struct.Party, hero: str) -> struct.Party:
    if party is None:
        raise error.DrollError("No party currently active.")
    prior_heroes = getattr(party, hero)
    if not prior_heroes:
        raise error.DrollError("Require at least one hero {}.".format(hero))
    return party._replace(**{hero: prior_heroes - 1})


def __increment_hero(party: struct.Party, hero: str) -> struct.Party:
    if party is None:
        raise error.DrollError("No party currently active.")
    return party._replace(**{hero: getattr(party, hero) + 1})


def __decrement_target(dungeon: struct.Dungeon, target: str) -> struct.Dungeon:
    if dungeon is None:
        raise error.DrollError("No dungeon currently active.")
    prior_targets = getattr(dungeon, target)
    if not prior_targets:
        raise ValueError("Require at least one target {}.".format(target))
    return dungeon._replace(**{target: prior_targets - 1})


def defeat_all(
    game: struct.World, randrange: dice.RandRange, hero: str, target: str
) -> struct.World:
    """Update game after hero handles all of one type of target."""
    return game._replace(
        party=__decrement_hero(game.party, hero),
        dungeon=__eliminate_targets(game.dungeon, target),
    )


def defeat_all_plus_additional(
    game: struct.World,
    randrange: dice.RandRange,
    hero: str,
    target: str,
    *additional
) -> struct.World:
    """Update game after hero handles all of one target type plus one more."""
    # First, defeat all of the specified target
    game = defeat_all(game=game, randrange=randrange, hero=hero, target=target)

    # Second, determine if additional should not have been supplied
    if world.defeated_monsters(game.dungeon):
        if additional:
            raise error.DrollError(
                "Additional {} given but no monsters left.".format(additional)
            )
        return game

    # Third, confirm at most one additional provided
    if len(additional) != 1:
        raise error.DrollError(
            "One additional target okay but {} provided.".format(additional)
        )

    # Last, attempt to defeat the additional monster using the same hero
    return defeat_one(
        game=game._replace(party=__increment_hero(game.party, hero)),
        randrange=randrange,
        hero=hero,
        target=additional[0],
    )


def __eliminate_targets(dungeon: struct.Dungeon, target: str) -> struct.Dungeon:
    if dungeon is None:
        raise error.DrollError("No dungeon currently active.")
    prior_targets = getattr(dungeon, target)
    if not prior_targets:
        raise error.DrollError("Require at least one target {}.".format(target))
    return dungeon._replace(**{target: 0})


def open_one(
    game: struct.World,
    randrange: dice.RandRange,
    hero: str,
    target: str,
    *,
    _after_monsters=True
) -> struct.World:
    """Update game after hero opens exactly one chest."""
    if _after_monsters and not world.defeated_monsters(game.dungeon):
        raise error.DrollError("Monsters must be defeated before opening.")
    return world.draw_treasure(game, randrange)._replace(
        party=__decrement_hero(game.party, hero),
        dungeon=__decrement_target(game.dungeon, target),
    )


def open_all(
    game: struct.World,
    randrange: dice.RandRange,
    hero: str,
    target: str,
    *,
    _after_monsters=True
) -> struct.World:
    """Update game after hero opens all chests."""
    if _after_monsters and not world.defeated_monsters(game.dungeon):
        raise error.DrollError("Monsters must be defeated before opening.")
    howmany = getattr(game.dungeon, target)
    if not howmany:
        raise error.DrollError("At least 1 {} required.".format(target))
    for _ in range(howmany):
        game = world.draw_treasure(game, randrange)
    return game._replace(
        party=__decrement_hero(game.party, hero),
        dungeon=__eliminate_targets(game.dungeon, target),
    )


def quaff(
    game: struct.World,
    randrange: dice.RandRange,
    hero: str,
    target: str,
    *revivable,
    _after_monsters=True
) -> struct.World:
    """Update game after hero quaffs all available potions.

    Unlike {defend,open}_{one,all}(...), heroes to revive are arguments."""
    howmany = getattr(game.dungeon, target)
    if not howmany:
        raise error.DrollError("At least 1 {} required.".format(target))
    if len(revivable) != howmany:
        raise error.DrollError("Require exactly {} to revive.".format(howmany))
    if _after_monsters and not world.defeated_monsters(game.dungeon):
        raise error.DrollError("Monsters must be defeated before quaffing.")
    party = __decrement_hero(game.party, hero)
    for revived in revivable:
        party = __increment_hero(party, revived)
    return game._replace(
        party=party, dungeon=__eliminate_targets(game.dungeon, target)
    )


def reroll(
    game: struct.World, randrange: dice.RandRange, hero: str, *targets
) -> struct.World:
    """Update game after hero re-rolls some number of targets."""
    if not targets:
        raise error.DrollError("At least one target must be re-rolled.")

    # Remove requested target from the dungeon
    reduced = game.dungeon
    for target in targets:
        if target in {"potion", "dragon"}:
            raise error.DrollError("{} cannot be re-rolled".format(target))
        reduced = __decrement_target(reduced, target)

    # Re-roll the necessary number of dice then add to anything left fixed
    increased = dice.roll_dungeon(dice=len(targets), randrange=randrange)
    return game._replace(
        party=__decrement_hero(game.party, hero),
        dungeon=struct.Dungeon(*tuple(map(operator.add, reduced, increased))),
    )


def defeat_dragon_heroes(
    *heroes,
    _disallowed_heroes: typing.Sequence[str] = ("scroll",),
    _distinct_heroes: int = 3
) -> bool:
    """Have sufficiently many distinct heroes been provided to slay dragon?

    Specifically, in the case when all heroes must be distinct.
    """
    if {*heroes} & {*_disallowed_heroes}:
        raise error.DrollError(
            "Heroes {} cannot defeat a dragon.".format(_disallowed_heroes)
        )
    if len(heroes) != _distinct_heroes:
        raise error.DrollError(
            "Exactly {} heroes must be specified.".format(_distinct_heroes)
        )
    if len({*heroes}) != _distinct_heroes:
        raise error.DrollError(
            "The {} heroes must all be distinct.".format(_distinct_heroes)
        )
    return True


def defeat_dragon_heroes_interchangeable(
    *heroes,
    _interchangeable: typing.Set[str],
    _disallowed_heroes: typing.Sequence[str] = ("scroll",),
    _required_heroes: int = 3
) -> bool:
    """Have sufficiently many heroes been provided to slay dragon?

    Specifically, in the case when 'A may be used as B and B may be used as A'.
    """
    if {*heroes} & {*_disallowed_heroes}:
        raise error.DrollError(
            "Heroes {} cannot defeat a dragon.".format(_disallowed_heroes)
        )
    if len(heroes) != _required_heroes:
        raise error.DrollError(
            "Exactly {} heroes must be specified.".format(_required_heroes)
        )

    # Count all heroes, accumulating all _interchangable into just one hero
    counter = collections.Counter(heroes)
    interchangeable = list(sorted(_interchangeable))
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
    distinct_heroes = sum(v for k, v in counter.items())
    if distinct_heroes != _required_heroes:
        raise error.DrollError("Heroes {} not sufficiently distinct.", heroes)

    return True


def defeat_dragon(
    game: struct.World,
    randrange: dice.RandRange,
    hero: str,
    target: str,
    *others,
    _defeat_dragon_heroes=defeat_dragon_heroes,  # What type hint?
    _min_dragon_length: int = 3
) -> struct.World:
    """Update game after hero handles a dragon using multiple distinct heroes.

    Additional required heroes are specified within variable-length others."""
    # Simple prerequisites for attempting to defeat the dragon
    if game.dungeon.dragon < _min_dragon_length:
        raise error.DrollError(
            "Enemy {} only comes at length {}.".format(
                target, _min_dragon_length
            )
        )
    if not world.defeated_monsters(game.dungeon):
        raise error.DrollError(
            "Enemy {} only comes after all others defeated.".format(target)
        )

    # Confirm required number of distinct heroes available
    party = __decrement_hero(game.party, hero)
    heroes = [hero]
    for other in others:
        party = __decrement_hero(party, other)
        heroes.append(other)
    if not _defeat_dragon_heroes(*heroes):
        raise RuntimeError("Unexpected result from _defeat_dragon_heroes")

    # Attempt was successful, so update experience and treasure
    return world.draw_treasure(game, randrange)._replace(
        experience=game.experience + 1,
        party=party,
        dungeon=__eliminate_targets(game.dungeon, target),
    )


def bait_dragon(
    game: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: typing.Optional[str] = None,
    *,
    _enemies: typing.Sequence[str] = ("goblin", "skeleton", "ooze"),
    _require_treasure: bool = True
) -> struct.World:
    """Convert all monster faces into dragon dice."""
    # Confirm well-formed request optionally containing a target
    target = "dragon" if target is None else target
    if target != "dragon":
        raise error.DrollError("Cannot {} a {}.".format(noun, target))
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
        raise error.DrollError(
            "At least one of {} required for '{}'.".format(_enemies, noun)
        )

    # Increment the number of targets (i.e. dragons)
    return game._replace(
        dungeon=dungeon._replace(
            **{target: getattr(dungeon, target) + new_targets}
        )
    )


def elixir(
    game: struct.World, randrange: dice.RandRange, noun: str, target: str
) -> struct.World:
    """Add one hero die of any requested type."""
    return world.replace_treasure(game, noun)._replace(
        party=__increment_hero(game.party, target)
    )


def consume_ability(game: struct.World):
    if not game.ability:
        raise error.DrollError("Ability not available for use.")
    return game._replace(ability=False)


def nop_ability(
    game: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: typing.Optional[str] = None,
) -> struct.World:
    """No special ability available (though its consumption is tracked)"""
    if target is not None:
        raise error.DrollError("No targets accepted for {}.".format(noun))
    return consume_ability(game)
