# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Type definitions, generally of the struct-like variety."""
import collections
import typing


Dungeon = collections.namedtuple('Dungeon', (
    'goblin',
    'skeleton',
    'ooze',
    'chest',
    'potion',
    'dragon',
))

Party = collections.namedtuple('Party', (
    'fighter',
    'cleric',
    'mage',
    'thief',
    'champion',
    'scroll',
))

Roll = collections.namedtuple('Roll', [
    'dungeon',
    'party',
])

Player = collections.namedtuple('Player', (
    'ability',
    'advance',
    'bait',
    'elixir',
    'portal',
    'ring',
    'roll',
    'artifacts',
    'party',
))

_RESERVE = collections.OrderedDict((
    ('sword', 3),
    ('talisman', 3),
    ('sceptre', 3),
    ('tools', 3),
    ('scroll', 3),
    ('elixir', 3),
    ('bait', 4),
    ('portal', 4),
    ('ring', 4),
    ('scale', 6),
))

Treasure = collections.namedtuple('Treasure', _RESERVE.keys())

RESERVE_INITIAL = Treasure(*_RESERVE.values())

TREASURE_INITIAL = Treasure(*([0] * len(_RESERVE)))

World = collections.namedtuple('World', (
    'delve',
    'depth',
    'experience',
    'dungeon',
    'party',
    'ability',
    'treasure',
    'reserve',
))


def brief(o: typing.Any, *, omitted: typing.Set[str] = {'reserve'}) -> str:
    """A __str__(...) variant suppressing False fields within namedtuples."""
    fields = getattr(o, '_fields', None)
    if fields is None:
        return str(o)

    keyvalues = []
    for field, value in zip(fields, o):
        if value and field not in omitted:
            keyvalues.append('{}={}'.format(field, brief(value)))
    return '({})'.format(', '.join(keyvalues))
