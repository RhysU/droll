# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with player action mechanics."""

import collections

from .action import (
    defeat_all, defeat_dragon, defeat_one,
    open_all, open_one, quaff, reroll, bait_dragon, elixir
)
from .error import DrollError
from .world import Level, Party, RandRange, World, replace_treasure

Player = collections.namedtuple('Player', (
    'bait',
    'elixir',
    'artifacts',
    'party',
))


def apply(
        player: Player,
        world: World,
        randrange: RandRange,
        noun: str,
        target: str = None,
        *additional
) -> World:
    """Apply noun to target within world, returning a new version.

    Also covers hero-like artifacts (i.e. not rings/portals/bait/scales).
    Varargs 'additional' permits passing more required information.
    For example, what heroes to revive when quaffing a potion."""
    # One-off handling of some treasures
    if noun in {'bait', 'elixir'}:
        action = getattr(player, noun)
        return action(world, randrange, noun, target, *additional)

    # Consume an artifact if hero of requested type is not available.
    # Implementation adds a phantom hero prior to it being consumed.
    if getattr(world.party, noun) == 0:
        artifact = getattr(player.artifacts, noun, None)
        if artifact is None:
            pass
        elif getattr(world.treasure, artifact):
            world = replace_treasure(world, artifact)._replace(
                party=world.party._replace(**{noun: 1})
            )
        else:
            raise DrollError("Neither hero {} nor artifact {} available"
                             .format(noun, artifact))

    # Apply a hero (or hero-like artifact) to some collection of targets.
    action = getattr(getattr(player.party, noun), target)
    return action(world, randrange, noun, target, *additional)


DEFAULT = Player(
    bait=bait_dragon,
    elixir=elixir,
    artifacts=Party(
        fighter='sword',
        cleric='talisman',
        mage='sceptre',
        thief='tools',
        champion=None,
        scroll='scroll',
    ),
    party=Party(
        fighter=Level(
            goblin=defeat_all,
            skeleton=defeat_one,
            ooze=defeat_one,
            chest=open_one,
            potion=quaff,
            dragon=defeat_dragon,
        ),
        cleric=Level(
            goblin=defeat_one,
            skeleton=defeat_all,
            ooze=defeat_one,
            chest=open_one,
            potion=quaff,
            dragon=defeat_dragon,
        ),
        mage=Level(
            goblin=defeat_one,
            skeleton=defeat_one,
            ooze=defeat_all,
            chest=open_one,
            potion=quaff,
            dragon=defeat_dragon,
        ),
        thief=Level(
            goblin=defeat_one,
            skeleton=defeat_one,
            ooze=defeat_one,
            chest=open_all,
            potion=quaff,
            dragon=defeat_dragon,
        ),
        champion=Level(
            goblin=defeat_all,
            skeleton=defeat_all,
            ooze=defeat_all,
            chest=open_all,
            potion=quaff,
            dragon=defeat_dragon,
        ),
        # Technically scrolls could re-roll potions,
        # but doing so would be a really peculiar choice.
        scroll=Level(
            goblin=reroll,
            skeleton=reroll,
            ooze=reroll,
            chest=reroll,
            potion=quaff,
            dragon=defeat_dragon,
        ),
    ),
)
