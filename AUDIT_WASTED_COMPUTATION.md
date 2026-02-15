# Audit: Wasted Computation

## Category 1: `replace` wrapping `replace` — throwaway intermediate objects

The codebase uses frozen dataclasses throughout, which means every mutation
creates a new object.  Several call sites create an intermediate `World` (or
other dataclass) via one `replace`, then immediately wrap it in *another*
`replace`, discarding the intermediate.

### 1a. `replace(replace_treasure(...), ...)`

`replace_treasure` itself returns `replace(world, treasure=..., reserve=...)`.
Callers that immediately `replace` the result throw away the intermediate
`World`:

| Location | Code |
|---|---|
| `action.py:423‑426` | `replace(replace_treasure(world, noun), party=increment_party(...))` |
| `world.py:252‑253` | `world = replace_treasure(world, noun)` then `replace(world, dungeon=replace(world.dungeon, dragon=0))` |
| `world.py:265` | `replace(replace_treasure(world, "portal"), dungeon=struct.Dungeon())` |

**Fix pattern:** Have `replace_treasure` accept optional extra keyword
overrides so its internal `replace` can fold additional fields in one shot.
Or extract the raw treasure/reserve pair and build a single `replace`.

### 1b. `replace(draw_treasure(...), ...)`

`draw_treasure` also returns `replace(world, treasure=..., reserve=...)`.
Same intermediate‑discard issue:

| Location | Code |
|---|---|
| `action.py:149‑154` (`open_one`) | `replace(draw_treasure(world, randrange), dungeon=..., party=..., regroup=...)` |
| `action.py:372‑378` (`defeat_dragon`) | `replace(draw_treasure(world, randrange), experience=..., party=..., dungeon=..., regroup=...)` |

### 1c. Double `replace` on `world` in `player.apply`

`player.py:129‑140` builds a new `world` with treasure‑augmented party, then
`player.py:161‑172` builds *another* `world` reversing the augmentation.
Each call site is `replace(world, party=replace(world.party, ...))` — so we
get `replace` inside `replace`, creating a throwaway `Party` and `World`
on each side of the action.

### 1d. Loop body in `player.apply` treasure consumption

`player.py:179‑182`:
```python
world = replace_treasure(world, getattr(player.artifacts, hero))
world = replace(world, party=replace(world.party, **{hero: 0}))
```
Two consecutive `replace(world, ...)` calls per negative‑hero iteration;
each creates an intermediate `World`.

---

## Category 2: Materializing lists when generators (or direct computation) would suffice

### 2a. `_draw` builds a full expanded list to pick one element

`world.py:209‑215`:
```python
items = [
    name
    for name, count in struct.field_items(reserve)
    for _ in range(count)
]
return items[randrange(0, len(items))]
```
The reserve starts with 36 items total.  Every treasure draw builds a 36‑element
list of repeated strings, indexes into it once, and throws the list away.

**Fix:** Use the counts directly as weights:
```python
names, weights = zip(*((n, c) for n, c in struct.field_items(reserve) if c))
cumulative = list(itertools.accumulate(weights))
i = bisect.bisect_left(cumulative, randrange(0, cumulative[-1]) + 1)
return names[i]
```
Or if `random.choices` is acceptable, `choices(names, weights=weights)[0]`.

### 2b. `tuple(map(...))` unpacked immediately

`action.py:228‑236`:
```python
struct.Dungeon(
    *tuple(
        map(
            operator.add,
            struct.field_values(reduced),
            struct.field_values(increased),
        )
    )
)
```
`tuple(...)` creates an intermediate tuple just to unpack it with `*`.
`struct.Dungeon(*map(...))` works directly — `*` accepts any iterable.

### 2c. `list(sorted(...))` is redundant

`action.py:316`:
```python
interchangeable = list(sorted(_interchangeable))
```
`sorted()` already returns a `list`.  Wrapping in `list()` creates a copy
for no reason.

---

## Category 3: Repeated set construction

### 3a. `{*heroes}` computed twice in `defeat_dragon_heroes`

`action.py:251,259`:
```python
if {*heroes} & {*_disallowed_heroes}:   # builds {*heroes}
    ...
if len({*heroes}) != _distinct_heroes:  # builds {*heroes} again
    ...
```
A local variable `hero_set = {*heroes}` would avoid the second construction.

### 3b. Same pattern in `defeat_dragon_heroes_interchangeable`

`action.py:305`:
```python
if {*heroes} & {*_disallowed_heroes}:
```
`_disallowed_heroes` is always `("scroll",)`.  `{*("scroll",)}` constructs a
set each call; this could be a `frozenset` default parameter.

---

## Category 4: Sequential single‑element mutations on frozen dataclasses

