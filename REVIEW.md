Review of Droll: Beta Testing 100 Games
========================================

## Methodology

Played 100 games (12-13 per hero) with TTY color output enabled,
using an automated strategy bot across all 8 base heroes.  Recorded
full game logs including ANSI color codes, then read the source code.

Average score: 2.8 (range 0-12).

## Issues Found and Proposals

### 1. `retire(+N XP)` annotation is misleading — shows net score delta, not XP

**Problem**: `game.py:score_deltas()` computes
`world.score(action(self._world)) - current`, a **net score change**.
But `display.py:_format_available()` labels it `(+N XP)`.  When a
portal (2 pts) or ring (1 pt) is auto-consumed, the displayed number
is less than the actual depth.  At depth 4 with a portal, the player
sees `retire(+2 XP)` instead of the expected `retire(+4 XP)`.

**Proposal A (recommended)**: Change the label from `XP` to `score`:
```python
f"{c}({deltas[c]:+d} score)" if deltas and c in deltas else c
```
This accurately describes what the number represents.

**Proposal B**: Show both raw XP and the cost separately:
`retire(+4 XP, -2 portal)`.  More informative but more complex.

**Proposal C**: Always show the raw XP gain (depth) and ignore
treasure costs in the annotation.  This changes `score_deltas()` to
compute only the experience delta, not the full score delta.  Simpler
to understand but hides the true score impact.

---

### 2. Color scheme is undocumented

**Problem**: Six colors are used (cyan=commands, bright-red=monsters,
dark-red=dragons, gray=None, green=prompt, yellow=help) but none are
documented in-game or in the README.

**Proposal**: Add a one-line legend to the README's display notation
section:

> Colors indicate role: commands and usable party members in cyan,
> monsters in red, dragons in dark red, and inactive elements in gray.

No code change needed; purely a README addition.

---

### 3. Party members lose highlighting when dungeon is empty

**Problem**: `shell.py:84-88` colors only `feasible` commands.  When
the dungeon is empty, party members aren't feasible commands, so they
appear as plain text.  The party didn't change, but it looks different.

**Proposal**: After coloring feasible commands, also color party
members that are present (count > 0) in a distinct muted/dim color
so they remain visually grouped as "your party" rather than appearing
to vanish into the background text.

Alternatively, keep the current behavior but document it: "Cyan
highlighting indicates items you can type as commands right now."

---

### 4. Chests and potions have no color in dungeon display

**Problem**: Monsters are red, dragons are dark red, but chests and
potions are uncolored plain text.  In a dungeon line like
`goblin skeleton chest dragon×1`, the chest is visually lost.

**Proposal**: Color chests and potions in a distinct color (e.g.,
yellow/gold for chests, blue for potions) to distinguish them from
both monsters and plain text.  Add to `shell.py:89-97`:
```python
summary = summary.replace("chest", _CHEST + "chest" + _RESET)
summary = summary.replace("potion", _POTION + "potion" + _RESET)
```

---

### 5. "Score N" vs "with M XP" — dual display is confusing

**Problem**: The score line shows both `Score N:` and `with M XP`.
When they're equal (no treasure), they seem redundant.  When they
differ, the relationship is unexplained.

**Proposal A**: Show the breakdown explicitly:
```
Score 7 (5 XP + 2 treasure): depth 3 in delve 2
```

**Proposal B (simpler)**: Drop "with M XP" from the location text
when Score equals XP (no treasure held), to reduce noise:
```
Score 0:  depth 1 in delve 1
Score 7:  depth 3 in delve 2 with 5 XP  ← only when Score ≠ XP
```

---

### 6. `Consider:` line omits party/treasure commands

**Problem**: `Consider:` only shows meta-commands (descend, retire,
retreat, ability, reroll, undo).  Party members and treasures are
also valid commands but aren't listed.

**Proposal**: This is intentional design — listing every party member
and treasure would make the Consider line very long.  However, a
first-time hint would help.  On the very first move of a game, print
a one-time message:

> Hint: party members and treasures are also valid commands.
> Type "help" for details.

---

### 7. `scroll×3~1` tilde notation is cryptic

**Problem**: The `~D` notation for temporary dice (discarded on
regroup) is only explained in the README.  There's no in-game help
topic for it.

**Proposal**: Add a `help notation` or `help display` topic that
explains the display conventions:
- `name×N` means N dice of that type
- `name×N~D` means D of those are temporary (lost on regroup)
- `dragon×N` always shows count (even ×1)

---

