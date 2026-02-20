# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Ability functions for all heroes."""

from dataclasses import replace
from typing import Optional

from . import dice, regular, special, struct
from .dungeon import defeated_monsters, decrement_dungeon, eliminate_dungeon, increment_dungeon
from .error import DrollError
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
    noun: str,
    target: Optional[str],
    acceptable: frozenset[str],
) -> struct.World:
    """Default target to sorted-first acceptable; validate; add one hero to party."""
    if target is None:
        target = next(iter(sorted(acceptable)))
    if target not in acceptable:
        raise DrollError(f"Target {target} not one of {acceptable}.")
    return _consume_ability(
        replace(world, party=regular.increment_party(world.party, target))
    )


def _convert_one(
    world: struct.World,
    target: Optional[str],
    source: str,
    destination: str,
) -> struct.World:
    """Validate optional target is source type; convert 1 dungeon die to party."""
    if target and target != source:
        raise DrollError(f"Ability can only target 1 {source}.")
    return _consume_ability(
        special.convert_dungeon_to_party(
            world, source=source, destination=destination, max_count=1
        )
    )


def _convert_two(
    world: struct.World,
    target: Optional[str],
    extra_targets: tuple[str, ...],
    source: str,
    destination: str,
) -> struct.World:
    """Validate optional targets are source type; convert up to 2 dungeon dice to party."""
    if target and target != source:
        raise DrollError(f"Ability can only target {source}s.")
    if extra_targets and extra_targets[0] != source:
        raise DrollError(f"Ability can only target {source}s.")
    if len(extra_targets) > 1:
        raise DrollError("At most 2 targets can be changed.")
    return _consume_ability(
        special.convert_dungeon_to_party(
            world, source=source, destination=destination, max_count=2
        )
    )


def default_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: Optional[str] = None,
) -> struct.World:
    """No special ability available (though its consumption is tracked)"""
    if target is not None:
        raise DrollError(f"No targets accepted for {noun}.")
    return _consume_ability(world)


def battlemage_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: Optional[str] = None,
    *,
    _acceptable_targets: frozenset[str] = frozenset({"fighter", "mage"}),
) -> struct.World:
    """Discard all monsters, chests, potions, and dice in the dragon's lair."""
    if target is not None:
        raise DrollError(f"No targets accepted for {noun}.")
    return _consume_ability(replace(world, dungeon=struct.Dungeon()))


def beguiler_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: Optional[str] = None,
    *extra_targets: str,
) -> struct.World:
    """Transform at most 2 monsters into 1 potion.

    Requires transforming 2 monsters when 2+ monsters available."""
    dungeon = world.dungeon
    dungeon = decrement_dungeon(dungeon, target)
    if len(extra_targets) > 1:
        raise DrollError("At most 2 targets can be changed.")
    elif len(extra_targets) == 1:
        dungeon = decrement_dungeon(dungeon, extra_targets[0])
    elif not defeated_monsters(dungeon):
        assert len(extra_targets) == 0
        raise DrollError("2 targets required when 2+ available.")
    dungeon = increment_dungeon(dungeon, "potion")
    return _consume_ability(replace(world, dungeon=dungeon))


def chieftain_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: Optional[str] = None,
    *extra_targets: str,
) -> struct.World:
    """Transform 2 goblins into thieves, discarding them at next regroup."""
    return _convert_two(world, target, extra_targets, source="goblin", destination="thief")


def commander_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: Optional[str] = None,
    *additional,
) -> struct.World:
    """Rerolls any number of Party and Dungeon dice."""
    if target is None:
        raise DrollError(f"At least 1 reroll target required for {noun}.")
    # Temporarily add a scroll to be consumed by reroll
    world = replace(world, party=regular.increment_party(world.party, "scroll"))
    world = regular.reroll(world, randrange, "scroll", target, *additional, allow_dragon=True)
    return _consume_ability(world)


