# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Functionality associated with player action mechanics."""

from collections.abc import Sequence
from dataclasses import replace

from . import ability, dice, regular, struct
from .struct import (
    Action,
    Artifact,
    Dungeon,
    DrollError,
    Party,
    frozen,
)
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
    ability=ability.default_ability,
    # Advance maps struct.World -> struct.Player, permitting promotion.
    # However, the Default player is not promotable.
    advance=(lambda _: Default),
    bait=regular.bait_dragon,
    elixir=regular.elixir,
    # Behavior at specific lifecycle events?
    roll=struct.Roll(dungeon=dice.roll_dungeon, party=dice.roll_party),
    # How do artifacts map to heroes?
    artifacts=frozen({
        Party.FIGHTER: Artifact.SWORD,
        Party.CLERIC: Artifact.TALISMAN,
        Party.MAGE: Artifact.SCEPTRE,
        Party.THIEF: Artifact.TOOLS,
        Party.CHAMPION: None,
        Party.SCROLL: Artifact.SCROLL,
    }),
    # What effect does each hero have on each enemy?
    party=frozen({
        Party.FIGHTER: frozen({
            Dungeon.GOBLIN: regular.defeat_all,
            Dungeon.SKELETON: regular.defeat_one,
            Dungeon.OOZE: regular.defeat_one,
            Dungeon.CHEST: regular.open_one,
            Dungeon.POTION: regular.quaff,
            Dungeon.DRAGON: regular.defeat_dragon,
        }),
        Party.CLERIC: frozen({
            Dungeon.GOBLIN: regular.defeat_one,
            Dungeon.SKELETON: regular.defeat_all,
            Dungeon.OOZE: regular.defeat_one,
            Dungeon.CHEST: regular.open_one,
            Dungeon.POTION: regular.quaff,
            Dungeon.DRAGON: regular.defeat_dragon,
        }),
        Party.MAGE: frozen({
            Dungeon.GOBLIN: regular.defeat_one,
            Dungeon.SKELETON: regular.defeat_one,
            Dungeon.OOZE: regular.defeat_all,
            Dungeon.CHEST: regular.open_one,
            Dungeon.POTION: regular.quaff,
            Dungeon.DRAGON: regular.defeat_dragon,
        }),
        Party.THIEF: frozen({
            Dungeon.GOBLIN: regular.defeat_one,
            Dungeon.SKELETON: regular.defeat_one,
            Dungeon.OOZE: regular.defeat_one,
            Dungeon.CHEST: regular.open_all,
            Dungeon.POTION: regular.quaff,
            Dungeon.DRAGON: regular.defeat_dragon,
        }),
        Party.CHAMPION: frozen({
            Dungeon.GOBLIN: regular.defeat_all,
            Dungeon.SKELETON: regular.defeat_all,
            Dungeon.OOZE: regular.defeat_all,
            Dungeon.CHEST: regular.open_all,
            Dungeon.POTION: regular.quaff,
            Dungeon.DRAGON: regular.defeat_dragon,
        }),
        # Scrolls re-roll via the 'reroll' command (see issue #133).
        # Using 'scroll' as a noun targets only quaff and dragon.
        Party.SCROLL: frozen({
            Dungeon.GOBLIN: regular.not_reroll,
            Dungeon.SKELETON: regular.not_reroll,
            Dungeon.OOZE: regular.not_reroll,
            Dungeon.CHEST: regular.not_reroll,
            Dungeon.POTION: regular.quaff,
            Dungeon.DRAGON: regular.defeat_dragon,
        }),
    }),
)


def _adjust_phantom_treasures(world, artifacts, treasure, sign):
    """Add (+1) or remove (-1) treasure counts as phantom party members."""
    return replace(
        world,
        party=frozen({
            hero: world.party[hero] + (
                sign * treasure[artifact] if artifact is not None else 0
            )
            for hero, artifact in artifacts.items()
        }),
    )


def _parse_token(token: str) -> Dungeon | Party | Artifact | Action:
    """Convert a string token to the appropriate enum."""
    # Try Action first (ability, bait, elixir, reroll)
    try:
        return Action(token)
    except ValueError:
        pass
    # Try Party
    try:
        return Party(token)
    except ValueError:
        pass
    # Try Dungeon
    try:
        return Dungeon(token)
    except ValueError:
        pass
    # Try Artifact
    try:
        return Artifact(token)
    except ValueError:
        pass
    raise DrollError(f'Unknown token "{token}".')


