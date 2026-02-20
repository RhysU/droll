# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Crusader/Paladin hero abilities."""

import random
import pytest

from droll import struct
from droll.ability import crusader_ability, paladin_ability
from droll.heroes.crusader import Crusader, Paladin

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


def testcrusader_ability_adds_fighter():
    """Crusader ability adds a fighter to party."""
    world = struct.World(
        ability=True,
        party=struct.Party(fighter=1, cleric=1),
    )
    result = crusader_ability(world, _UNUSED, "ability", "fighter")
    assert result.party.fighter == 2
    assert not result.ability


def testcrusader_ability_adds_cleric():
    """Crusader ability adds a cleric to party."""
    world = struct.World(
        ability=True,
        party=struct.Party(fighter=1, cleric=1),
    )
    result = crusader_ability(world, _UNUSED, "ability", "cleric")
    assert result.party.cleric == 2


def testcrusader_ability_rejects_invalid_target():
    """Crusader ability rejects invalid targets like mage."""
    world = struct.World(
        ability=True,
        party=struct.Party(fighter=1, cleric=1),
    )
    with pytest.raises(struct.DrollError):
        crusader_ability(world, _UNUSED, "ability", "mage")


def test_crusader_advances_to_paladin():
    """Crusader advances to Paladin at 5+ experience."""
    low_xp = struct.World(experience=4)
    high_xp = struct.World(experience=5)
    assert Crusader.advance(low_xp) == Crusader
    assert Crusader.advance(high_xp) == Paladin


def testpaladin_ability_clears_dungeon():
    """Paladin ability consumes treasure and clears dungeon."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(goblin=2, skeleton=1, dragon=1),
        party=struct.Party(fighter=1, cleric=1),
        treasure=struct.Treasure(
            own=struct.Artifacts(elixir=1),
            box=struct.Artifacts(sword=1, talisman=1),
        ),
    )
    result = paladin_ability(world, _UNUSED, "ability", "elixir")
    assert sum(struct.field_values(result.dungeon)) == 0
    assert result.treasure.own.elixir == 0
    assert not result.ability


def testpaladin_ability_opens_chests():
    """Paladin ability draws treasure for each chest."""
    randrange = random.Random(4).randrange
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(chest=2),
        party=struct.Party(fighter=1),
        treasure=struct.Treasure(
            own=struct.Artifacts(bait=1),
            box=struct.Artifacts(sword=1, talisman=1, sceptre=1),
        ),
    )
    pre_treasure = sum(struct.field_values(world.treasure.own))
    result = paladin_ability(world, randrange, "ability", "bait")
    post_treasure = sum(struct.field_values(result.treasure.own))
    assert post_treasure == pre_treasure - 1 + 2  # -1 consumed, +2 from chests


def testpaladin_ability_revives_from_potions():
    """Paladin ability revives heroes from potions."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(potion=2),
        party=struct.Party(fighter=1),
        treasure=struct.Treasure(own=struct.Artifacts(elixir=1)),
    )
    result = paladin_ability(
        world, _UNUSED, "ability", "elixir", "mage", "thief"
    )
    assert result.party.mage == 1
    assert result.party.thief == 1


def testcrusader_ability_default_target():
    """Crusader ability defaults to 'cleric' (first sorted) when no target."""
    world = struct.World(
        ability=True,
        party=struct.Party(fighter=1, cleric=1),
    )
    result = crusader_ability(world, _UNUSED, "ability")
    assert result.party.cleric == 2


def testpaladin_ability_wrong_revivable_count():
    """Paladin ability rejects wrong number of heroes for potions."""
    world = struct.World(
        ability=True,
        dungeon=struct.Dungeon(potion=2),
        party=struct.Party(fighter=1),
        treasure=struct.Treasure(own=struct.Artifacts(elixir=1)),
    )
    with pytest.raises(struct.DrollError):
        paladin_ability(world, _UNUSED, "ability", "elixir", "mage")


def testpaladin_ability_requires_treasure():
    """Paladin ability fails without specifying treasure."""
    world = struct.World(
        ability=True,
        party=struct.Party(fighter=1),
        treasure=struct.Treasure(own=struct.Artifacts(elixir=1)),
    )
    with pytest.raises(struct.DrollError):
        paladin_ability(world, _UNUSED, "ability")
