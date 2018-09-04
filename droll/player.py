# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with player action mechanics."""

import collections

from .action import (
    ActionError, defeat_all, defeat_dragon, defeat_one,
    open_all, open_one, quaff, reroll, bait_dragon, elixir
)
from .world import Level, Party, RandRange, World, replace_treasure

# Placeholder for further expansion
Player = collections.namedtuple('Player', (
    'party',
))

_HERO_ARTIFACTS = Party(
    fighter='sword',
    cleric='talisman',
    mage='sceptre',
    thief='tools',
    champion=None,
    scroll='scroll'
)


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

    # TODO Migrate to Player
    if target is None:
        if noun != 'bait':
            raise ActionError('Unknown noun {} lacking a target'.format(noun))
        return bait_dragon(world)

    # TODO Migrate to Player
    if noun == 'elixir':
        if not additional:
            raise ActionError('Noun {} accepts only one target'.format(noun))
        return elixir(world, target)

    # Consume an artifact if hero of requested type is not available.
    if getattr(world.party, noun) == 0:
        artifact = getattr(_HERO_ARTIFACTS, noun, None)
        if artifact is not None and getattr(world.treasure, artifact) == 0:
            raise ActionError("Neither hero {} nor artifact {} available"
                              .format(noun, artifact))
        world = replace_treasure(world, artifact)

    # TODO Elixir can be swapped for any party dice

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
