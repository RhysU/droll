# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Ability functions for all heroes."""

from dataclasses import replace
from . import regular, special, struct
from .dungeon import (
    defeated_monsters,
    decrement_dungeon,
    eliminate_dungeon,
    increment_dungeon,
)
from .party import increment_party
from .struct import Action, Artifact, Dungeon, DrollError, Party
from .treasure import draw_treasure, replace_treasure

__all__ = (
    "default_ability",
    "bard_ability",
    "battlemage_ability",
    "beguiler_ability",
    "chieftain_ability",
    "commander_ability",
    "crusader_ability",
    "dragonslayer_ability",
    "enchantress_ability",
    "halfgoblin_ability",
    "knight_ability",
    "mercenary_ability",
    "minstrel_ability",
    "necromancer_ability",
    "occultist_ability",
    "paladin_ability",
    "spellsword_ability",
)


def _consume_ability(world: struct.World) -> struct.World:
    """Mark the hero's special ability as used."""
    if not world.ability:
        raise DrollError("Ability not available.")
    return replace(world, ability=False)


def _choose_and_add_hero(
    world: struct.World,
    command: Action,
    targets: tuple[Dungeon | Party, ...],
    acceptable: frozenset[Party],
) -> struct.World:
    """Default target to sorted-first acceptable; validate; add one hero."""
    world = _consume_ability(world)
    if len(targets) > 1:
        raise DrollError(f"At most 1 target accepted for {command.value}.")
    target = targets[0] if targets else next(iter(sorted(acceptable, key=lambda p: p.value)))
    if target not in acceptable:
        raise DrollError(
            f"Target '{target.value}' not one of {', '.join(sorted(p.value for p in acceptable))}."
        )
    return replace(world, party=increment_party(world.party, target))


def _convert_one(
    world: struct.World,
    targets: tuple[Dungeon | Party, ...],
    source: Dungeon,
    destination: Party,
) -> struct.World:
    """Validate optional target; convert 1 dungeon die to party."""
    world = _consume_ability(world)
    if any(t is not source for t in targets):
        raise DrollError(f"Ability can only target 1 {source.value}.")
    if len(targets) > 1:
        raise DrollError(f"Ability can only target 1 {source.value}.")
    return special.convert_dungeon_to_party(
        world, source=source, destination=destination, max_count=1
    )


def _convert_two(
    world: struct.World,
    targets: tuple[Dungeon | Party, ...],
    source: Dungeon,
    destination: Party,
) -> struct.World:
    """Validate optional targets; convert up to 2 dungeon dice to party."""
    world = _consume_ability(world)
    if targets and targets[0] is not source:
        raise DrollError(f"Ability can only target a {source.value}.")
    if len(targets) > 1 and targets[1] is not source:
        raise DrollError(f"Ability can only target a {source.value}.")
    if len(targets) > 2:
        raise DrollError("At most 2 targets can be changed.")
    return special.convert_dungeon_to_party(
        world, source=source, destination=destination, max_count=2
    )


def default_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: Action,
    targets: tuple[Dungeon | Party, ...] = (),
) -> struct.World:
    """No special ability."""
    world = _consume_ability(world)
    if targets:
        raise DrollError(f"No targets accepted for {command.value}.")
    return world


def battlemage_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: Action,
    targets: tuple[Dungeon | Party, ...] = (),
) -> struct.World:
    """Discard all monsters, chests, potions, and dice in the dragon's lair.

    Example: ability"""
    world = _consume_ability(world)
    if targets:
        raise DrollError(f"No targets accepted for {command.value}.")
    return replace(world, dungeon=struct.empty_dungeon())