def apply(
    player: struct.Player,
    world: struct.World,
    randrange: struct.RandRange,
    command: str,
    *targets: str,
) -> struct.World:
    """Apply command to targets within world, returning a new version.

    Processes hero-like artifacts (i.e. not rings/portals/scales).
    For example, what heroes to revive when quaffing a potion."""
    # One-off handling of some treasures, with error wrapping to aid usability
    if command == "portal":
        raise DrollError('To use a portal, directly "retire".')
    if command == "ring":
        raise DrollError(
            "Rings are consumed automatically when a dragon blocks."
            ' Just "descend" or "retire".'
        )

    # Parse command token
    cmd_enum = _parse_token(command)

    # Dispatch ability/bait/elixir before artifact-to-hero translation (#181).
    # These commands define their own target semantics (e.g. paladin_ability
    # expects a treasure name, not a hero name) so _partify_all is wrong here.
    if isinstance(cmd_enum, Action) and cmd_enum in {Action.ABILITY, Action.BAIT, Action.ELIXIR}:
        try:
            if cmd_enum is Action.ABILITY:
                action_ = player.ability
            elif cmd_enum is Action.BAIT:
                action_ = player.bait
            else:
                action_ = player.elixir
            # Parse targets: for ability, paladin expects Artifact targets
            parsed_targets = tuple(_parse_token(t) for t in targets)
            return action_(world, randrange, cmd_enum, parsed_targets)
        except (AttributeError, TypeError, KeyError) as cause:
            if world.dungeon is None:
                raise DrollError("You must descend first.") from cause
            raise DrollError(str(cause)) from cause

    # Reject artifact commands when the player doesn't own the treasure
    if isinstance(cmd_enum, Artifact) and cmd_enum not in {Artifact.SCROLL}:
        if not world.treasure.own.get(cmd_enum, 0):
            raise DrollError(f"'{cmd_enum.value}' not in player's treasure.")

    # Convert artifact command name into corresponding hero type
    hero = _partify_command(player.artifacts, cmd_enum)

    # Parse targets
    parsed_targets = tuple(_parse_token(t) for t in targets)

    # Temporarily inflate party with treasure-as-hero counts
    prior_own = world.treasure.own
    world = _adjust_phantom_treasures(world, player.artifacts, prior_own, +1)

    # Dispatch: reroll always uses scroll mechanics;
    # everything else is hero-target
    if isinstance(cmd_enum, Action) and cmd_enum is Action.REROLL:
        world = regular.reroll(world, randrange, Party.SCROLL, parsed_targets)
    else:
        if hero not in player.party:
            raise DrollError(f'Unknown command "{command}".')
        hero_actions = player.party[hero]
        if not parsed_targets:
            valid = [
                d.value for d in Dungeon
                if world.dungeon is not None and world.dungeon.get(d, 0)
            ]
            hint = f" Available: {', '.join(valid)}." if valid else ""
            raise DrollError(f'"{command}" requires a target.{hint}')
        target0 = parsed_targets[0]
        if target0 not in hero_actions:
            raise DrollError(f'Unknown target "{targets[0]}".')
        if world.dungeon is None:
            raise DrollError("You must descend first.")
        try:
            action_ = hero_actions[target0]
            world = action_(world, randrange, hero, parsed_targets)
        except (AttributeError, TypeError, KeyError) as cause:
            raise DrollError(str(cause)) from cause

    # Undo phantom inflation, then consume treasure for any artifacts spent
    world = _adjust_phantom_treasures(world, player.artifacts, prior_own, -1)
    treasure = world.treasure
    party_updates = {}
    for hero_member, quantity in world.party.items():
        if quantity >= 0:
            continue
        artifact = player.artifacts[hero_member]
        for _ in range(-quantity):
            treasure = replace_treasure(treasure, artifact)
        party_updates[hero_member] = 0
    if party_updates:
        world = replace(
            world,
            party=frozen({**world.party, **party_updates}),
            treasure=treasure,
        )

    return world


def _partify_command(artifacts: struct.ArtifactMapping, command) -> Party:
    """Convert an artifact enum to its hero (Party) enum, or pass through."""
    if isinstance(command, Party):
        return command
    if isinstance(command, Artifact):
        # Reverse lookup: artifact -> hero
        for hero, artifact in artifacts.items():
            if artifact is command:
                return hero
    if isinstance(command, Action) and command is Action.REROLL:
        return Party.SCROLL
    # If it's already a Party enum, return it
    raise DrollError(f'Unknown command "{command.value if hasattr(command, "value") else command}".')


# Artifact names that can be used as commands (sword, talisman, etc.).
# Excludes artifacts whose name matches their hero (e.g. scroll -> scroll),
# since those are already valid party die commands.
_ARTIFACT_COMMANDS = frozenset(
    artifact
    for hero, artifact in Default.artifacts.items()
    if artifact is not None and artifact.value != hero.value
)

# Treasures excluded from completion because they lack associated commands.
# Portal and ring are auto-used; scale is for scoring only.
_TREASURE_NO_COMMAND = frozenset({Artifact.PORTAL, Artifact.RING, Artifact.SCALE})


def _available_nouns(world: struct.World) -> set[str]:
    """Candidate nouns (position 0): available party members and treasures."""
    candidates = set()
    for hero, count in world.party.items():
        if count:
            candidates.add(hero.value)
    for artifact, count in world.treasure.own.items():
        if count and artifact not in _TREASURE_NO_COMMAND:
            candidates.add(artifact.value)
    if Party.SCROLL.value in candidates:
        candidates.add("reroll")
    return candidates


def _available_targets(world: struct.World) -> set[str]:
    """Candidate targets (position 1): available party and dungeon dice."""
    candidates = set()
    for p, count in world.party.items():
        if count:
            candidates.add(p.value)
    if world.dungeon is not None:
        for d, count in world.dungeon.items():
            if count:
                candidates.add(d.value)
    return candidates


def _all_dice_names() -> set[str]:
    """All possible party and dungeon field names (position 2+)."""
    return {p.value for p in Party} | {d.value for d in Dungeon}


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
        candidates = {p.value for p in Party}
    elif position == 1:
        candidates = _available_targets(world)
    else:
        candidates = _all_dice_names()

    return sorted(key for key in candidates if key.startswith(text))
