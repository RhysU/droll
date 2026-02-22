Beta Tester Report: README Review + 100 Games Played
=====================================================

## Methodology

1. Read only the README.
2. Wrote a strategy bot and played 100 games (all 9 heroes, seeds 1–100).
3. Catalogued every confusion point, error message, and misunderstanding.
4. Read the code to understand actual behavior.
5. Proposed fixes (README and code).

### Playing experience

- **First attempt** (README understanding only): 55 of 100 games stuck
  in infinite loops due to misunderstood rules.  Common traps: wrong
  potion syntax, trying to use ring/portal as explicit commands, wrong
  ability argument counts.
- **After correcting misunderstandings** (from error messages and `help`):
  All 100 games completed; avg score 15.7, range 5–32.

A careful reader of the README still misunderstands enough mechanics
to break >50% of games.  That is the core finding.

---

## 13 Confusing or Misleading Aspects

### 1. Potion syntax — unexplained hero-count constraint

**README**: The combat table lists potions but never explains the
syntax.  Only a `help fighter` example buried in the walkthrough shows
`fighter potion mage thief`.

**Reality**: `<hero> potion <revive1> <revive2> ...` where the revive
count must *exactly* equal the number of potions in the dungeon.
Error: "Exactly N heroes to revive required."

**Code**: `regular.py:quaff()` validates `len(targets) - 1 != howmany`.

### 2. Portal — described as a command, actually auto-consumed

**README**: *"A portal immediately ends the delve, scoring your current
depth as experience."*  Reads as though you type `portal`.

**Reality**: Portal is auto-consumed when you type `retire` with
monsters present.  Typing `portal` gives "To use a portal, directly
'retire'."

**Code**: `world.py:retire()` calls `_apply_portal()`.
`player.py:apply()` raises `DrollError` on direct `portal`.

### 3. Ring — described as a choice, actually auto-consumed

**README**: *"A ring lets you ignore a blocking dragon without removing
the dragon dice."*  Reads as though you decide to use it.

**Reality**: Auto-consumed when you `descend` or `retire` past a
blocking dragon.  Typing `ring` gives "To use a ring, directly
'descend' or 'retire'."

**Code**: `world.py:descend()` calls `_apply_ring()`.

### 4. "Regroup" — used but never defined

**README**: Uses `~D` notation, says "discarded at the next regroup."
Never defines what regroup is or when it happens.

**Reality**: Regroup happens before every descend, retire, or retreat.
Temporary allies from abilities are discarded.

**Code**: `world.py:_regroup()` subtracts `regroup.discard` counts.

### 5. `Available:` line omits most valid commands

**README**: Shows the `Available:` line in examples without explanation.

**Reality**: Only lists structural commands (`ability`, `descend`,
`retire`, `retreat`, `reroll`, `undo`).  Party members, treasure items,
and `help` are never shown.  A player seeing `Available: retreat` has
no obvious indication that `fighter goblin` is valid.

**Code**: `shell.py:_AVAILABLE_COMMANDS` is a hard-coded set of six
command names.

### 6. No "Game Over" message

**README**: No mention of end-of-game behavior.

**Reality**: After the third delve the display shows `Available: None`
and a prompt.  No score announcement.  Player must realize it is over.

**Code**: `game.py:_next_delve()` catches `DrollError` and returns
`GameState.STOP`, which silently terminates the command loop.

### 7. Invalid commands expose Python internals

**README**: No mention of error handling.

**Reality**: Typing `foo` produces `'Party' object has no attribute
'foo'` — a raw `AttributeError`.

**Code**: `player.py:apply()` does `getattr(player.party, command)`.
The `AttributeError` is not caught or wrapped.

### 8. Scroll / reroll — two names, overlapping function

**README**: Scrolls are in the combat table; `reroll <targets>` is
mentioned separately.  The relationship between the two is never stated.

**Reality**: `reroll <targets>` is a command that consumes a party
scroll to re-roll dice.  `scroll potion <heroes>` is a separate command
for quaffing potions.  Both spend a scroll.

**Code**: `game.py:reroll()` consumes a scroll explicitly.
`scroll potion ...` routes through normal party dispatch.

### 9. Treasure-as-command syntax never shown

**README**: Says sword is "Usable as a fighter," etc.  Never shows what
to type.

**Reality**: `sword goblin`, `talisman skeleton`, `elixir champion`,
`bait`.

**Code**: `player.py:_partify_all()` maps artifact names to hero names.

### 10. "Defeats one each" is ambiguous

**README table**: Column header "Defeats one each" implies simultaneous
multi-type targeting.

**Reality**: Defeats one monster of one type per use.  `fighter
skeleton` kills one skeleton, not one of each non-favored type.

**Code**: `regular.py:defeat_one()` decrements exactly one of the
target type.

### 11. Dragon fight prerequisite unstated

**README**: *"the dragon blocks progress and must be fought by 3
distinct party members."*

**Reality**: Other monsters must be cleared first.  Error: "Enemy dragon
only comes after all others defeated."

**Code**: `regular.py:_fight_dragon()` checks `defeated_monsters()`.

### 12. Level-up "each counts as" is opaque

**README table**: "Each counts as either fighter or cleric" for Paladin.

**Reality**: Any party member can be typed as either type's command —
the game treats all dice as valid for either role.  The README never
explains this mechanic.

**Code**: Hero-specific `Party` dataclasses override member actions.

### 13. Must descend before retiring — undocumented

**README**: Silent on this constraint.

**Reality**: `retire` at depth 0 gives "Descend at least once prior
to retiring."

**Code**: `world.py:retire()` checks `world.depth == 0`.

---

## Proposals

### README documentation fixes

| #    | Issue                       | Proposal |
|------|-----------------------------|----------|
| P1   | Potion syntax (§1)          | Add a "Potions" subsection: `<hero> potion <revive_targets>` with the count constraint. |
| P2   | Portal / ring (§2, §3)      | Rewrite to say each is consumed *automatically* on `retire`/`descend`; they are not standalone commands. |
| P3   | Define regroup (§4)         | Add: "Between depths (and when leaving the dungeon), a *regroup* phase discards temporary allies." |
| P4   | Explain `Available:` (§5)   | Add: "`Available:` shows structural commands.  Party members and treasures are always usable — type `help` for the full list." |
| P5   | Column header (§10)         | Change "Defeats one each" → "Defeats one". |
| P6   | Dragon prerequisite (§11)   | Add: "Other monsters must be cleared before fighting the dragon." |
| P7   | Treasure syntax (§9)        | Add examples: `sword goblin`, `elixir champion`, `bait`. |
| P8   | Descend-before-retire (§13) | Add: "You must descend at least once before retiring." |
| P9   | Scroll / reroll (§8)        | State: "`reroll <targets>` re-rolls dice (costs a scroll).  `scroll potion <heroes>` quaffs potions (also costs a scroll)." |

### Code fixes

| #    | Issue                       | Proposal |
|------|-----------------------------|----------|
| C1   | Python internals leak (§7)  | In `player.py:apply()`, catch `AttributeError` and raise `DrollError(f"Unknown command: {command}")`. |
| C2   | No game-over message (§6)   | In `shell.py:postcmd()`, print "Game over! Final score: N" when `stop` is truthy. |
| C3   | `Available:` label (§5)     | Rename to `Actions:` or include party/treasure commands. |
