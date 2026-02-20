# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Crusader advancing to Paladin."""

from dataclasses import replace
import functools
from typing import Optional

from .. import regular
from .. import dice
from ..error import DrollError
from .. import struct
from ..treasure import replace_treasure, draw_treasure
from ..player import Default

__all__ = (
    "Crusader",
    "Paladin",
)


def _crusader_ability(
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: Optional[str] = None,
    *,
    _acceptable_targets: frozenset[str] = frozenset({"fighter", "cleric"}),
) -> struct.World:
    """Crusader usable as a fighter or a cleric, adding one hero.

    Optionally, specify 'fighter' or 'cleric' to select which to choose."""
    if target is None:
        target = next(iter(sorted(_acceptable_targets)))
    if target not in _acceptable_targets:
        raise DrollError(f"Target {target} not one of {_acceptable_targets}.")
    return regular.consume_ability(
        replace(world, party=regular.increment_party(world.party, target))
    )


def _paladin_ability(
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
            raise DrollError(
                f"Exactly {potion_count} heroes to revive required."
            )

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

    return regular.consume_ability(world)


# Fighter/cleric are interchangeable for dragon defeats
_crusader_defeat_dragon = functools.partial(
    regular.defeat_dragon,
    defeat_dragon_heroes=functools.partial(
        regular.defeat_dragon_heroes,
        interchangeable=frozenset({"fighter", "cleric"}),
    ),
)

# Defined in terms of Default, not Crusader, to permit advance(...) closure
Paladin = replace(
    Default,
    name="Paladin",
    ability=_paladin_ability,
    advance=(lambda _: Paladin),
    party=struct.Party(
        fighter=replace(
            Default.party.fighter,
            dragon=_crusader_defeat_dragon,
            skeleton=Default.party.cleric.skeleton,
        ),
        cleric=replace(
            Default.party.cleric,
            dragon=_crusader_defeat_dragon,
            goblin=Default.party.fighter.goblin,
        ),
        mage=replace(
            Default.party.mage,
            dragon=_crusader_defeat_dragon,
        ),
        thief=replace(
            Default.party.thief,
            dragon=_crusader_defeat_dragon,
        ),
        champion=replace(
            Default.party.champion,
            dragon=_crusader_defeat_dragon,
        ),
        scroll=replace(
            Default.party.scroll,
            dragon=_crusader_defeat_dragon,
        ),
    ),
)

# Defined after Paladin to permit advance(...) closure
Crusader = replace(
    Paladin,
    name="Crusader",
    ability=_crusader_ability,
    advance=(lambda world: Crusader if world.experience < 5 else Paladin),
    party=Paladin.party,
)
