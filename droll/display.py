# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Compact display formatting for the experimental CLI mode."""
import enum
import typing

from . import struct


class DisplayMode(enum.Enum):
    """Display mode for the droll CLI."""

    CURRENT = "current"
    LEGACY = "legacy"

# Dragons always show count (tracking them is crucial to gameplay)
_ALWAYS_COUNT = frozenset({"dragon"})


def _format_item(name: str, count: int) -> typing.Optional[str]:
    """Format a single item, returning None if count is zero."""
    if not count:
        return None
    if count > 1 or name in _ALWAYS_COUNT:
        return f"{name}×{count}"
    return name


def format_items(instance: typing.Any) -> str:
    """Format dataclass fields as 'name' or 'name×N', in field order."""
    parts = (_format_item(n, c) for n, c in struct.field_items(instance))
    return " ".join(filter(None, parts)) or "none"


def format_treasure(treasure: struct.Treasure) -> str:
    """Format treasure alphabetically."""
    parts = (_format_item(n, c) for n, c in sorted(struct.field_items(treasure)))
    return " ".join(filter(None, parts)) or "none"


def format_available(available: typing.Sequence[str]) -> str:
    """Format available commands alphabetically."""
    return " ".join(sorted(available)) or "None"


def format_dungeon(dungeon: typing.Optional[struct.Dungeon]) -> typing.Optional[str]:
    """Format dungeon contents, returning None if empty."""
    if dungeon is None or not any(struct.field_values(dungeon)):
        return None
    return format_items(dungeon)


def compact_summary(
    w: struct.World,
    player_name: str,
    score: int,
    available: typing.Sequence[str],
) -> str:
    """Format the world state in compact multi-line format."""
    # Compute the width for alignment (prompt width)
    prompt = f"{player_name}>"
    width = max(len(prompt), len("Available:"))

    # Build the location line
    if w.depth:
        location = f"depth {w.depth} in delve {w.delve} with experience {w.experience}"
    else:
        location = f"delve {w.delve} with experience {w.experience}"

    # Format each component
    treasure_str = format_treasure(w.treasure)
    party_str = format_items(w.party) if w.party else "none"
    available_str = format_available(available)
    dungeon_str = format_dungeon(w.dungeon)

    # Build lines with aligned colons
    lines = [
        f"{'Score ' + str(score) + ':':<{width}} {location}",
        f"{'Treasure:':<{width}} {treasure_str}",
        f"{'Available:':<{width}} {available_str}",
        f"{'Party:':<{width}} {party_str}",
    ]
    if dungeon_str:
        lines.append(f"{'Dungeon:':<{width}} {dungeon_str}")

    return "\n".join(lines)
