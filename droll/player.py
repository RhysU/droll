# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with player action mechanics."""

import collections

from .action import (
    defeat_all, defeat_dragon, defeat_one,
    open_all, open_one, quaff, reroll
)
from .world import Level, Party, RandRange, World

# Placeholder for further expansion
Player = collections.namedtuple('Player', (
    'party',
))


def apply(
        player: Player,
        world: World,
        randrange: RandRange,
        noun: str,
        target: str,
        *additional
) -> World:
    """Apply noun to target within world, returning a new version.

    Varargs 'additional' permits passing more required information.
    For example, what heros to revive when quaffing a potion."""
    action = getattr(getattr(player.party, noun), target)
    return action(world, randrange, noun, target, *additional)


DEFAULT = Player(
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
