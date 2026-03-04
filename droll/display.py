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


def _format_available(
    available: Sequence[str],
    deltas: Optional[dict[str, int]] = None,
) -> str:
    """Format available commands alphabetically, annotating score deltas."""
    return " ".join(
        f"{c}({deltas[c]:+d} score)" if deltas and c in deltas else c
        for c in sorted(available)
    ) or "None"


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
) -> str:
    """Format dungeon contents, always returning a displayable string."""
    if dungeon is None:
        return "None"
    return _format_items(dungeon)


def compact_summary(
    w: struct.World,
    player_name: str,
    score: int,
    available: Sequence[str],
    deltas: Optional[dict[str, int]] = None,
) -> str:
    """Format the world state in compact multi-line format."""
    # Fixed width based on longest label for consistent alignment
    width = len("Consider:")

    # Build the location line with score breakdown
    treasure_score = score - w.experience
    if w.depth:
        location = f"depth {w.depth} in delve {w.delve} with {w.experience} XP plus {treasure_score} treasure"
    else:
        location = f"delve {w.delve} with {w.experience} XP plus {treasure_score} treasure"

    # Format each component
    treasure_str = _format_treasure(w.treasure.own)
    party_str = _format_party(w.party, w.regroup.discard)
    available_str = _format_available(available, deltas)
    dungeon_str = _format_dungeon(w.dungeon)

    # Build lines with aligned colons
    lines = [
        f"{'Score ' + str(score) + ':':<{width}} {location}",
        f"{'Treasure:':<{width}} {treasure_str}",
        f"{'Consider:':<{width}} {available_str}",
        f"{'Party:':<{width}} {party_str}",
    ]
    lines.append(f"{'Dungeon:':<{width}} {dungeon_str}")

    return "\n".join(lines)
