# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with player action mechanics."""

import collections

from . import action
from . import error
from . import world

Player = collections.namedtuple('Player', (
    'bait',
    'elixir',
    'portal',
    'ring',
    'artifacts',
    'party',
))


def apply(
        player: Player,
        game: world.World,
        randrange: world.RandRange,
        noun: str,
        target: str = None,
        *additional
) -> world.World:
    """Apply noun to target within game, returning a new version.

    Processes hero-like artifacts (i.e. not rings/portals/scales).
    Varargs 'additional' permits passing more required information.
    For example, what heroes to revive when quaffing a potion."""
    # Convert any artifacts in the command into any corresponding hero types
    noun = partify(noun, player.artifacts)
    target = partify(target, player.artifacts)
    additional = tuple(partify(i, player.artifacts) for i in additional)

    # One-off handling of some treasures, with error wrapping to aid usability
    if noun in {'bait', 'elixir', 'ring', 'portal'}:
        try:
            action = getattr(player, noun)
            return action(game, randrange, noun, target, *additional)
        except AttributeError as cause:
            raise error.DrollError(str(cause)) from cause

    # Many treasures behave exactly like party members, so
    # convert into party members prior to action invocation.
    prior_treasure = game.treasure
    game = game._replace(
        party=game.party._replace(**{
            hero: getattr(game.party, hero) + getattr(prior_treasure, artifact)
            for hero, artifact in player.artifacts._asdict().items()
            if artifact is not None
        })
    )

    # Apply a hero (possibly phantom per above) to some collection of targets.
    try:
        action = getattr(getattr(player.party, noun), target)
        game = action(game, randrange, noun, target, *additional)
    except AttributeError as cause:
        raise error.DrollError(str(cause)) from cause

    # Undo the prior transformation by subtracting prior_treasure.
    game = game._replace(
        party=game.party._replace(**{
            hero: getattr(game.party, hero) - getattr(prior_treasure, artifact)
            for hero, artifact in player.artifacts._asdict().items()
            if artifact is not None
        })
    )

    # Consume treasure equivalent to any hero which has gone negative.
    for hero, quantity in game.party._asdict().items():
        if quantity >= 0:
            continue
        for _ in range(-min(0, quantity)):
            game = world.replace_treasure(game, getattr(player.artifacts, hero))
        game = game._replace(party=game.party._replace(**{hero: 0}))

    return game


def partify(token: str, artifacts: world.Party):
    """Possibly convert tokens from treasures into associated party members."""
    if token is None:
        return None
    for party, artifact in artifacts._asdict().items():
        if token == artifact:
            return party
    return token


DEFAULT = Player(
    bait=action.bait_dragon,
    elixir=action.elixir,
    portal=action.portal,
    ring=action.ring,
    artifacts=world.Party(
        fighter='sword',
        cleric='talisman',
        mage='sceptre',
        thief='tools',
        champion=None,
        scroll='scroll',
    ),
    party=world.Party(
        fighter=world.Dungeon(
            goblin=action.defeat_all,
            skeleton=action.defeat_one,
            ooze=action.defeat_one,
            chest=action.open_one,
            potion=action.quaff,
            dragon=action.defeat_dragon,
        ),
        cleric=world.Dungeon(
            goblin=action.defeat_one,
            skeleton=action.defeat_all,
            ooze=action.defeat_one,
            chest=action.open_one,
            potion=action.quaff,
            dragon=action.defeat_dragon,
        ),
        mage=world.Dungeon(
            goblin=action.defeat_one,
            skeleton=action.defeat_one,
            ooze=action.defeat_all,
            chest=action.open_one,
            potion=action.quaff,
            dragon=action.defeat_dragon,
        ),
        thief=world.Dungeon(
            goblin=action.defeat_one,
            skeleton=action.defeat_one,
            ooze=action.defeat_one,
            chest=action.open_all,
            potion=action.quaff,
            dragon=action.defeat_dragon,
        ),
        champion=world.Dungeon(
            goblin=action.defeat_all,
            skeleton=action.defeat_all,
            ooze=action.defeat_all,
            chest=action.open_all,
            potion=action.quaff,
            dragon=action.defeat_dragon,
        ),
        # Technically scrolls could re-roll potions,
        # but doing so would be a really peculiar choice.
        scroll=world.Dungeon(
            goblin=action.reroll,
            skeleton=action.reroll,
            ooze=action.reroll,
            chest=action.reroll,
            potion=action.quaff,
            dragon=action.defeat_dragon,
        ),
    ),
)
