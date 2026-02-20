# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with player action mechanics."""

from typing import Dict, Optional, Sequence
from dataclasses import replace

from . import dice, regular, struct
from .error import DrollError
from .treasure import replace_treasure

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
    ability=regular.nop_ability,
    # Advance maps struct.World -> struct.Player, permitting promotion.
    # However, the Default player is not promotable.
    advance=(lambda _: Default),
    bait=regular.bait_dragon,
    elixir=regular.elixir,
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
            goblin=regular.defeat_all,
            skeleton=regular.defeat_one,
            ooze=regular.defeat_one,
            chest=regular.open_one,
            potion=regular.quaff,
            dragon=regular.defeat_dragon,
        ),
        cleric=struct.Dungeon(
            goblin=regular.defeat_one,
            skeleton=regular.defeat_all,
            ooze=regular.defeat_one,
            chest=regular.open_one,
            potion=regular.quaff,
            dragon=regular.defeat_dragon,
        ),
        mage=struct.Dungeon(
            goblin=regular.defeat_one,
            skeleton=regular.defeat_one,
            ooze=regular.defeat_all,
            chest=regular.open_one,
            potion=regular.quaff,
            dragon=regular.defeat_dragon,
        ),
        thief=struct.Dungeon(
            goblin=regular.defeat_one,
            skeleton=regular.defeat_one,
            ooze=regular.defeat_one,
            chest=regular.open_all,
            potion=regular.quaff,
            dragon=regular.defeat_dragon,
        ),
        champion=struct.Dungeon(
            goblin=regular.defeat_all,
            skeleton=regular.defeat_all,
            ooze=regular.defeat_all,
            chest=regular.open_all,
            potion=regular.quaff,
            dragon=regular.defeat_dragon,
        ),
        # Scrolls can re-roll chests and potions though doing so feels odd.
        # Scrolls can also, less oddly, quaff potions so always assume quaff.
        scroll=struct.Dungeon(
            goblin=regular.reroll,
            skeleton=regular.reroll,
            ooze=regular.reroll,
            chest=regular.reroll,
            potion=regular.quaff,
            dragon=regular.defeat_dragon,
        ),
    ),
)


def _adjust_phantom_treasures(world, artifacts, treasure, sign):
    """Add (+1) or remove (-1) treasure counts as phantom party members."""
    return replace(
        world,
        party=replace(
            world.party,
            **{
                hero: getattr(world.party, hero) + sign * getattr(treasure, artifact)
                for hero, artifact in struct.field_items(artifacts)
                if artifact is not None
            },
        ),
    )


def apply(
    player: struct.Player,
    world: struct.World,
    randrange: dice.RandRange,
    noun: str,
    target: Optional[str] = None,
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
        raise DrollError('To use a portal, directly "retire".')
    if noun == "ring":
        raise DrollError('To use a ring, directly "descend" or "retire".')
    if noun in {"ability", "bait", "elixir"}:
        try:
            action_ = getattr(player, noun)
            return action_(world, randrange, noun, target, *additional)
        except AttributeError as cause:
            raise DrollError(str(cause)) from cause

    # Temporarily inflate party with treasure-as-hero counts
    prior_own = world.treasure.own
    world = _adjust_phantom_treasures(world, player.artifacts, prior_own, +1)

    # Dispatch: reroll always uses scroll mechanics; everything else is hero-target
    if noun == "reroll":
        world = regular.reroll(world, randrange, "scroll", target, *additional)
    else:
        try:
            action_ = getattr(player.party, noun)
            if target is None:
                raise DrollError(f'"{noun}" requires a target.')
            action_ = getattr(action_, target)
            world = action_(world, randrange, noun, target, *additional)
        except (AttributeError, TypeError) as cause:
            raise DrollError(str(cause)) from cause

    # Undo phantom inflation, then consume treasure for any artifacts spent
    world = _adjust_phantom_treasures(world, player.artifacts, prior_own, -1)
    for hero, quantity in struct.field_items(world.party):
        if quantity >= 0:
            continue
        for _ in range(-quantity):
            world = replace(
                world,
                treasure=replace_treasure(
                    world.treasure, getattr(player.artifacts, hero)
                ),
            )
        world = replace(world, party=replace(world.party, **{hero: 0}))

    return world


def _artifact_to_hero(artifacts: struct.Party) -> Dict[str, str]:
    """Build a reverse mapping from artifact name to hero name."""
    return {
        artifact: hero
        for hero, artifact in struct.field_items(artifacts)
        if artifact is not None
    }


def _partify(token: str, reverse: Dict[str, str]):
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


def _available_nouns(world: struct.World) -> set[str]:
    """Candidate nouns (position 0): available party members and treasures."""
    candidates = {
        key
        for source in (world.party, world.treasure.own)
        if source is not None
        for key, value in struct.field_items(source)
        if value and key not in _TREASURE_NO_COMMAND
    }
    if "scroll" in candidates:
        candidates.add("reroll")
    return candidates


def _available_targets(world: struct.World) -> set[str]:
    """Candidate targets (position 1): available party and dungeon dice."""
    return {
        key
        for source in (world.party, world.dungeon)
        if source is not None
        for key, value in struct.field_items(source)
        if value
    }


def _all_dice_names() -> set[str]:
    """All possible party and dungeon field names (position 2+)."""
    return {
        key
        for source in (struct.Party, struct.Dungeon)
        for key in struct.field_names(source)
    }


def complete(
    world: struct.World,
    tokens: Sequence[str],
    text: str,
    position: int,
) -> Sequence[str]:
    """Possible completions for text with position among (partial) tokens."""
    if position == 0:
        candidates = _available_nouns(world)
    elif position == 1 and tokens[0] == "elixir":
        candidates = set(struct.field_names(struct.Party))
    elif position == 1:
        candidates = _available_targets(world)
    else:
        candidates = _all_dice_names()

    return sorted(key for key in candidates if key.startswith(text))
