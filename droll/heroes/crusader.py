# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Crusader advancing to Paladin."""
from dataclasses import replace
import functools
import typing

from .. import action
from .. import dice
from .. import error
from .. import struct
from .. import world
from ..player import Default


def _crusader_ability(
    game: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: typing.Optional[str] = None,
    *,
    _acceptable_targets: typing.FrozenSet[str] = frozenset(
        {"fighter", "cleric"}
    )
) -> struct.World:
    """Crusader usable as a fighter or a cleric, adding one hero.

    Optionally, specify 'fighter' or 'cleric' to select which to choose."""
    if target is None:
        target = next(iter(sorted(_acceptable_targets)))
    if target not in _acceptable_targets:
        raise error.DrollError(
            "Target {} not one of {}".format(target, _acceptable_targets)
        )
    return action.consume_ability(
        replace(game, party=action.increment_hero(game.party, target))
    )


def _paladin_ability(
    game: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: typing.Optional[str] = None,
    *revivable: str,
    _acceptable_targets: typing.FrozenSet[str] = frozenset(
        {"fighter", "cleric"}
    )
) -> struct.World:
    """Consume treasure to clear dungeon, open chests, and quaff potions.

    Specify consumed treasure as first argument.
    For each potion, add one argument for the hero to review."""
    # Validate that a treasure was specified
    if target is None:
        raise error.DrollError(
            "Must specify which treasure to consume for {}".format(noun)
        )

    # Consume the specified treasure (will error if not possessed)
    game = world.replace_treasure(game, target)

    # Validate potion/revivable count before making changes
    if game.dungeon is not None:
        potion_count = game.dungeon.potion
        if len(revivable) != potion_count:
            raise error.DrollError(
                "Require exactly {} heroes to revive for {} potions.".format(
                    potion_count, potion_count
                )
            )

        # Draw treasure for each chest
        for _ in range(game.dungeon.chest):
            game = world.draw_treasure(game, randrange)

        # Revive heroes for each potion
        party = game.party
        for revived in revivable:
            party = action.increment_hero(party, revived)
        game = replace(game, party=party)

    # Clear the entire dungeon (all monsters, chests, potions, dragons)
    game = replace(game, dungeon=struct.Dungeon())

    return action.consume_ability(game)


# Fighter/cleric are interchangeable for dragon defeats
_crusader_defeat_dragon = functools.partial(
    action.defeat_dragon,
    _defeat_dragon_heroes=functools.partial(
        action.defeat_dragon_heroes_interchangeable,
        _interchangeable={"fighter", "cleric"},
    ),
)

# Defined in terms of Default, not Crusader, to permit advance(...) closure
Paladin = replace(
    Default,
    name="Paladin",
    ability=_paladin_ability,
    advance=(lambda _: Paladin),
    party=replace(
        struct.update_party_dragon(Default.party, _crusader_defeat_dragon),
        fighter=replace(
            Default.party.fighter, skeleton=Default.party.cleric.skeleton
        ),
        cleric=replace(
            Default.party.cleric, goblin=Default.party.fighter.goblin
        ),
    ),
)

# Defined after Paladin to permit advance(...) closure
Crusader = replace(
    Default,
    name="Crusader",
    ability=_crusader_ability,
    advance=(lambda world: Crusader if world.experience < 5 else Paladin),
    party=Paladin.party,
)
