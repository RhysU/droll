# README.md Audit

## Duplicated Information

### 1. Retire/retreat scoring explained twice

Lines 269-271 ("How to play"):
> After defeating any monsters, "retire" from the delve to earn experience
> equal to your depth.  If monsters remain and you cannot defeat them,
> instead "retreat" but earn nothing.

Lines 340-343 ("How does scoring work?"):
> Experience is earned by retiring from a delve.  When you retire, you gain
> experience equal to the depth you reached in the dungeon.  For example,
> retiring at depth 5 earns 5 experience points.  Retreating earns no
> experience.

**Recommendation:** Keep the brief version in "How to play" and remove the
restatement from "How does scoring work?" or, conversely, make "How to play"
step 4 say only "Retire or retreat to end a delve" and let the scoring section
carry the full explanation.  Either way, a single canonical location avoids the
reader wondering if the two descriptions differ in any subtle way.

### 2. Portal scoring stated twice

The treasure table already shows `portal | 2 | Town portal to escape the
dungeon`.  The prose immediately below repeats: "Town portals are worth 2
points each."

**Recommendation:** Drop the portal sentence from the prose paragraph.  The
table is authoritative; the repetition adds nothing.

### 3. Scale scoring stated twice

Similarly, the table says `scale | 1 | But a pair of scales scores 4` and the
prose restates "Scales score 1 point each, but every pair of scales scores 4
rather than 2, a +2 bonus per pair."

**Recommendation:** Fold the pair-bonus detail into the table's Notes column
(e.g., "1 each, but 4 per pair") and remove the prose duplication.

### 4. Knight ability described twice

The "Hero abilities" table says "Convert all monsters to dragons" and the
"Level-up progression" table repeats it nearly verbatim in the "New ability"
column for DragonSlayer.  Several other heroes are similar (Minstrel/Bard
"Discard all dragon dice" appears in both tables).

**Recommendation:** The level-up table's "New ability" column should describe
only what *changed* relative to the base ability.  For Knight/DragonSlayer the
ability is the same; the real upgrade is the party change (dragon needs only
2 heroes).  Clarify the column header or note "same as base" where applicable.

---

## Vague Content

### 5. "mechanical display format" is unexplained

The `--help` output (line 48) shows `--mechanical  Use mechanical display
format.` but nothing in the README explains what this means or when you would
want it.  The codebase shows it switches from a compact colored format to a
legacy plain-text format.

**Recommendation:** Add a one-sentence explanation after the `--help` block,
e.g., "The `--mechanical` flag disables color output and uses a fixed-field
format suitable for machine parsing or piping."

### 6. "tab completion" is mentioned but not demonstrated

Line 15: "A REPL providing the classic game, including tab completion to speed
playing."  A reader unfamiliar with the game doesn't know what gets completed
(commands? targets? both?).

**Recommendation:** Add a brief note: "Tab completion covers both commands
(e.g., `des<TAB>` expands to `descend`) and context-sensitive arguments (e.g.,
party member and monster names)."

### 7. "REPL" and "classic game" are jargon/ambiguous

"REPL" is programmer jargon that board-game players may not know.  "Classic
game" is ambiguous--does it mean the base game (excluding expansions) or simply
the well-known game?

**Recommendation:** Replace with: "An interactive command-line interface for
playing the base game (no expansions)."

### 8. Champion "defeats all three" relies on implicit context

The combat table's champion row says "all three" without naming them.

**Recommendation:** Write "goblin, skeleton, ooze" explicitly, as other rows
do, or add a footnote.

### 9. Scroll row is vague about potion quaffing

The combat table says scrolls "quaffs potions, rerolls dice" but does not
explain the quaffing mechanic.  The paragraph below only explains rerolling.

**Recommendation:** Add a sentence explaining how scrolls quaff potions:
"A scroll can also quaff a potion to revive a party member:
`scroll potion fighter` returns a fighter to your party."

