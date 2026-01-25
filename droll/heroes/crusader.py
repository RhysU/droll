# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hero definitions for Crusader advancing to Paladin."""
import functools
import typing

from .. import action
from .. import dice
from .. import error
from .. import struct
from .. import world
from ..player import Default


def crusader_ability(
    game: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: typing.Optional[str] = None,
    *,
    _acceptable_targets: typing.Set[str] = {"fighter", "cleric"}
) -> struct.World:
    """Holy Strike: Crusader usable as a fighter or a cleric, adding one hero.

    Optionally, specify 'fighter' or 'cleric' to select which to choose."""
    if target is None:
        target = next(iter(sorted(_acceptable_targets)))
    if target not in _acceptable_targets:
        raise error.DrollError(
            "Target {} not one of {}".format(target, _acceptable_targets)
        )
    return action.consume_ability(
        game._replace(party=action.__increment_hero(game.party, target))
    )


def paladin_ability(
    game: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: typing.Optional[str] = None,
    *revivable,
    _acceptable_targets: typing.Set[str] = {"fighter", "cleric"}
) -> struct.World:
    """Divine Intervention: Use treasure to clear dungeon and revive heroes.

    Requires specifying which treasure to consume as the first argument.
    For each potion in the dungeon, specify one hero to revive."""
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
            party = action.__increment_hero(party, revived)
        game = game._replace(party=party)

    # Clear the entire dungeon (all monsters, chests, potions, dragons)
    game = game._replace(
        dungeon=struct.Dungeon(*([0] * len(struct.Dungeon._fields)))
    )

    return action.consume_ability(game)


@functools.wraps(action.defeat_dragon)
def crusader_defeat_dragon(*args, **kwargs):
    return action.defeat_dragon(
        *args, **kwargs, _defeat_dragon_heroes=crusader_defeat_dragon_heroes
    )


@functools.wraps(action.defeat_dragon_heroes_interchangeable)
def crusader_defeat_dragon_heroes(*args, **kwargs):
    return action.defeat_dragon_heroes_interchangeable(
        *args, **kwargs, _interchangeable={"fighter", "cleric"}
    )


# Defined in terms of Default, not Crusader, to permit advance(...) closure
Paladin = Default._replace(
    name="Paladin",
    ability=paladin_ability,
    advance=(lambda _: Paladin),  # Cannot advance further
    party=Default.party._replace(
        fighter=Default.party.fighter._replace(
            # Fighters usable as clerics implies fighter.skeleton as if a cleric
            skeleton=Default.party.cleric.skeleton,
            dragon=crusader_defeat_dragon,
        ),
        cleric=Default.party.cleric._replace(
            # Clerics usable as fighters implies cleric.goblin as if a fighter
            goblin=Default.party.fighter.goblin,
            dragon=crusader_defeat_dragon,
        ),
        mage=Default.party.mage._replace(dragon=crusader_defeat_dragon),
        thief=Default.party.thief._replace(dragon=crusader_defeat_dragon),
        champion=Default.party.champion._replace(dragon=crusader_defeat_dragon),
        scroll=Default.party.scroll._replace(dragon=crusader_defeat_dragon),
    ),
)

# Defined after Paladin to permit advance(...) closure
Crusader = Default._replace(
    name="Crusader",
    ability=crusader_ability,
    advance=(lambda world: Crusader if world.experience < 5 else Paladin),
    party=Paladin.party,
)
