# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Top-level module for droll."""
import typing


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
