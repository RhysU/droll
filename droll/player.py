# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with player action mechanics."""

import collections

from .action import (
    defeat_all, defeat_dragon, defeat_one,
    open_all, open_one, quaff, reroll, bait_dragon, elixir
)
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

    Processes hero-like artifacts (i.e. not rings/portals/scales).
    Varargs 'additional' permits passing more required information.
    For example, what heroes to revive when quaffing a potion."""
    # One-off handling of some treasures
    if noun in {'bait', 'elixir'}:
        action = getattr(player, noun)
        return action(world, randrange, noun, target, *additional)

    # Many treasures behave exactly like party members, so
    # convert into party members prior to action invocation.
    prior_treasure = world.treasure
    world = world._replace(
        party=world.party._replace(**{
            hero: getattr(world.party, hero) + getattr(prior_treasure, artifact)
            for hero, artifact in player.artifacts._asdict().items()
            if artifact is not None
        })
    )

    # Apply a hero (possibly phantom per above) to some collection of targets.
    action = getattr(getattr(player.party, noun), target)
    world = action(world, randrange, noun, target, *additional)

    # Undo the prior transformation by subtracting prior_treasure.
    world = world._replace(
        party=world.party._replace(**{
            hero: getattr(world.party, hero) - getattr(prior_treasure, artifact)
            for hero, artifact in player.artifacts._asdict().items()
            if artifact is not None
        })
    )

    # Consume treasure equivalent to any hero which has gone negative.
    for hero, quantity in world.party._asdict().items():
        if quantity >= 0:
            continue
        for _ in range(-min(0, quantity)):
            world = replace_treasure(world, getattr(player.artifacts, hero))
        world = world._replace(party=world.party._replace(**{hero: 0}))

    return world


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