def crusader_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: Optional[str] = None,
    *,
    _acceptable_targets: frozenset[str] = frozenset({"fighter", "cleric"}),
) -> struct.World:
    """Crusader usable as a fighter or a cleric, adding one hero.

    Optionally, specify 'fighter' or 'cleric' to select which to choose."""
    return _choose_and_add_hero(world, noun, target, _acceptable_targets)


def enchantress_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: Optional[str] = None,
) -> struct.World:
    """Transform exactly 1 monster into 1 potion."""
    dungeon = world.dungeon
    dungeon = decrement_dungeon(dungeon, target)
    dungeon = increment_dungeon(dungeon, "potion")
    return _consume_ability(replace(world, dungeon=dungeon))


def halfgoblin_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: Optional[str] = None,
) -> struct.World:
    """Transform 1 goblin into 1 thief, discarding it at next regroup."""
    return _convert_one(world, target, source="goblin", destination="thief")


def knight_ability(*args, **kwargs):
    """Convert all monster faces into dragon dice."""
    return _consume_ability(
        regular.bait_dragon(*args, require_treasure=False, **kwargs)
    )


def mercenary_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: Optional[str] = None,
    *additional,
) -> struct.World:
    """Defeat any 2 monsters."""
    if target is None:
        raise DrollError(f"At least 1 target required for {noun}.")
    # Temporarily add a champion to be consumed by defeat_one_plus_additional
    world = replace(world, party=regular.increment_party(world.party, "champion"))
    world = special.defeat_one_plus_additional(
        world, randrange, "champion", target, *additional
    )
    return _consume_ability(world)


def minstrel_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: Optional[str] = None,
) -> struct.World:
    """Discard all dragon dice."""
    target = "dragon" if target is None else target
    if target != "dragon":
        raise DrollError(f"Can only discard dragon dice, not {target}.")
    return _consume_ability(
        replace(world, dungeon=eliminate_dungeon(world.dungeon, target))
    )


def necromancer_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: Optional[str] = None,
    *extra_targets: str,
) -> struct.World:
    """Transform 2 skeletons into fighters, discarding them at next regroup."""
    return _convert_two(world, target, extra_targets, source="skeleton", destination="fighter")


def occultist_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: Optional[str] = None,
) -> struct.World:
    """Transform 1 skeleton into 1 fighter, discarding it at next regroup."""
    return _convert_one(world, target, source="skeleton", destination="fighter")


def paladin_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: Optional[str] = None,
    *revivable: str,
) -> struct.World:
    """Consume treasure to clear dungeon, open chests, and quaff potions.

    Specify consumed treasure as first argument.
    For each potion, add one argument for the hero to review."""
    # Validate that a treasure was specified
    if target is None:
        raise DrollError(f"Treasure to consume required for {noun}.")

    # Consume the specified treasure (will error if not possessed)
    world = replace(world, treasure=replace_treasure(world.treasure, target))

    # Validate potion/revivable count before making changes
    if world.dungeon is not None:
        potion_count = world.dungeon.potion
        if len(revivable) != potion_count:
            raise DrollError(f"Exactly {potion_count} heroes to revive required.")

        # Draw treasure for each chest
        treasure = world.treasure
        for _ in range(world.dungeon.chest):
            treasure = draw_treasure(treasure, randrange)
        world = replace(world, treasure=treasure)

        # Revive heroes for each potion
        party = world.party
        for revived in revivable:
            party = regular.increment_party(party, revived)
        world = replace(world, party=party)

    # Clear the entire dungeon (all monsters, chests, potions, dragons)
    world = replace(world, dungeon=struct.Dungeon())

    return _consume_ability(world)


def spellsword_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: Optional[str] = None,
    *,
    _acceptable_targets: frozenset[str] = frozenset({"fighter", "mage"}),
) -> struct.World:
    """Spellsword usable as a fighter or a mage, adding one hero to party.

    Optionally, specify 'fighter' or 'mage' to select which to choose."""
    return _choose_and_add_hero(world, noun, target, _acceptable_targets)
