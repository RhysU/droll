# Droll Beta Tester Review

Findings from playing 100+ automated games across all 8 heroes, plus targeted
manual sessions testing error messages, edge cases, and color output.

## Key Findings

### Critical: `retreat()` silently consumes portals (world.py:160-176)

The `retreat()` function auto-consumes a portal to earn depth XP.  The README
says "retreat but earn nothing" -- this is incorrect when you have a portal.
The player's 2-point treasure disappears without explicit warning.

Both `retire` and `retreat` then show identical score deltas (e.g.,
`retire(+1 score) retreat(+1 score)`), offering a false choice since both
operations are functionally identical when a portal is involved.

### Critical: `help portal` and `help score` text are wrong

- `help portal` says "Retiring consumes a portal automatically" but retreat
  also consumes it.
- `help score` says "Retreating earns no experience" but retreat-with-portal
  does earn experience.

### Confusing: Score line formula is implicit

`Score 3: depth 1 in delve 2 with 1 XP plus 2 treasure` -- must deduce 1+2=3.

### Confusing: `help dragon` returns "No help on dragon"

Dragons are the game's central threat but have no help entry.

### Confusing: `ring` as a command is misleading

Typing `ring` says `To use a ring, directly "descend" or "retire".`  Unclear
that the ring is consumed automatically, not activated manually.

### Confusing: `~D` notation (e.g. `thief×2~1`) unexplained in-game

Only documented in the README, never explained to the player.

### Confusing: No hint that party members / treasures are commands

The `Consider:` line only shows meta-commands.  The README says "party members
and treasures are also valid commands" but nothing in-game tells you this.

### Confusing: `Consider: None` at game end

Shown after the final delve, looks like a bug.

### Grammar: "Exactly 1 heroes to revive required" (regular.py:149)

Should be "1 hero" not "1 heroes".

### Minor: `help scroll` shows all heroes' scroll behavior

Irrelevant information for the current hero.

### Minor: No "Level up!" message on hero advancement

### Minor: No score breakdown at game over

### Minor: `Party: None` looks like an error state

## Proposals

See inline proposals in the main analysis.  Priority order:

1. Fix retire/retreat portal display and help text
2. Explain score formula in the Score line
3. Add `help dragon`
4. Fix grammar in error messages
5. Add `~D` notation explanation
6. Hint that party/treasure are commands
7. Fix `Consider: None` at game end
8. Show score breakdown at game over
9. Filter `help scroll` by current hero
10. Add "Level up!" message
11. Use em-dash instead of "None" for empty states
12. Improve `ring` error message
