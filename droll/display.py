# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Compact display formatting for the experimental CLI mode."""

from enum import Enum
from typing import Any, Optional, Sequence

from . import struct

__all__ = (
    "DisplayMode",
    "compact_summary",
)


class DisplayMode(Enum):
    """Display mode for the droll CLI."""

    CURRENT = "current"
    MECHANICAL = "mechanical"


# Dragons always show count (tracking them is crucial to gameplay)
_ALWAYS_COUNT = frozenset({"dragon"})


def _format_item(name: str, count: int, discard: int = 0) -> Optional[str]:
    """Format a single item, returning None if count is zero."""
    if not count:
        return None
    counted = count > 1 or name in _ALWAYS_COUNT
    if discard:
        return f"{name}×{count}~{discard}" if counted else f"{name}~{discard}"
    return f"{name}×{count}" if counted else name


def _format_items(counts: Any, discards: Any = None) -> str:
    """Format dataclass fields as 'name' or 'name×N' or 'name×N-M'."""
    if discards is None:
        parts = (_format_item(n, c) for n, c in struct.field_items(counts))
    else:
        parts = (
            _format_item(n, getattr(counts, n), getattr(discards, n))
            for n in struct.field_names(counts)
        )
    return " ".join(filter(None, parts)) or "None"


def _format_treasure(artifacts: struct.Artifacts) -> str:
    """Format treasure alphabetically."""
    parts = (
        _format_item(n, c) for n, c in sorted(struct.field_items(artifacts))
    )
    return " ".join(filter(None, parts)) or "None"


def _format_available(available: Sequence[str]) -> str:
    """Format available commands alphabetically."""
    return " ".join(sorted(available)) or "None"


def _format_party(
    party: struct.Party,
    discard: struct.Party,
) -> Optional[str]:
    """Format party contents, returning None if empty."""
    if not any(struct.field_values(party)):
        return None
    return _format_items(counts=party, discards=discard)


def _format_dungeon(
    dungeon: Optional[struct.Dungeon],
) -> Optional[str]:
    """Format dungeon contents, returning None only if no dungeon exists."""
    if dungeon is None:
        return None
    return _format_items(dungeon)


def compact_summary(
    w: struct.World,
    player_name: str,
    score: int,
    available: Sequence[str],
) -> str:
    """Format the world state in compact multi-line format."""
    # Compute the width for alignment (prompt width)
    prompt = f"{player_name}>"
    width = max(len(prompt), len("Available:"))

    # Build the location line
    if w.depth:
        location = (
            f"depth {w.depth} in delve {w.delve}"
            f" with experience {w.experience}"
        )
    else:
        location = f"delve {w.delve} with experience {w.experience}"

    # Format each component
    treasure_str = _format_treasure(w.treasure.own)
    party_str = _format_party(w.party, w.regroup.discard)
    available_str = _format_available(available)
    dungeon_str = _format_dungeon(w.dungeon)

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
