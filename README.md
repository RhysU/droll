Droll
=====
[![CircleCI](https://circleci.com/gh/RhysU/droll/tree/master.svg?style=svg)](https://circleci.com/gh/RhysU/droll/tree/master)

## What is it?

Droll implements [Dungeon Roll](https://boardgamegeek.com/boardgame/138788/dungeon-roll),
a product of [Tasty Minstrel Games](https://boardgamegeek.com/boardgamepublisher/9499/tasty-minstrel-games).
Droll is in no way affiliated with either the game or the publisher.  Go buy
their excellent game, learn [how to play](https://www.youtube.com/watch?v=PzZ8hUzXBtE)
it, and then come back here.

## What is implemented?

An interactive command-line interface for playing the base game
without expansions, with tab completion for commands and
context-sensitive arguments such as party members, monsters,
and treasures.
All base game heroes are implemented.

## Why implement it?

In 2018, it seemed like a fun thing to hack on.  Also, I was curious how
much code was required to capture a game that children will catch onto in
the space of 20 minutes.  In 2026, this codebase has been a self-contained
playspace for LLM-assisted coding.

This game has always seemed like a neat problem to throw into reinforcement
learning algorithms as the strategy isn't too complicated, the score
is very straightforward, and there's probabilistic behavior in both the
basic die mechanics as well as the expected value of the treasure.  That
said, I've done such things in neither 2018 nor 2026.

## What does it look like?

```
$ droll --help
usage: droll [-h] [--seed N]
             {Crusader,Enchantress,HalfGoblin,Knight,Mercenary,Minstrel,Occultist,Spellsword}

Command-line version of droll.

positional arguments:
  {Crusader,Enchantress,HalfGoblin,Knight,Mercenary,Minstrel,Occultist,Spellsword}
                        Select the hero for this game.

options:
  -h, --help            show this help message and exit
  --seed N              An integer to seed random number generation.


$ droll --seed 7 Knight
--- Knight ---
    Convert all monster faces into dragon dice.

        Example: ability

Score 0:  delve 1 with 0 XP plus 0 treasure
Treasure: None
Consider: descend
Party:    fighter×2 cleric mage thief champion×2
Dungeon:  None
00 Knight> descend

Score 0:  depth 1 in delve 1 with 0 XP plus 0 treasure
Treasure: None
Consider: ability retreat(+0 score)
Party:    fighter×2 cleric mage thief champion×2
Dungeon:  goblin
01 Knight> help fighter
Fighters defeat ALL goblins but only ONE skeleton or ooze:

        fighter goblin                # Defeat all goblins
        fighter skeleton              # Defeat one skeleton
        fighter ooze                  # Defeat one ooze
        fighter chest                 # Open one chest
        fighter potion mage thief       # Drink 2 potions obtaining mage, thief
        fighter dragon cleric mage      # Attack dragon with party of 3


Score 0:  depth 1 in delve 1 with 0 XP plus 0 treasure
Treasure: None
Consider: ability retreat(+0 score)
Party:    fighter×2 cleric mage thief champion×2
Dungeon:  goblin
01 Knight> fighter goblin

Score 0:  depth 1 in delve 1 with 0 XP plus 0 treasure
Treasure: None
Consider: descend retire(+1 score) undo
Party:    fighter cleric mage thief champion×2
Dungeon:  None
02 Knight> descend

Score 0:  depth 2 in delve 1 with 0 XP plus 0 treasure
Treasure: None
Consider: ability retreat(+0 score)
Party:    fighter cleric mage thief champion×2
Dungeon:  ooze potion
03 Knight> mage ooze

Score 0:  depth 2 in delve 1 with 0 XP plus 0 treasure
Treasure: None
Consider: descend retire(+2 score) undo
Party:    fighter cleric thief champion×2
Dungeon:  potion
04 Knight> champion potion mage

Score 0:  depth 2 in delve 1 with 0 XP plus 0 treasure
Treasure: None
Consider: descend retire(+2 score) undo
Party:    fighter cleric mage thief champion
Dungeon:  None
05 Knight> descend

Score 0:  depth 3 in delve 1 with 0 XP plus 0 treasure
Treasure: None
Consider: ability retreat(+0 score)
Party:    fighter cleric mage thief champion
Dungeon:  goblin skeleton potion
06 Knight> help ability
Invoke the player's ability.

    Convert all monster faces into dragon dice.

        Example: ability

Score 0:  depth 3 in delve 1 with 0 XP plus 0 treasure
Treasure: None
Consider: ability retreat(+0 score)
Party:    fighter cleric mage thief champion
Dungeon:  goblin skeleton potion
06 Knight> ability

Score 0:  depth 3 in delve 1 with 0 XP plus 0 treasure
Treasure: None
Consider: descend retire(+3 score) undo
Party:    fighter cleric mage thief champion
Dungeon:  potion dragon×2
07 Knight> descend

Score 0:  depth 4 in delve 1 with 0 XP plus 0 treasure
Treasure: None
Consider: retreat(+0 score)
Party:    fighter cleric mage thief champion
Dungeon:  goblin×2 chest×2 dragon×2
08 Knight> fighter goblin

Score 0:  depth 4 in delve 1 with 0 XP plus 0 treasure
Treasure: None
Consider: descend retire(+4 score) undo
Party:    cleric mage thief champion
Dungeon:  chest×2 dragon×2
09 Knight> thief chest

Score 2:  depth 4 in delve 1 with 0 XP plus 2 treasure
Treasure: elixir talisman
Consider: descend retire(+4 score)
Party:    cleric mage champion
Dungeon:  dragon×2
10 Knight> descend

Score 2:  depth 5 in delve 1 with 0 XP plus 2 treasure
Treasure: elixir talisman
Consider: retreat(+0 score)
Party:    cleric mage champion
Dungeon:  goblin×2 chest potion×2 dragon×2
11 Knight> champion goblin

Score 2:  depth 5 in delve 1 with 0 XP plus 2 treasure
Treasure: elixir talisman
Consider: descend retire(+5 score) undo
Party:    cleric mage
Dungeon:  chest potion×2 dragon×2
12 Knight> mage potion champion thief

Score 2:  depth 5 in delve 1 with 0 XP plus 2 treasure
Treasure: elixir talisman
Consider: descend retire(+5 score) undo
Party:    cleric thief champion
Dungeon:  chest dragon×2
13 Knight> thief chest

Score 3:  depth 5 in delve 1 with 0 XP plus 3 treasure
Treasure: elixir sceptre talisman
Consider: descend retire(+5 score)
Party:    cleric champion
Dungeon:  dragon×2
14 Knight> retire
--- DragonSlayer ---
    Convert all monster faces into dragon dice.
    Dragons require only 2 distinct party members to defeat.

        Example: ability
        Example: fighter dragon mage

Score 8:  delve 2 with 5 XP plus 3 treasure
Treasure: elixir sceptre talisman
Consider: descend
Party:    fighter cleric champion×5
Dungeon:  None
15 DragonSlayer> descend

Score 8:  depth 1 in delve 2 with 5 XP plus 3 treasure
Treasure: elixir sceptre talisman
Consider: descend retire(+1 score)
Party:    fighter cleric champion×5
Dungeon:  chest
16 DragonSlayer> champion chest

Score 9:  depth 1 in delve 2 with 5 XP plus 4 treasure
Treasure: elixir sceptre talisman×2
Consider: descend retire(+1 score)
Party:    fighter cleric champion×4
Dungeon:  None
17 DragonSlayer> descend

Score 9:  depth 2 in delve 2 with 5 XP plus 4 treasure
Treasure: elixir sceptre talisman×2
Consider: ability retreat(+0 score)
Party:    fighter cleric champion×4
Dungeon:  goblin skeleton
18 DragonSlayer> talisman goblin

Score 9:  depth 2 in delve 2 with 5 XP plus 4 treasure
Treasure: elixir sceptre talisman×2
Consider: ability retreat(+0 score) undo
Party:    fighter champion×4
Dungeon:  skeleton
19 DragonSlayer> sceptre skeleton

Score 8:  depth 2 in delve 2 with 5 XP plus 3 treasure
Treasure: elixir talisman×2
Consider: descend retire(+2 score) undo
Party:    fighter champion×4
Dungeon:  None
20 DragonSlayer> elixir mage

Score 7:  depth 2 in delve 2 with 5 XP plus 2 treasure
Treasure: talisman×2
Consider: descend retire(+2 score) undo
Party:    fighter mage champion×4
Dungeon:  None
21 DragonSlayer> ^D
```

Beyond the "Consider:" line, party members and treasures in
your possession are valid commands.  Type "help" to see
the full list.

The default display uses color when writing to a terminal.
Press Ctrl+D to exit at any time.

## How to play

You get 3 delves into the dungeon per game.  Each delve proceeds
as follows:

1. Roll 7 party dice producing random fighters, clerics, mages,
   thieves, champions, and scrolls.
2. Descend one depth at a time.  At each depth, new dungeon dice
   appear: goblins, skeletons, ooze, chests, potions, and dragons.
3. Use party members to defeat monsters, open chests, and quaff
   potions.  Monsters must be cleared before opening chests, quaffing
   potions, or descending further.
4. After defeating any monsters, "retire" from the delve to earn
   experience equal to your depth.  You must descend at least once
   before retiring.  If monsters remain and you cannot defeat them,
   instead "retreat" but earn nothing.  When you have no way to
   defeat the remaining monsters, retreat is your only option.

Undo: you can `undo` any command that did not involve rolling or drawing.

Combat: each party member can target any monster type.  Against
a favored type they defeat all at once; otherwise they defeat one:

| Hero     | Defeats all | Defeats one            | Special          |
|----------|-------------|------------------------|------------------|
| fighter  | goblin      | skeleton, ooze         | opens one chest  |
| cleric   | skeleton    | goblin, ooze           | opens one chest  |
| mage     | ooze        | goblin, skeleton       | opens one chest  |
| thief    | —           | goblin, skeleton, ooze | opens all chests |
| champion | goblin, skeleton, ooze | —             | opens all chests |
| scroll   | —           | —                      | quaffs potions, rerolls dice |

Potions: any party member can quaff potions.  The syntax is
`<drinker> potion <type1> <type2> ...` where you specify one
die type per potion to recover.  For example,
`fighter potion mage thief` spends the fighter to drink 2
potions, adding a mage and thief to your party.  The number
of recovery targets must equal the number of potions in
the dungeon.

Scrolls cannot target monsters directly.  The `reroll` command
consumes one scroll and re-rolls any number of dungeon or party
dice, for example `reroll goblin skeleton` re-rolls those two
dice.  A scroll can also quaff potions: `scroll potion fighter`
adds a fighter to your party.
Scroll behavior varies by hero: Enchantress/Beguiler can use a
scroll offensively against skeletons, Knight converts scrolls to
champions during party roll, and Mercenary/Commander receives one
bonus scroll, discarded on regroup.

Dragons accumulate across depths.  At 3 or more, the dragon
blocks progress and must be fought by 3 distinct party members.
Defeating a dragon earns 1 experience and draws 1 treasure.
A ring lets you ignore a blocking dragon without removing the
dragon dice.  A portal immediately ends the delve, scoring your
current depth as experience.

Display notation: `name×N` means N dice of that type, for
example `champion×3`.  Dragon dice always show their count, like `dragon×1` or
`dragon×2`, because tracking dragon accumulation is
crucial — at 3 or more, they block progress.
In the party line, `name~D` or `name×N~D` means
D of those dice will be discarded at the next regroup.
Regroup is the cleanup phase when descending, retiring, or
retreating — these temporary dice are allies converted from
monsters by hero abilities.
For example, `thief×2~1` means 2 thieves, 1 temporary.
The prompt shows the move number and current hero name,
for example `00 Knight>`.

### Hero abilities

| Hero        | Ability                          | Syntax example                    | Requires                |
|-------------|----------------------------------|-----------------------------------|-------------------------|
| Crusader    | Add 1 fighter or cleric          | `ability` or `ability cleric`     | —                       |
| Enchantress | Transform 1 monster into potion  | `ability goblin`                  | 1 monster target        |
| HalfGoblin  | Transform 1 goblin into thief    | `ability` or `ability goblin`     | goblin present          |
| Knight      | Convert all monsters to dragons  | `ability`                         | —                       |
| Mercenary   | Defeat any 2 monsters            | `ability goblin skeleton`         | 1–2 monster targets     |
| Minstrel    | Discard all dragon dice          | `ability`                         | —                       |
| Occultist   | Transform 1 skeleton into fighter| `ability` or `ability skeleton`   | skeleton present        |
| Spellsword  | Add 1 fighter or mage            | `ability` or `ability mage`       | —                       |

### Level-up progression

At 5+ experience, each hero advances to a stronger form with an
upgraded ability and enhanced party interactions.  A "Party change"
of "each counts as either X or Y" means every party member can be
used as either type in commands:

| Base        | Advanced      | New ability                          | Party change                            |
|-------------|---------------|--------------------------------------|-----------------------------------------|
| Crusader    | Paladin       | Consume treasure to clear dungeon    | Each counts as either fighter or cleric           |
| Enchantress | Beguiler      | Transform up to 2 monsters to potion | Scrolls target monsters like party members         |
| HalfGoblin  | Chieftain     | Transform up to 2 goblins to thieves | Open chests/quaff potions before clearing monsters |
| Knight      | DragonSlayer  | *(unchanged)*                        | Dragon requires only 2 distinct party members      |
| Mercenary   | Commander     | Reroll any number of dice            | Each fighter use defeats one additional monster     |
| Minstrel    | Bard          | *(unchanged)*                        | Each champion use defeats one additional monster    |
| Occultist   | Necromancer   | Transform up to 2 skeletons to fighters | Each counts as either cleric or mage            |
| Spellsword  | Battlemage    | Discard all monsters, chests, potions | Each counts as either fighter or mage              |

## How does scoring work?

Your score has two components: experience earned by retiring
and treasure.  Experience accumulates across delves.  For
example, retiring at depth 5 earns 5 experience; if you then
retire at depth 3 in the next delve, you have 8 experience total.

Treasure is drawn randomly from a shared box whenever you open
chests.  Each piece of treasure scores 1 point, with two exceptions:

| Treasure   | Points | Notes                                  |
|------------|--------|----------------------------------------|
| sword      | 1      | Usable as a fighter                    |
| talisman   | 1      | Usable as a cleric                     |
| sceptre    | 1      | Usable as a mage                       |
| tools      | 1      | Usable as a thief                      |
| scroll     | 1      | Usable as a scroll                     |
| elixir     | 1      | Add a party member of any type         |
| bait       | 1      | Lure the dragon                        |
| portal     | 2      | Town portal to escape the dungeon      |
| ring       | 1      | Sneak past a dragon                    |
| scale      | 1      | But a pair of scales scores 4          |

Treasures are used by typing them as commands.  `sword goblin`
acts as a fighter, `talisman skeleton` acts as a cleric,
`tools chest` acts as a thief, `elixir mage` adds a mage,
and `bait` converts all monsters to dragons.
Using a treasure during a delve removes it from your collection
and reduces your score accordingly.

Total score = experience + treasure points.

## Quick Start

Requires Python 3.9+.  Clone this repository then run via:

```
PYTHONPATH=. python3 -m droll --help
```

## Installation

Install the package in development mode with:
```
pip install -e .
```

## Testing

Run unit tests with:
```
pytest
```