### 8. Hero level-up is completely silent

**Problem**: When the hero advances (e.g., Knight → DragonSlayer at
5+ XP), only the prompt name changes.  No announcement, no
explanation of new abilities.

**Proposal**: Print a level-up message in `game.py:_next_delve()`
when the player name changes:
```python
old_name = self._player.name
self._player = self._player.advance(self._world)
if self._player.name != old_name:
    # Print or signal level-up to the shell
```
The message could include the new ability description:
```
Level up!  Knight → DragonSlayer
  Dragon requires only 2 distinct party members.
```

---

### 9. Error: "Monsters remain so one additional target required"

**Problem**: When Commander/Bard's enhanced combat needs two targets,
this error fires from `special.py:35`.  It doesn't explain the
expected syntax.

**Proposal**: Include an example in the error message:
```python
raise DrollError(
    f"Monsters remain so one additional target required."
    f" Try: {hero} {first_target} <second_monster>"
)
```
Or more specifically: "Monsters remain. Specify a second target,
e.g., 'champion goblin skeleton'."

---

### 10. Error: "Exactly 2 heroes required"

**Problem**: For DragonSlayer (2-hero dragon fight), the error
`regular.py:278` says "Exactly 2 heroes required" but doesn't explain
WHY it's 2 instead of the usual 3.

**Proposal**: Make the error hero-aware:
```
"DragonSlayer fights dragons with 2 heroes, not 3."
```
Or keep the generic message but add a hint:
```
"Exactly 2 heroes required (DragonSlayer needs fewer)."
```

---

### 11. Variable column alignment per hero

**Problem**: `display.py:98` computes `width = max(len(prompt),
len("Consider:"))`, which varies by hero name length.

**Proposal**: Use a fixed minimum width that accommodates the longest
hero name (DragonSlayer = 12 chars → prompt "00 DragonSlayer> " = 17):
```python
width = max(len(prompt), len("Consider:"), 17)
```
This ensures consistent alignment across all heroes.  Alternatively,
use `max(..., 14)` to accommodate "DragonSlayer>" without the number
prefix, keeping alignment stable within a game session even after
level-up.

---

### 12. `Consider: None` at game end looks like a bug

**Problem**: After the 3rd delve ends, `Consider: None` appears in
gray.  Combined with the terse "Game over!" message, the ending feels
abrupt and the "None" looks like missing data.

**Proposal**: Skip printing the `Consider:` line (or print
`Consider: (game over)`) when stop is true.  Enhance the game-over
message with a brief summary:
```
Game over!  Final score: 12
  Experience: 8    Treasure: 4 (sword, portal, scale)
  Delve 1: retired at depth 5
  Delve 2: retired at depth 3
  Delve 3: retreated at depth 4
```

---

### 13. `retreat(+0 XP)` is noise when it's the only option

**Problem**: When retreat is the only available action, showing
`retreat(+0 XP)` adds no information.

**Proposal**: Suppress the `(+0 XP)` annotation when the delta is
zero: only annotate retire/retreat when the delta is non-zero.
Change `display.py:64`:
```python
f"{c}({deltas[c]:+d} XP)" if deltas and c in deltas and deltas[c] else c
```
This keeps `retire(+5 XP)` but simplifies `retreat` (no annotation).

---

### 14. `descend` means two different things

**Problem**: At delve start, `descend` means "enter the dungeon."
Mid-delve, it means "go deeper."  The `help descend` text only
describes the latter.

**Proposal**: This is minor and probably not worth changing the
command name.  But the help text could acknowledge both uses:
"Descend to the next depth, or enter the dungeon at the start
of a delve."

---

## Priority Ranking

| # | Issue | Severity | Effort |
|---|-------|----------|--------|
| 1 | "+N XP" is net score, not XP | High | Low |
| 8 | Silent hero level-up | High | Low |
| 9 | Cryptic "additional target" error | Medium | Low |
| 10| Cryptic "2 heroes required" error | Medium | Low |
| 4 | Chests/potions uncolored | Medium | Low |
| 12| `Consider: None` at game end | Medium | Low |
| 2 | Undocumented colors | Medium | Low |
| 6 | Consider line omits party commands | Medium | Medium |
| 13| `retreat(+0 XP)` noise | Low | Low |
| 7 | Cryptic tilde notation | Low | Low |
| 5 | Score vs XP confusion | Low | Medium |
| 3 | Party dims when idle | Low | Low |
| 11| Variable alignment | Low | Low |
| 14| Dual-meaning descend | Low | Low |
