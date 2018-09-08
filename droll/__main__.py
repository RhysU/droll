# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Command-line version of droll."""

from .shell import Shell

# TODO Permit specifying seeds
# TODO Permit specifying different players
if __name__ == '__main__':
    s = Shell()
    s.cmdloop()
