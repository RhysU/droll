# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Top-level entry points and basic utilities."""
import typing


def brief(o: typing.Any) -> str:
    """A __str__(...) variant suppressing False fields within namedtuples."""
    fields = getattr(o, '_fields', None)
    if fields is None:
        return str(o)

    keyvalues = []
    for field, value in zip(fields, o):
        if value:
            keyvalues.append('{}={}'.format(field, brief(value)))
    return '{}({})'.format(o.__class__.__name__, ', '.join(keyvalues))
