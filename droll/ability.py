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
from .struct import DrollError
from .treasure import draw_treasure, replace_treasure

__all__ = (
    "default_ability",
    "battlemage_ability",
    "beguiler_ability",
    "chieftain_ability",
    "commander_ability",
    "crusader_ability",
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
    command: str,
    targets: tuple[str, ...],
    acceptable: frozenset[str],
) -> struct.World:
    """Default target to sorted-first acceptable; validate; add one hero."""
    world = _consume_ability(world)
    if len(targets) > 1:
        raise DrollError(f"At most 1 target accepted for {command}.")
    target = targets[0] if targets else next(iter(sorted(acceptable)))
    if target not in acceptable:
        raise DrollError(f"Target {target} not one of {acceptable}.")
    return replace(world, party=increment_party(world.party, target))


def _convert_one(
    world: struct.World,
    targets: tuple[str, ...],
    source: str,
    destination: str,
) -> struct.World:
    """Validate optional target; convert 1 dungeon die to party."""
    world = _consume_ability(world)
    if any(t != source for t in targets):
        raise DrollError(f"Ability can only target 1 {source}.")
    if len(targets) > 1:
        raise DrollError(f"Ability can only target 1 {source}.")
    return special.convert_dungeon_to_party(
        world, source=source, destination=destination, max_count=1
    )


def _convert_two(
    world: struct.World,
    targets: tuple[str, ...],
    source: str,
    destination: str,
) -> struct.World:
    """Validate optional targets; convert up to 2 dungeon dice to party."""
    world = _consume_ability(world)
    if targets and targets[0] != source:
        raise DrollError(f"Ability can only target a {source}.")
    if len(targets) > 1 and targets[1] != source:
        raise DrollError(f"Ability can only target a {source}.")
    if len(targets) > 2:
        raise DrollError("At most 2 targets can be changed.")
    return special.convert_dungeon_to_party(
        world, source=source, destination=destination, max_count=2
    )


def default_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: str,
    targets: tuple[str, ...] = (),
) -> struct.World:
    """No special ability available (though its consumption is tracked)"""
    world = _consume_ability(world)
    if targets:
        raise DrollError(f"No targets accepted for {command}.")
    return world


def battlemage_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: str,
    targets: tuple[str, ...] = (),
) -> struct.World:
    """Discard all monsters, chests, potions, and dice in the dragon's lair."""
    world = _consume_ability(world)
    if targets:
        raise DrollError(f"No targets accepted for {command}.")
    return replace(world, dungeon=struct.Dungeon())


def beguiler_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: str,
    targets: tuple[str, ...] = (),
) -> struct.World:
    """Transform at most 2 monsters into 1 potion.

    Requires transforming 2 monsters when 2+ monsters available."""
    if not targets:
        raise struct.DrollError(f'"{command}" requires a monster target.')
    world = _consume_ability(world)
    dungeon = world.dungeon
    dungeon = decrement_dungeon(dungeon, targets[0])
    if len(targets) > 2:
        raise DrollError("At most 2 targets can be changed.")
    elif len(targets) == 2:
        dungeon = decrement_dungeon(dungeon, targets[1])
    elif not defeated_monsters(dungeon):
        raise DrollError("2 targets required when 2+ available.")
    dungeon = increment_dungeon(dungeon, "potion")
    return replace(world, dungeon=dungeon)


def chieftain_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: str,
    targets: tuple[str, ...] = (),
) -> struct.World:
    """Transform up to 2 goblins into thieves, discarding them on regroup."""
    return _convert_two(world, targets, source="goblin", destination="thief")


def commander_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: str,
    targets: tuple[str, ...] = (),
) -> struct.World:
    """Rerolls any number of Party and Dungeon dice."""
    if not targets:
        raise DrollError(f"At least 1 reroll target required for {command}.")
    world = _consume_ability(world)
    # Temporarily add a scroll to be consumed by reroll
    world = replace(world, party=increment_party(world.party, "scroll"))
    return regular.reroll(
        world, randrange, "scroll", targets, allow_dragon=True
    )


def crusader_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: str,
    targets: tuple[str, ...] = (),
    *,
    _acceptable_targets: frozenset[str] = frozenset({"fighter", "cleric"}),
) -> struct.World:
    """Crusader usable as a fighter or a cleric, adding one hero.

    Optionally, specify 'fighter' or 'cleric' to select which to choose."""
    return _choose_and_add_hero(world, command, targets, _acceptable_targets)