When two or more increments/decrements are known at call time, calling them
one‑by‑one creates throwaway intermediate objects.

### 4a. Chieftain ability — two goblin decrements, two thief increments

`halfgoblin.py:65‑69`:
```python
dungeon = action.decrement_dungeon(dungeon, "goblin")
dungeon = action.decrement_dungeon(dungeon, "goblin")   # intermediate discarded
party = action.increment_party(party, "thief")
party = action.increment_party(party, "thief")           # intermediate discarded
```
Each call validates, does `getattr`, and calls `replace`.  A batch
`replace(dungeon, goblin=dungeon.goblin - 2)` would be one object, not two.

### 4b. Necromancer ability — same pattern with skeletons/fighters

`occultist.py:64‑67`: identical structure.

### 4c. `reroll` loop of `decrement_dungeon`

`action.py:218‑222`:
```python
reduced = world.dungeon
for target in targets:
    reduced = decrement_dungeon(reduced, target)
```
Creates one intermediate `Dungeon` per target.  A `Counter`‑based batch
would build one:
```python
counts = Counter(targets)
reduced = replace(dungeon, **{t: getattr(dungeon, t) - n for t, n in counts.items()})
```

---

## Category 5: Trial execution for tab‑completion feasibility

### 5a. `game.py:139‑155` — `completenames` runs full game actions

```python
try:
    world.descend(self._world, self._player.roll.dungeon, _dummy_randrange)
    possible.append("descend")
except error.DrollError:
    pass
```
Three full game‑state transformations (`descend`, `retire`, `retreat`) are
executed — each creating multiple intermediate `World`/`Dungeon`/`Party`
objects — solely to determine whether the command is *feasible*.  Lightweight
predicate functions (e.g. `can_descend(world) -> bool`) would avoid all
that object construction.

### 5b. `_available_commands` round‑trips through `get_names`

`shell.py:63‑78` calls `self.get_names()`, which calls
`self._game.completenames(text="", head=[], tail=[])`, which runs the trial
executions above.  Then `_available_commands` iterates the result, strips the
`"do_"` prefix it just added, and filters to a hardcoded set.  The `"do_"` +
`"help_"` prefix construction in `get_names` is pure overhead for this caller.

---

## Category 6: Redundant guards and trivially dead code

### 6a. `min(0, quantity)` when `quantity` is known negative

`player.py:177‑178`:
```python
if quantity >= 0:
    continue
for _ in range(-min(0, quantity)):
```
Since we only reach line 178 when `quantity < 0`, `min(0, quantity)` is
always `quantity`.  The call collapses to `range(-quantity)`.

### 6b. `getattr(discard, "thief", 0)` with a default that cannot trigger

`halfgoblin.py:35,69,73` / `occultist.py:34,68,72`:
```python
discard = replace(discard, thief=getattr(discard, "thief", 0) + 1)
```
`discard` is a `Party`, which always defines `thief` (default `0`).  The
third argument to `getattr` is dead code.  `discard.thief` is sufficient
and avoids the dynamic lookup.

---

## Category 7: `exhausted_dungeon` sums then subtracts

`world.py:37`:
```python
0 == sum(struct.field_values(dungeon)) - dungeon.dragon
```
This sums *all* six fields (including `dragon`), then subtracts `dragon` back
out.  It performs 6 additions + 1 subtraction.  Summing only the 5 non‑dragon
fields directly (`goblin + skeleton + ooze + chest + potion`) avoids the
unnecessary addition and subtraction of dragon.

---

## Category 8: `_partify` linear scan per token

`player.py:187‑194`:
```python
def _partify(token, artifacts):
    if token is None:
        return None
    for party, artifact in struct.field_items(artifacts):
        if token == artifact:
            return party
    return token
```
Called for `noun`, `target`, and each element of `additional`.  Each call
iterates up to 6 `(party, artifact)` pairs.  A pre‑built reverse‑lookup
`dict` (artifact→party) would make each lookup O(1).

---

## Summary by impact

| Category | Pattern | Occurrences | Relative cost |
|---|---|---|---|
| 1 | `replace(replace(...))` throwaway intermediates | ~10 | Medium — extra frozen‑dataclass allocation per game action |
| 2 | Materializing lists unnecessarily | 3 | `_draw` is Medium (36‑element list per treasure draw); others Low |
| 3 | Repeated set construction | 3 | Low |
| 4 | Sequential single‑element mutations | 4 | Medium — 2× the dataclass allocations needed |
| 5 | Trial execution for completion | 2 | High — full game‑state transformations on every tab‑press |
| 6 | Redundant guards / dead defaults | 6 | Low |
| 7 | Sum‑then‑subtract instead of direct sum | 1 | Low |
| 8 | Linear scan instead of dict lookup | 1 per token | Low |