def beguiler_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: Action,
    targets: tuple[Dungeon | Party, ...] = (),
) -> struct.World:
    """Transform at most 2 monsters into 1 potion.
    Requires transforming 2 monsters when 2+ monsters available.
    Scrolls target monsters like party members.

    Example: ability goblin skeleton
    Example: ability goblin"""
    if not targets:
        raise struct.DrollError(f'"{command.value}" requires a monster target.')
    world = _consume_ability(world)
    dungeon = world.dungeon
    dungeon = decrement_dungeon(dungeon, targets[0])
    if len(targets) > 2:
        raise DrollError("At most 2 targets can be changed.")
    elif len(targets) == 2:
        dungeon = decrement_dungeon(dungeon, targets[1])
    elif not defeated_monsters(dungeon):
        raise DrollError("2 targets required when 2+ available.")
    dungeon = increment_dungeon(dungeon, Dungeon.POTION)
    return replace(world, dungeon=dungeon)


def chieftain_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: Action,
    targets: tuple[Dungeon | Party, ...] = (),
) -> struct.World:
    """Transform up to 2 goblins into thieves, discarding them on regroup.
    Open chests and quaff potions before clearing monsters.

    Example: ability"""
    return _convert_two(world, targets, source=Dungeon.GOBLIN, destination=Party.THIEF)


def commander_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: Action,
    targets: tuple[Dungeon | Party, ...] = (),
) -> struct.World:
    """Rerolls any number of Party and Dungeon dice.
    Each fighter defeats one additional monster beyond its usual targets.
    Specify two targets when monsters remain after the first, e.g.
    'fighter goblin skeleton' defeats all goblins and one skeleton.

    Example: ability goblin skeleton
    Example: fighter goblin ooze"""
    if not targets:
        raise DrollError(f"At least 1 reroll target required for {command.value}.")
    world = _consume_ability(world)
    # Temporarily add a scroll to be consumed by reroll
    world = replace(world, party=increment_party(world.party, Party.SCROLL))
    return regular.reroll(
        world, randrange, Party.SCROLL, targets, allow_dragon=True
    )


def crusader_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: Action,
    targets: tuple[Dungeon | Party, ...] = (),
    *,
    _acceptable_targets: frozenset[Party] = frozenset({Party.FIGHTER, Party.CLERIC}),
) -> struct.World:
    """Add 1 fighter or cleric to the party.

    Example: ability
    Example: ability cleric"""
    return _choose_and_add_hero(world, command, targets, _acceptable_targets)


def enchantress_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: Action,
    targets: tuple[Dungeon | Party, ...] = (),
) -> struct.World:
    """Transform exactly 1 monster into 1 potion.

    Example: ability goblin"""
    if not targets:
        raise struct.DrollError(f'"{command.value}" requires a monster target.')
    if len(targets) > 1:
        raise struct.DrollError(f'"{command.value}" accepts only 1 monster target.')
    world = _consume_ability(world)
    dungeon = world.dungeon
    dungeon = decrement_dungeon(dungeon, targets[0])
    dungeon = increment_dungeon(dungeon, Dungeon.POTION)
    return replace(world, dungeon=dungeon)


def halfgoblin_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: Action,
    targets: tuple[Dungeon | Party, ...] = (),
) -> struct.World:
    """Transform 1 goblin into 1 thief, discarding it on regroup.

    Example: ability"""
    return _convert_one(world, targets, source=Dungeon.GOBLIN, destination=Party.THIEF)


def knight_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: Action,
    targets: tuple[Dungeon | Party, ...] = (),
) -> struct.World:
    """Convert all monster faces into dragon dice.

    Example: ability"""
    world = _consume_ability(world)
    return regular.bait_dragon(
        world, randrange, command, targets, require_treasure=False
    )


def dragonslayer_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: Action,
    targets: tuple[Dungeon | Party, ...] = (),
) -> struct.World:
    """Convert all monster faces into dragon dice.
    Dragons require only 2 distinct party members to defeat.

    Example: ability
    Example: fighter dragon mage"""
    return knight_ability(world, randrange, command, targets)