def enchantress_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: str,
    targets: tuple[str, ...] = (),
) -> struct.World:
    """Transform exactly 1 monster into 1 potion."""
    if not targets:
        raise struct.DrollError(f'"{command}" requires a monster target.')
    if len(targets) > 1:
        raise struct.DrollError(f'"{command}" accepts only 1 monster target.')
    world = _consume_ability(world)
    dungeon = world.dungeon
    dungeon = decrement_dungeon(dungeon, targets[0])
    dungeon = increment_dungeon(dungeon, "potion")
    return replace(world, dungeon=dungeon)


def halfgoblin_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: str,
    targets: tuple[str, ...] = (),
) -> struct.World:
    """Transform 1 goblin into 1 thief, discarding it on regroup."""
    return _convert_one(world, targets, source="goblin", destination="thief")


def knight_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: str,
    targets: tuple[str, ...] = (),
) -> struct.World:
    """Convert all monster faces into dragon dice."""
    world = _consume_ability(world)
    return regular.bait_dragon(
        world, randrange, command, targets, require_treasure=False
    )


def mercenary_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: str,
    targets: tuple[str, ...] = (),
) -> struct.World:
    """Defeat any 2 monsters."""
    if not targets:
        raise DrollError(f"At least 1 target required for {command}.")
    world = _consume_ability(world)
    # Temporarily add a champion to be consumed by defeat_one_plus_additional
    world = replace(world, party=increment_party(world.party, "champion"))
    return special.defeat_one_plus_additional(
        world, randrange, "champion", targets
    )


def minstrel_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: str,
    targets: tuple[str, ...] = (),
) -> struct.World:
    """Discard all dragon dice."""
    world = _consume_ability(world)
    if any(t != "dragon" for t in targets):
        raise DrollError("Can discard only dragon dice.")
    return replace(world, dungeon=eliminate_dungeon(world.dungeon, "dragon"))


def necromancer_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: str,
    targets: tuple[str, ...] = (),
) -> struct.World:
    """Transform up to 2 skeletons into fighters, discarding on regroup."""
    return _convert_two(world, targets, source="skeleton", destination="fighter")


def occultist_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: str,
    targets: tuple[str, ...] = (),
) -> struct.World:
    """Transform 1 skeleton into 1 fighter, discarding it on regroup."""
    return _convert_one(world, targets, source="skeleton", destination="fighter")


def paladin_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: str,
    targets: tuple[str, ...] = (),
) -> struct.World:
    """Consume treasure to clear dungeon, open chests, and quaff potions.

    Specify consumed treasure as first argument.
    For each potion, add one argument for the hero to revive."""
    world = _consume_ability(world)
    # Validate that a treasure was specified
    if not targets:
        raise DrollError(f"Treasure to consume required for {command}.")

    # Consume the specified treasure (will error if not possessed)
    world = replace(world, treasure=replace_treasure(world.treasure, targets[0]))

    # Validate potion/revivable count before making changes
    if world.dungeon is not None:
        if len(targets) - 1 != world.dungeon.potion:
            raise DrollError(
                f"Exactly {world.dungeon.potion} heroes to revive required."
            )

        # Draw treasure for each chest
        treasure = world.treasure
        for _ in range(world.dungeon.chest):
            treasure = draw_treasure(treasure, randrange)
        world = replace(world, treasure=treasure)

        # Revive heroes for each potion
        party = world.party
        for revived in targets[1:]:
            party = increment_party(party, revived)
        world = replace(world, party=party)

    # Clear the entire dungeon (all monsters, chests, potions, dragons)
    world = replace(world, dungeon=struct.Dungeon())

    return world


def spellsword_ability(
    world: struct.World,
    randrange: struct.RandRange,
    command: str,
    targets: tuple[str, ...] = (),
    *,
    _acceptable_targets: frozenset[str] = frozenset({"fighter", "mage"}),
) -> struct.World:
    """Spellsword usable as a fighter or a mage, adding one hero to party.

    Optionally, specify 'fighter' or 'mage' to select which to choose."""
    return _choose_and_add_hero(world, command, targets, _acceptable_targets)
