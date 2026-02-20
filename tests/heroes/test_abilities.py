# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Catalog of every hero ability method assigned via ability= in droll/heroes/*.py."""

from droll.heroes.crusader import Crusader, Paladin, _crusader_ability, _paladin_ability
from droll.heroes.enchantress import Beguiler, Enchantress, _beguiler_ability, _enchantress_ability
from droll.heroes.halfgoblin import Chieftain, HalfGoblin, _chieftain_ability, _halfgoblin_ability
from droll.heroes.knight import DragonSlayer, Knight, _knight_bait_dragon
from droll.heroes.mercenary import Commander, Mercenary, _commander_ability, _mercenary_ability
from droll.heroes.minstrel import Bard, Minstrel, _minstrel_ability
from droll.heroes.occultist import Necromancer, Occultist, _necromancer_ability, _occultist_ability
from droll.heroes.spellsword import Battlemage, Spellsword, _battlemage_ability, _spellsword_ability


def test_crusader_ability():
    """Crusader ability is _crusader_ability."""
    assert Crusader.ability is _crusader_ability


def test_paladin_ability():
    """Paladin ability is _paladin_ability."""
    assert Paladin.ability is _paladin_ability


def test_enchantress_ability():
    """Enchantress ability is _enchantress_ability."""
    assert Enchantress.ability is _enchantress_ability


def test_beguiler_ability():
    """Beguiler ability is _beguiler_ability."""
    assert Beguiler.ability is _beguiler_ability


def test_halfgoblin_ability():
    """HalfGoblin ability is _halfgoblin_ability."""
    assert HalfGoblin.ability is _halfgoblin_ability


def test_chieftain_ability():
    """Chieftain ability is _chieftain_ability."""
    assert Chieftain.ability is _chieftain_ability


def test_knight_ability():
    """Knight ability is _knight_bait_dragon."""
    assert Knight.ability is _knight_bait_dragon


def test_dragonslayer_ability():
    """DragonSlayer ability is _knight_bait_dragon."""
    assert DragonSlayer.ability is _knight_bait_dragon


def test_mercenary_ability():
    """Mercenary ability is _mercenary_ability."""
    assert Mercenary.ability is _mercenary_ability


def test_commander_ability():
    """Commander ability is _commander_ability."""
    assert Commander.ability is _commander_ability


def test_minstrel_ability():
    """Minstrel ability is _minstrel_ability."""
    assert Minstrel.ability is _minstrel_ability


def test_bard_ability():
    """Bard ability is _minstrel_ability."""
    assert Bard.ability is _minstrel_ability


def test_occultist_ability():
    """Occultist ability is _occultist_ability."""
    assert Occultist.ability is _occultist_ability


def test_necromancer_ability():
    """Necromancer ability is _necromancer_ability."""
    assert Necromancer.ability is _necromancer_ability


def test_spellsword_ability():
    """Spellsword ability is _spellsword_ability."""
    assert Spellsword.ability is _spellsword_ability


def test_battlemage_ability():
    """Battlemage ability is _battlemage_ability."""
    assert Battlemage.ability is _battlemage_ability
