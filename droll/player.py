# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with player action mechanics."""

from dataclasses import replace
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
    name="Default",
    # Behavior of special commands?
    ability=action.nop_ability,
    # Advance maps struct.World -> struct.Player, permitting promotion.
    # However, the Default player is not promotable.
    advance=(lambda _: Default),
    bait=action.bait_dragon,
    elixir=action.elixir,
    # Behavior at specific lifecycle events?
    roll=struct.Roll(dungeon=dice.roll_dungeon, party=dice.roll_party),
    # How do artifacts map to heroes?
    artifacts=struct.Party(
        fighter="sword",
        cleric="talisman",
        mage="sceptre",
        thief="tools",
        champion=None,
        scroll="scroll",
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
        # Scrolls can re-roll chests and potions though doing so feels odd.
        # Scrolls can also, less oddly, quaff potions so always assume quaff.
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
    noun = _partify(noun, player.artifacts)
    target = _partify(target, player.artifacts)
    additional = tuple(_partify(i, player.artifacts) for i in additional)

    # One-off handling of some treasures, with error wrapping to aid usability
    if noun == "portal":
        raise error.DrollError('To use a portal, directly "retire".')
    if noun == "ring":
        raise error.DrollError(
            'To use a ring, directly "descend" or "retire".'
        )
    if noun in {"ability", "bait", "elixir"}:
        try:
            action_ = getattr(player, noun)  # Else name collision w/ import
            return action_(game, randrange, noun, target, *additional)
        except AttributeError as cause:
            raise error.DrollError(str(cause)) from cause

    # Many treasures behave exactly like party members, so
    # convert into party members prior to action invocation.
    prior_treasure = game.treasure
    game = replace(
        game,
        party=replace(
            game.party,
            **{
                hero: getattr(game.party, hero)
                + getattr(prior_treasure, artifact)
                for hero, artifact in struct.field_items(player.artifacts)
                if artifact is not None
            },
        ),
    )

    if noun == "reroll":
        # Re-roll is a special verb that always overrides scroll settings
        # found within struct.Player so, e.g., Beguiler can re-roll dice
        # with "reroll skeleton" because "scroll skeleton" kills a skeleton.
        game = action.reroll(game, randrange, "scroll", target, *additional)
    else:
        # Apply a hero (possibly phantom per above) to some targets.
        try:
            action_ = getattr(player.party, noun)
            if target is None:
                raise error.DrollError(
                    '"{}" requires some target'.format(noun)
                )
            action_ = getattr(action_, target)
            game = action_(game, randrange, noun, target, *additional)
        except AttributeError as cause:
            raise error.DrollError(str(cause)) from cause

    # Undo the prior transformation by subtracting prior_treasure.
    game = replace(
        game,
        party=replace(
            game.party,
            **{
                hero: getattr(game.party, hero)
                - getattr(prior_treasure, artifact)
                for hero, artifact in struct.field_items(player.artifacts)
                if artifact is not None
            },
        ),
    )

    # Consume treasure equivalent to any hero which has gone negative.
    for hero, quantity in struct.field_items(game.party):
        if quantity >= 0:
            continue
        for _ in range(-min(0, quantity)):
            game = world.replace_treasure(
                game, getattr(player.artifacts, hero)
            )
        game = replace(game, party=replace(game.party, **{hero: 0}))

    return game


def _partify(token: str, artifacts: struct.Party):
    """Possibly convert tokens from treasures into associated party members."""
    if token is None:
        return None
    for party, artifact in struct.field_items(artifacts):
        if token == artifact:
            return party
    return token


# Early tokens dominated by items/dice that can be applied/attacked.
# Later tokens contain mixtures of present and requested items.
# Attempts to specialize much beyond this seem to quickly go awry.
# One notable special case is 'elixir' as any party die follows.

# Treasures excluded from completion because they lack associated commands.
# Portal and ring are auto-used; scale is for scoring only.
TREASURE_NO_COMMAND = frozenset({"portal", "ring", "scale"})


def complete(
    game: struct.World, tokens: typing.Sequence[str], text: str, position: int
) -> typing.Sequence[str]:
    """Possible completions for text with position among (partial) tokens."""
    # First compute candidate completions independent of observed text
    if position == 0:
        candidates = {
            key
            for source in (game.party, game.treasure)
            if source is not None
            for key, value in struct.field_items(source)
            if value and key not in TREASURE_NO_COMMAND
        }
        # Special command "reroll" is available iff "scroll" is available
        if "scroll" in candidates:
            candidates.add("reroll")
    elif position == 1 and tokens[0] == "elixir":
        candidates = {key for key in struct.field_names(struct.Party)}
    elif position == 1:
        candidates = {
            key
            for source in (game.party, game.dungeon)
            if source is not None
            for key, value in struct.field_items(source)
            if value
        }
    else:
        candidates = {
            key
            for source in (struct.Party, struct.Dungeon)
            for key in struct.field_names(source)
        }

    # Then filter to retain only those matching requested text prefix
    return sorted(key for key in candidates if key.startswith(text))
