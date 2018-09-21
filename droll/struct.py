# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Type definitions, generally of the struct-like variety."""
import collections

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
