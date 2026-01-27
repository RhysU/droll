# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Compact display formatting for the experimental CLI mode."""
import typing

from . import struct


def format_items(
    instance: typing.Any,
    always_count: typing.AbstractSet[str] = frozenset({"dragon"}),
) -> str:
    """Format dataclass fields as 'name' or 'name×N', sorted by field order."""
    parts = []
    for name, count in struct.field_items(instance):
        if count == 1 and name not in always_count:
            parts.append(name)
        elif count > 1 or (count == 1 and name in always_count):
            parts.append(f"{name}×{count}")
    return " ".join(parts) if parts else "none"


def format_treasure(treasure: struct.Treasure) -> str:
    """Format treasure alphabetically."""
    items = []
    for name, count in sorted(struct.field_items(treasure)):
        if count == 1:
            items.append(name)
        elif count > 1:
            items.append(f"{name}×{count}")
    return " ".join(items) if items else "none"


def format_available(available: typing.Sequence[str]) -> str:
    """Format available commands alphabetically."""
    return " ".join(sorted(available))


def format_dungeon(dungeon: typing.Optional[struct.Dungeon]) -> typing.Optional[str]:
    """Format dungeon contents, returning None if empty."""
    if dungeon is None:
        return None
    if sum(struct.field_values(dungeon)) == 0:
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
        f"{'Party:':<{width}} {party_str}",
        f"{'Available:':<{width}} {available_str}",
    ]
    if dungeon_str:
        lines.append(f"{'Dungeon:':<{width}} {dungeon_str}")

    return "\n".join(lines)