def mercenary_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: Action,
    targets: tuple[Dungeon | Party, ...] = (),
) -> struct.World:
    """Defeat any 2 monsters.

    Example: ability goblin skeleton"""
    if not targets:
        raise DrollError(f"At least 1 target required for {command.value}.")
    world = _consume_ability(world)
    # Temporarily add a champion to be consumed by defeat_one_plus_additional
    world = replace(world, party=increment_party(world.party, Party.CHAMPION))
    return special.defeat_one_plus_additional(
        world, randrange, Party.CHAMPION, targets
    )


def minstrel_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: Action,
    targets: tuple[Dungeon | Party, ...] = (),
) -> struct.World:
    """Discard all dragon dice.

    Example: ability"""
    world = _consume_ability(world)
    if any(t is not Dungeon.DRAGON for t in targets):
        raise DrollError("Can discard only dragon dice.")
    return replace(world, dungeon=eliminate_dungeon(world.dungeon, Dungeon.DRAGON))


def bard_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: Action,
    targets: tuple[Dungeon | Party, ...] = (),
) -> struct.World:
    """Discard all dragon dice.
    Each champion defeats one additional monster beyond its usual targets.
    Specify two targets when monsters remain after the first, e.g.
    'champion goblin skeleton' defeats all goblins and one skeleton.

    Example: ability
    Example: champion goblin ooze"""
    return minstrel_ability(world, randrange, command, targets)


def necromancer_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: Action,
    targets: tuple[Dungeon | Party, ...] = (),
) -> struct.World:
    """Transform up to 2 skeletons into fighters, discarding on regroup.
    Heroes cleric and mage are interchangeable.

    Example: ability"""
    return _convert_two(world, targets, source=Dungeon.SKELETON, destination=Party.FIGHTER)


def occultist_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: Action,
    targets: tuple[Dungeon | Party, ...] = (),
) -> struct.World:
    """Transform 1 skeleton into 1 fighter, discarding it on regroup.

    Example: ability"""
    return _convert_one(world, targets, source=Dungeon.SKELETON, destination=Party.FIGHTER)


def paladin_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: Action,
    targets: tuple[Dungeon | Party, ...] = (),
) -> struct.World:
    """Consume treasure to clear dungeon, open chests, and quaff potions.
    Specify consumed treasure as first argument.
    For each potion, add one argument for the hero to revive.
    Heroes fighter and cleric are interchangeable.

    Example: ability sword
    Example: ability talisman mage"""
    world = _consume_ability(world)
    # Validate that a treasure was specified
    if not targets:
        raise DrollError(f"Treasure to consume required for {command.value}.")

    # Consume the specified treasure (will error if not possessed)
    # targets[0] is an Artifact enum for paladin
    world = replace(world, treasure=replace_treasure(world.treasure, targets[0]))

    # Validate potion/revivable count before making changes
    if world.dungeon is not None:
        if len(targets) - 1 != world.dungeon[Dungeon.POTION]:
            raise DrollError(
                f"Exactly {world.dungeon[Dungeon.POTION]} heroes to revive required."
            )

        # Draw treasure for each chest
        treasure = world.treasure
        for _ in range(world.dungeon[Dungeon.CHEST]):
            treasure = draw_treasure(treasure, randrange)
        world = replace(world, treasure=treasure)

        # Revive heroes for each potion
        party = world.party
        for revived in targets[1:]:
            party = increment_party(party, revived)
        world = replace(world, party=party)

    # Clear the entire dungeon (all monsters, chests, potions, dragons)
    world = replace(world, dungeon=struct.empty_dungeon())

    return world


def spellsword_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: Action,
    targets: tuple[Dungeon | Party, ...] = (),
    *,
    _acceptable_targets: frozenset[Party] = frozenset({Party.FIGHTER, Party.MAGE}),
) -> struct.World:
    """Add 1 fighter or mage to the party.

    Example: ability
    Example: ability mage"""
    return _choose_and_add_hero(world, command, targets, _acceptable_targets)
