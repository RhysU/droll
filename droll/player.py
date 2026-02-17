# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with player action mechanics."""
from __future__ import annotations

import collections.abc
from dataclasses import replace

from . import action
from . import dice
from . import error
from . import struct
from .world import replace_treasure

__all__ = (
    "Default",
    "apply",
    "complete",
)

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
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: str | None = None,
    *additional,
) -> struct.World:
    """Apply noun to target within world, returning a new version.

    Processes hero-like artifacts (i.e. not rings/portals/scales).
    Varargs 'additional' permits passing more required information.
    For example, what heroes to revive when quaffing a potion."""
    # Convert any artifacts in the command into any corresponding hero types
    reverse = _artifact_to_hero(player.artifacts)
    noun = _partify(noun, reverse)
    target = _partify(target, reverse)
    additional = tuple(_partify(i, reverse) for i in additional)

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
            return action_(world, randrange, noun, target, *additional)
        except AttributeError as cause:
            raise error.DrollError(str(cause)) from cause

    # Many treasures behave exactly like party members, so
    # convert into party members prior to action invocation.
    prior_treasure = world.treasure
    world = replace(
        world,
        party=replace(
            world.party,
            **{
                hero: getattr(world.party, hero)
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
        world = action.reroll(world, randrange, "scroll", target, *additional)
    else:
        # Apply a hero (possibly phantom per above) to some targets.
        try:
            action_ = getattr(player.party, noun)
            if target is None:
                raise error.DrollError(
                    f'"{noun}" requires some target'
                )
            action_ = getattr(action_, target)
            world = action_(world, randrange, noun, target, *additional)
        except (AttributeError, TypeError) as cause:
            raise error.DrollError(str(cause)) from cause

    # Undo the prior transformation by subtracting prior_treasure.
    world = replace(
        world,
        party=replace(
            world.party,
            **{
                hero: getattr(world.party, hero)
                - getattr(prior_treasure, artifact)
                for hero, artifact in struct.field_items(player.artifacts)
                if artifact is not None
            },
        ),
    )

    # Consume treasure equivalent to any hero which has gone negative.
    for hero, quantity in struct.field_items(world.party):
        if quantity >= 0:
            continue
        for _ in range(-quantity):
            world = replace_treasure(
                world, getattr(player.artifacts, hero)
            )
        world = replace(world, party=replace(world.party, **{hero: 0}))

    return world


def _artifact_to_hero(artifacts: struct.Party) -> typing.Dict[str, str]:
    """Build a reverse mapping from artifact name to hero name."""
    return {
        artifact: hero
        for hero, artifact in struct.field_items(artifacts)
        if artifact is not None
    }


def _partify(token: str, reverse: typing.Dict[str, str]):
    """Possibly convert tokens from treasures into associated party members."""
    if token is None:
        return None
    return reverse.get(token, token)


# Early tokens dominated by items/dice that can be applied/attacked.
# Later tokens contain mixtures of present and requested items.
# Attempts to specialize much beyond this seem to quickly go awry.
# One notable special case is 'elixir' as any party die follows.

# Treasures excluded from completion because they lack associated commands.
# Portal and ring are auto-used; scale is for scoring only.
_TREASURE_NO_COMMAND = frozenset({"portal", "ring", "scale"})


def complete(
    world: struct.World, tokens: collections.abc.Sequence[str], text: str, position: int
) -> collections.abc.Sequence[str]:
    """Possible completions for text with position among (partial) tokens."""
    # First compute candidate completions independent of observed text
    if position == 0:
        candidates = {
            key
            for source in (world.party, world.treasure)
            if source is not None
            for key, value in struct.field_items(source)
            if value and key not in _TREASURE_NO_COMMAND
        }
        # Special command "reroll" is available iff "scroll" is available
        if "scroll" in candidates:
            candidates.add("reroll")
    elif position == 1 and tokens[0] == "elixir":
        candidates = {key for key in struct.field_names(struct.Party)}
    elif position == 1:
        candidates = {
            key
            for source in (world.party, world.dungeon)
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
