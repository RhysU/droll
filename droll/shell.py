# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""A REPL permitting playing a game via a tab-completion shell."""
import cmd
import collections
import textwrap
import typing
from random import Random

from . import action
from . import error
from . import player
from . import struct
from . import world

# TODO Populate intro for Shell
# TODO Improve test coverage for 'undo'
# TODO Include 'undo' in help, when appropriate


# Details necessary to implement undo tracking in Shell
Undo = collections.namedtuple('Undo', (
    'player',
    'randhash',
    'world',
))


class Shell(cmd.Cmd):
    """"REPL permitting playing a game via tab-completion shell."""

    ######################
    # LIFECYCLE BELOW HERE
    ######################

    def __init__(
            self,
            player: struct.Player = player.Default,
            random: Random = None
    ) -> None:
        super(Shell, self).__init__()
        # Review postcmd(...) and do_undo(...) when modifying instance state!
        self._player = player
        self._random = Random() if random is None else random
        self._undo = None
        self._world = None

    def summary(self) -> str:
        """Brief, string description of the present game state."""
        return '(None)' if self._world is None else struct.brief(self._world)

    def preloop(self):
        """Prepare a new game and start the first delve."""
        self._undo = []
        self._world = world.new_game()
        if self._next_delve_or_exit():
            raise RuntimeError('Unexpected True during preloop()')
        # Causes printing of initial world state
        self.postcmd(stop=False, line='')

    def _next_delve_or_exit(self) -> bool:
        """Either start next delve or exit the game, printing final score."""
        try:
            # Record any world updates
            self._world = world.next_delve(self._world,
                                           self._player.roll.party,
                                           self._random.randrange)
            # Permit the player to advance to higher abilities
            self._player = self._player.advance(self._world)
            return False
        except error.DrollError:
            return True

    def postcmd(self, stop, line):
        """Print game state after each commmand and final details on exit."""
        self._update_prompt()
        print()
        if line != 'EOF':
            print(self.summary())
            if stop:
                print(self.prompt)
        return stop

    def _update_prompt(self):
        """Compute a prompt including the current score."""
        score = world.score(self._world) if self._world else 0
        self.prompt = '({} {:-2d}) '.format(self._player.name, score)

    def onecmd(self, line):
        """Performs undo tracking whenever undo won't cause re-roll/re-draw."""
        # Track observable state before and after command processing.
        # Beware that do_undo(...), implemented below, mutates self._undo.
        self._undo.append(self._compute_undo())
        result = super(Shell, self).onecmd(line)
        after = self._compute_undo()

        # Retain only undo candidates that disallow cheating.
        # Okay would be 'Oh! I should have used a fighter on the goblin!'
        # Not okay would be undoing a 'descend' to roll a different dungeon.
        if not self._undo:
            pass  # No prior undo against which to compare
        elif after.randhash != self._undo[-1].randhash:
            self._undo.clear()  # Change in random state purges history
        elif after == self._undo[-1]:
            self._undo.pop()  # Ignore non-changing state (e.g. 'help')
        else:
            pass  # Change retained for possible later 'undo'

        return result

    def _compute_undo(self) -> Undo:
        """Produce an Undo instance comprising all current Shell state."""
        return Undo(player=self._player,
                    randhash=hash(self._random.getstate()),
                    world=self._world)

    def do_undo(self, line):
        """Undo prior commands.  Only permitted when nothing rolled/drawn."""
        with ShellManager():
            no_arguments(line)
            # self._random not mutated-- by onecmd(...) it did not change.
            if len(self._undo) > 1:
                self._undo.pop()  # 'undo' was itself on undo list...
                previous = self._undo.pop()  # ...hence two pops to previous.
                self._player = previous.player
                self._world = previous.world
            else:
                raise error.DrollError("Cannot undo any prior command(s).")
        return False

    def do_EOF(self, line):
        """End-of-file causes shell exit."""
        return True

    def emptyline(self):
        """Empty line causes no action to occur."""
        return self.onecmd('help')

    ####################
    # ACTIONS BELOW HERE
    ####################

    def do_ability(self, line):
        """Invoke the player's ability."""
        with ShellManager():
            self._world = player.apply(self._player, self._world,
                                       self._random.randrange, 'ability',
                                       *parse(line))

    def default(self, line):
        """Apply some named hero or treasure to some collection of nouns."""
        with ShellManager():
            self._world = player.apply(self._player, self._world,
                                       self._random.randrange, *parse(line))

    def do_descend(self, line):
        """Descend to the next depth (in contrast to retiring/retreating)."""
        with ShellManager():
            no_arguments(line)
            self._world = world.next_dungeon(self._world,
                                             self._player.roll.dungeon,
                                             self._random.randrange)

    def do_retire(self, line):
        """Retire to the tavern after successfully clearing a dungeon depth..

        Automatically uses a 'ring' or 'portal' treasure if so required.
        Automatically starts a new delve or ends game, as suitable."""
        with ShellManager():
            no_arguments(line)
            self._world = world.retire(self._world)
            return self._next_delve_or_exit()

    def do_retreat(self, line):
        """Retreat from the dungeon at any time (e.g. after being defeated).

        Automatically starts a new delve or ends game, as suitable."""
        with ShellManager():
            no_arguments(line)
            self._world = world.retreat(self._world)
            return self._next_delve_or_exit()

    #######################
    # COMPLETION BELOW HERE
    #######################

    def completenames(self, text, line, begidx, endidx):
        """Complete possible command names based upon context."""
        # Are any dungeon dice still active?  Distinct from defeating dungeon!
        # Distinct from exhausting dungeon-- could convert potions to dragon!
        dungeon_dice = sum(self._world.dungeon) if self._world.dungeon else 0

        # Which world actions might be taken successfully given game state?
        possible = []
        if self._world.ability and dungeon_dice:
            possible.append('ability')
        with ShellManager(verbose=False):
            world.next_dungeon(self._world,
                               self._player.roll.dungeon,
                               dummy_randrange)
            possible.append('descend')
        with ShellManager(verbose=False):
            world.retire(self._world)
            possible.append('retire')
        with ShellManager(verbose=False):
            world.retreat(self._world)
            possible.append('retreat')
        results = [x for x in possible if x.startswith(text)]

        # Add any hero-related possibilities
        if not world.exhausted_dungeon(self._world.dungeon):
            results += self.completedefault(text, line, begidx, endidx)

        return results

    def completedefault(self, text, line, begidx, endidx):
        """Complete loosely based upon available heroes/treasures/dungeon."""
        # Break line into tokens until and starting from present text
        head = parse(line[:begidx])
        tail = parse(line[begidx:])

        # Bulk of processing elsewhere to simplify unit testing, and because
        # many exceptions silently suppress tab completion in readline.
        raw = player.complete(game=self._world,
                              tokens=head + tail,
                              text=text,
                              position=len(head))

        # Trailing space causes tab completion to insert token separators.
        return [x + ' ' for x in raw]

    #################
    # HELP BELOW HERE
    #################

    doc_header = "Feasible commands (help <command>):"
    doc_hero_template = ("Attack monsters, quaff potions, and open chests"
                         " with a {} like so:")
    doc_hero_example = """
        champion skeleton            # Attack skeleton(s)
        thief chest                  # Open chest(s)
        fighter potion mage thief    # Drink 2 potions obtaining mage, thief
        mage dragon champion cleric  # Attack dragon with party of 3
    """

    # Overrides superclass behavior relying purely on do_XXX(...) methods.
    # Also, lies that help_XXX(...) present for completedefault(...) methods.
    def get_names(self):
        """Compute potential help topics from contextual completions."""
        names = self.completenames(text='', line='', begidx=0, endidx=0)
        return (['do_' + x for x in names] +
                ['help_' + x for x in names
                 if not getattr(self, 'do_' + x, None)])

    def help_ability(self):
        print(self.do_ability.__doc__)
        print()
        print(textwrap.indent(self._player.ability.__doc__, '    '))

    def help_bait(self):
        print(action.bait_dragon.__doc__)

    def help_champion(self):
        print(self.doc_hero_template.format('champion'))
        print(self.doc_hero_example)

    def help_cleric(self):
        print(self.doc_hero_template.format('cleric'))
        print(self.doc_hero_example)

    def help_elixir(self):
        print(action.elixir.__doc__)

    def help_fighter(self):
        print(self.doc_hero_template.format('fighter'))
        print(self.doc_hero_example)

    def help_mage(self):
        print(self.doc_hero_template.format('mage'))
        print(self.doc_hero_example)

    def help_sceptre(self):
        print("""Sceptres behave identically to a mage.""")

    def help_scroll(self):
        print("Scrolls may quaff potions and reroll dungeon dice like so:")
        print("""
            scroll potion mage thief    # Drink 2 potions obtaining mage, thief
            scroll skeleton goblin      # Re-roll all skeletons and goblins
        """)

    def help_sword(self):
        print("""Swords behave identically to a fighter.""")

    def help_talisman(self):
        print("""Talismans behave identically to a cleric.""")

    def help_thief(self):
        print(self.doc_hero_template.format('thief'))
        print(self.doc_hero_example)

    def help_tools(self):
        print("""Tools behave identically to a thief.""")


class ShellManager:
    """Print DrollErrors (if verbose) while propagating other exceptions."""

    def __init__(self, verbose=True):
        self._verbose = verbose

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, error.DrollError):
            if self._verbose:
                print(exc_val)
            return True


def parse(line: str) -> typing.Tuple[str]:
    """Split a line into a tuple of whitespace-delimited tokens."""
    return tuple(line.split())


def no_arguments(line):
    """Raise DrollError if line is non-empty."""
    if line:
        raise error.DrollError('Command accepts no arguments.')


def dummy_randrange(start, stop=None):
    """Non-random psuedorandom generator so that completion is stateless."""
    return start