### 10. "bypass a blocking dragon" is vague

Line 292: "A ring or portal can bypass a blocking dragon automatically."
Bypass how?  Does the dragon disappear?  Do you skip past it?

**Recommendation:** Clarify: "Using a ring removes your party from the
dragon's threat without fighting (the dragon dice remain).  Using a portal
immediately ends the delve, scoring your current depth as experience."

### 11. Level-up "Party change" column is cryptic

Several entries assume knowledge the reader doesn't have yet:

- "Fighter/Cleric interchangeable" -- does this mean either can fill the
  other's role?  Are they literally the same die?
- "Scrolls become offensive combatants" -- in what way?  What can they target?
- "Fighter defeats extra monster per use" -- extra beyond the normal one?
  Per use of what?
- "Champion defeats extra monster per use" -- same question.

**Recommendation:** Expand these into brief but concrete descriptions.  E.g.,
"Fighters and clerics each count as the other for all purposes (targeting,
specialization)" or "Each fighter use defeats one additional monster of any
type."

### 12. The undo command appears in the example but is never explained

The game session shows `undo` appearing as an available command (lines 99, 113,
119, etc.) but the README never describes what it does or its limitations.  The
code shows undo is blocked when a random-state change has occurred (e.g., after
opening a chest).

**Recommendation:** Add a brief note in "How to play": "You can `undo` the
most recent action unless it involved randomness (opening a chest, quaffing a
potion, etc.)."

### 13. The prompt number prefix is unexplained

The example shows `00 Knight>`, `01 Knight>`, etc.  The two-digit prefix is
the move counter, but this is never stated.

**Recommendation:** Add a sentence in "What does it look like?" or "How to
play" noting that the prompt shows the move number and current hero name.

### 14. `^D` exit is unexplained

The example session ends with `^D` (line 254) with no explanation.

**Recommendation:** Add: "Press Ctrl+D or type `quit` to exit at any time."

### 15. "Without Installation" is an awkward heading

**Recommendation:** Rename to "Quick Start" or "Running Without Installing."

---

## Structural Recommendations

### 16. The example session is very long (~220 lines)

The full game transcript from line 34 to 255 is valuable but overwhelming for
someone scanning the README.  It buries the gameplay rules that follow.

**Recommendation:** Shorten the inline example to ~30 lines showing one
descent, one combat, and one retire.  Offer the full session in a collapsible
`<details>` block or a separate file (e.g., `examples/sample-session.txt`).

### 17. Missing: Python version requirement

The codebase requires Python 3.9+ (per pyproject.toml), but the README does
not state this.

**Recommendation:** Add "Requires Python 3.9 or later" near the installation
instructions.

### 18. Missing: how to actually play a full game

The "How to play" section explains individual mechanics but never walks through
the overall flow: you pick a hero, play 3 delves, your total score is computed.
The relationship between delves and the game as a whole is stated only as "You
get 3 delves" without explaining that the game ends after 3 delves and the
final score is reported.

**Recommendation:** Add a brief overview paragraph: "A game consists of 3
delves.  After the third delve, your final score (experience + treasure) is
displayed.  The goal is to maximize your score across all three delves."

### 19. The CircleCI badge may be stale

Line 3 links to a CircleCI build badge.  If the project has moved CI systems
or the badge is no longer updating, it should be removed or updated.

**Recommendation:** Verify the badge still works; remove if not.

---

## Summary

| Category           | Count | Severity |
|--------------------|-------|----------|
| Duplicated content | 4     | Low      |
| Vague/unexplained  | 11    | Medium   |
| Structural issues  | 4     | Low      |

The README is **factually accurate**--all claims about heroes, combat,
treasure, and scoring match the source code.  The main opportunities are
eliminating redundancy, explaining implicit concepts (undo, mechanical mode,
prompt format), and restructuring the long example session so that the rules
are easier to find.
