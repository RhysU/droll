# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import collections

Level = collections.namedtuple('Level', (
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

Treasure = collections.namedtuple('Treasure', (
    'sword',
    'talisman',
    'sceptre',
    'tools',
    # Nothing matches champion
    'scroll',
    # Non-hero-like items
    'portal',
    'bait',
    'elixir',
    'scale',
    'ring',
))

World = collections.namedtuple('World', (
    'level',
    'party',
    'treasure',
    'ability',
))
