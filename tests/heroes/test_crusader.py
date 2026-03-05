# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Tests for Crusader/Paladin hero abilities."""

import random
import pytest

from droll import player, struct
from droll.ability import crusader_ability, paladin_ability
from droll.heroes.crusader import Crusader, Paladin
from droll.struct import Action, Artifact, Dungeon, Party, make_dungeon, make_party, make_artifacts

# Known to be unused because it would raise NameErrors on any use
_UNUSED = object()


def test_crusader_ability_adds_fighter():
    """Crusader ability adds a fighter to party."""
    world = struct.World(
        ability=True,
        party=make_party(fighter=1, cleric=1),
    )
    result = crusader_ability(world, _UNUSED, Action.ABILITY, (Party.FIGHTER,))
    assert result.party[Party.FIGHTER] == 2
    assert not result.ability


def test_crusader_ability_adds_cleric():
    """Crusader ability adds a cleric to party."""
    world = struct.World(
        ability=True,
        party=make_party(fighter=1, cleric=1),
    )
    result = crusader_ability(world, _UNUSED, Action.ABILITY, (Party.CLERIC,))
    assert result.party[Party.CLERIC] == 2


def test_crusader_ability_rejects_invalid_target():
    """Crusader ability rejects invalid targets like mage."""
    world = struct.World(
        ability=True,
        party=make_party(fighter=1, cleric=1),
    )
    with pytest.raises(struct.DrollError):
        crusader_ability(world, _UNUSED, Action.ABILITY, (Party.MAGE,))


def test_crusader_advances_to_paladin():
    """Crusader advances to Paladin at 5+ experience."""
    low_xp = struct.World(experience=4)
    high_xp = struct.World(experience=5)
    assert Crusader.advance(low_xp) == Crusader
    assert Crusader.advance(high_xp) == Paladin


def test_paladin_ability_clears_dungeon():
    """Paladin ability consumes treasure and clears dungeon."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=2, skeleton=1, dragon=1),
        party=make_party(fighter=1, cleric=1),
        treasure=struct.Treasure(
            own=make_artifacts(elixir=1),
            box=make_artifacts(sword=1, talisman=1),
        ),
    )
    result = paladin_ability(world, _UNUSED, Action.ABILITY, (Artifact.ELIXIR,))
    assert sum(result.dungeon.values()) == 0
    assert result.treasure.own[Artifact.ELIXIR] == 0
    assert not result.ability


def test_paladin_ability_opens_chests():
    """Paladin ability draws treasure for each chest."""
    randrange = random.Random(4).randrange
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(chest=2),
        party=make_party(fighter=1),
        treasure=struct.Treasure(
            own=make_artifacts(bait=1),
            box=make_artifacts(sword=1, talisman=1, sceptre=1),
        ),
    )
    pre_treasure = sum(world.treasure.own.values())
    result = paladin_ability(world, randrange, Action.ABILITY, (Artifact.BAIT,))
    post_treasure = sum(result.treasure.own.values())
    assert post_treasure == pre_treasure - 1 + 2  # -1 consumed, +2 from chests


def test_paladin_ability_revives_from_potions():
    """Paladin ability revives heroes from potions."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(potion=2),
        party=make_party(fighter=1),
        treasure=struct.Treasure(own=make_artifacts(elixir=1)),
    )
    result = paladin_ability(
        world, _UNUSED, Action.ABILITY, (Artifact.ELIXIR, Party.MAGE, Party.THIEF)
    )
    assert result.party[Party.MAGE] == 1
    assert result.party[Party.THIEF] == 1


def test_crusader_ability_default_target():
    """Crusader ability defaults to 'cleric' (first sorted) when no target."""
    world = struct.World(
        ability=True,
        party=make_party(fighter=1, cleric=1),
    )
    result = crusader_ability(world, _UNUSED, Action.ABILITY)
    assert result.party[Party.CLERIC] == 2


def test_paladin_ability_wrong_revivable_count():
    """Paladin ability rejects wrong number of heroes for potions."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(potion=2),
        party=make_party(fighter=1),
        treasure=struct.Treasure(own=make_artifacts(elixir=1)),
    )
    with pytest.raises(struct.DrollError):
        paladin_ability(world, _UNUSED, Action.ABILITY, (Artifact.ELIXIR, Party.MAGE))


def test_paladin_ability_requires_treasure():
    """Paladin ability fails without specifying treasure."""
    world = struct.World(
        ability=True,
        party=make_party(fighter=1),
        treasure=struct.Treasure(own=make_artifacts(elixir=1)),
    )
    with pytest.raises(struct.DrollError):
        paladin_ability(world, _UNUSED, Action.ABILITY)


def test_paladin_ability_talisman_via_apply(
):
    """Paladin ability with 'talisman' artifact must not be mangled (#181).

    When the user types 'ability talisman', _partify_all() was converting
    'talisman' to 'cleric' before paladin_ability could consume it as a
    treasure name, producing "'Artifacts' object has no attribute 'cleric'"."""
    world = struct.World(
        ability=True,
        dungeon=make_dungeon(goblin=2, skeleton=1, dragon=1),
        party=make_party(fighter=1, cleric=1),
        treasure=struct.Treasure(
            own=make_artifacts(talisman=1),
            box=make_artifacts(sword=1),
        ),
    )
    result = player.apply(Paladin, world, _UNUSED, "ability", "talisman")
    assert sum(result.dungeon.values()) == 0
    assert result.treasure.own[Artifact.TALISMAN] == 0
    assert not result.ability
