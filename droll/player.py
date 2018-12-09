# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with player action mechanics."""

import typing

from . import action
from . import dice
from . import error
from . import struct
from . import world

# Rules governing a default player lacking any special abilities.
# Effectively, this data is one large, dense dispatch table.
# Other players will generally be defined in terms of this one.
Default = struct.Player(
    name='Default',
    # Behavior of special commands?
    ability=action.nop_ability,
    # Advance maps struct.World -> struct.Player, permitting promotion.
    # However, the Default player is not promotable.
    advance=(lambda _: Default),
    bait=action.bait_dragon,
    elixir=action.elixir,
    # Behavior at specific lifecycle events?
    roll=struct.Roll(
        dungeon=dice.roll_dungeon,
        party=dice.roll_party,
    ),
    # How do artifacts map to heroes?
    artifacts=struct.Party(
        fighter='sword',
        cleric='talisman',
        mage='sceptre',
        thief='tools',
        champion=None,
        scroll='scroll',
    ),
    # What effect does each hero have on each enemy?
    party=struct.Party(
        fighter=struct.Dungeon(
            goblin=action.defeat_all,
            skeleton=action.defeat_one,
            ooze=action.defeat_one,
            chest=action.open_one,
            potion=action.quaff,
            dragon=action.defeat_dragon,
        ),
        cleric=struct.Dungeon(
            goblin=action.defeat_one,
            skeleton=action.defeat_all,
            ooze=action.defeat_one,
            chest=action.open_one,
            potion=action.quaff,
            dragon=action.defeat_dragon,
        ),
        mage=struct.Dungeon(
            goblin=action.defeat_one,
            skeleton=action.defeat_one,
            ooze=action.defeat_all,
            chest=action.open_one,
            potion=action.quaff,
            dragon=action.defeat_dragon,
        ),
        thief=struct.Dungeon(
            goblin=action.defeat_one,
            skeleton=action.defeat_one,
            ooze=action.defeat_one,
            chest=action.open_all,
            potion=action.quaff,
            dragon=action.defeat_dragon,
        ),
        champion=struct.Dungeon(
            goblin=action.defeat_all,
            skeleton=action.defeat_all,
            ooze=action.defeat_all,
            chest=action.open_all,
            potion=action.quaff,
            dragon=action.defeat_dragon,
        ),
        # Technically scrolls could re-roll potions,
        # but doing so would be a really peculiar choice.
        scroll=struct.Dungeon(
            goblin=action.reroll,
            skeleton=action.reroll,
            ooze=action.reroll,
            chest=action.reroll,
            potion=action.quaff,
            dragon=action.defeat_dragon,
        ),
    ),
)


def apply(
        player: struct.Player,
        game: struct.World,
        randrange: dice.RandRange,
        noun: str,
        target: str = None,
        *additional
) -> struct.World:
    """Apply noun to target within game, returning a new version.

    Processes hero-like artifacts (i.e. not rings/portals/scales).
    Varargs 'additional' permits passing more required information.
    For example, what heroes to revive when quaffing a potion."""
    # Convert any artifacts in the command into any corresponding hero types
    noun = partify(noun, player.artifacts)
    target = partify(target, player.artifacts)
    additional = tuple(partify(i, player.artifacts) for i in additional)

    # One-off handling of some treasures, with error wrapping to aid usability
    if noun == 'portal':
        raise error.DrollError('To use a portal, directly "retire".')
    if noun == 'ring':
        raise error.DrollError('To use a ring, directly "descend" or "retire".')
    if noun in {'ability', 'bait', 'elixir'}:
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
            for hero, artifact in zip(player.artifacts._fields,
                                      player.artifacts)
            if artifact is not None
        })
    )

    # Apply a hero (possibly phantom per above) to some collection of targets.
    try:
        action = getattr(player.party, noun)
        if target is None:
            raise error.DrollError('"{}" requires some target'.format(noun))
        action = getattr(action, target)
        game = action(game, randrange, noun, target, *additional)
    except AttributeError as cause:
        raise error.DrollError(str(cause)) from cause

    # Undo the prior transformation by subtracting prior_treasure.
    game = game._replace(
        party=game.party._replace(**{
            hero: getattr(game.party, hero) - getattr(prior_treasure, artifact)
            for hero, artifact in zip(player.artifacts._fields,
                                      player.artifacts)
            if artifact is not None
        })
    )

    # Consume treasure equivalent to any hero which has gone negative.
    for hero, quantity in zip(game.party._fields, game.party):
        if quantity >= 0:
            continue
        for _ in range(-min(0, quantity)):
            game = world.replace_treasure(game,
                                          getattr(player.artifacts, hero))
        game = game._replace(party=game.party._replace(**{hero: 0}))

    return game


def partify(token: str, artifacts: struct.Party):
    """Possibly convert tokens from treasures into associated party members."""
    if token is None:
        return None
    for party, artifact in zip(artifacts._fields, artifacts):
        if token == artifact:
            return party
    return token


# Early tokens dominated by items/dice that can be applied/attacked.
# Later tokens contain mixtures of present and requested items.
# Attempts to specialize much beyond this seem to quickly go awry.
# One notable special case is 'elixir' as any party die follows.
def complete(
        game: struct.World,
        tokens: typing.Sequence[str],
        text: str,
        position: int,
) -> typing.Sequence[str]:
    """Possible completions for text with position among (partial) tokens."""
    # First compute candidate completions independent of observed text
    if position == 0:
        candidates = (
            key
            for source in (game.party, game.treasure)
            if source is not None
            for key, value in zip(source._fields, source)
            if value
        )
    elif position == 1 and tokens[0] == 'elixir':
        candidates = (
            key
            for key in struct.Party._fields
        )
    elif position == 1:
        candidates = (
            key
            for source in (game.party, game.dungeon)
            if source is not None
            for key, value in zip(source._fields, source)
            if value
        )
    else:
        candidates = (
            key
            for source in (struct.Party, struct.Dungeon)
            for key in source._fields
        )

    # Then filter to retain only those matching requested text prefix
    return [key for key in candidates if key.startswith(text)]
