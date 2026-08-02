# Chapter 22 — Optimisation (Linear Programming)

**Badges:** 📖 🧪 💻

---

## Purpose

Optimisation means finding the *best* choice out of a huge number of options, subject
to rules. In this project it's the squad selector: pick the 11 players that score the
most points within a budget, a formation, and the max-3-per-club rule.

---

## Why We Use It — and where it sits in the architecture

Every earlier metric *ranked* or *described* players. The optimiser **chooses a set** —
the first feature that makes a *decision*. It lives in the analytics layer
(`src/analytics/optimizer.py`) and reads player data from storage; it's the one module
with an external dependency (**PuLP**), sealed away from everything else.

The mindset is different from normal code:

```
Imperative (everywhere else):  do step 1, then 2, then 3 → an answer
Declarative (optimisation):    state the GOAL + the RULES → the solver finds the answer
```

You describe *what* a good squad is; the solver works out *which* one.

---

## Concepts

- **Linear Programming (LP):** maximise/minimise a linear objective subject to linear
  constraints.
- **Integer Programming (ILP):** LP where variables must be whole numbers — here each
  player is a **binary** decision: picked (1) or not (0).
- **Objective:** the thing we maximise — total points.
- **Constraint:** a rule the answer must obey — budget, position counts, club cap.
- **Solver:** the engine (PuLP's CBC) that searches all legal combinations for the best.
- **Infeasible:** no answer satisfies the constraints (e.g. budget too low).

---

## The formulation (from ADR-008)

```
decision:  pick[p] ∈ {0, 1}   for each player p
maximise:  Σ total_points[p] · pick[p]
subject to Σ price[p] · pick[p] ≤ budget          (£80M default)
           1 GK, 4 DEF, 4 MID, 2 FWD              (= 11)
           ≤ 3 players per club
```

The code (`optimizer.py`) mirrors this almost line-for-line — one objective line, one
line per constraint family.

---

## Why not just be greedy? (the key lesson)

Picking the highest-points player for each slot **doesn't** give the best squad,
because the *budget* makes the combination matter. Worked example — 2 forwards, £15M:

| FWD | Points | Price |
|---|---|---|
| A | 10 | £10M |
| B | 9 | £9M |
| C | 8 | £6M |

Greedy grabs A (£10M), then can't afford a 2nd forward → stuck at 10 points. The solver
finds **B + C = £15M, 17 points**. That's why "optimal" needs a solver, not a shortcut.

---

## Forcing choices (include / exclude)

The user can force players **in** (favourites) or **out** (dislikes). In an integer
program these are the simplest constraints — fix the variable:

```python
for pid in include_ids:  problem += pick[pid] == 1   # must be in the XI
for pid in exclude_ids:  problem += pick[pid] == 0   # can't be in the XI
```

The solver then builds the best legal XI around them — and *validates the choices for
free*: forcing two goalkeepers, or players that bust the budget, simply comes back
**Infeasible**. The only extra code we wrote was **name resolution** — turning typed
names into ids — because `web_name` isn't unique (14 shared names, so `--include
Wilson` is ambiguous and needs `Wilson:NFO`). That's input validation at the edge:
resolve first (fail early with a clear message), then optimise.

---

## Choosing the objective (points / value / xp)

The objective — the thing being maximised — is **pluggable**. The optimiser maximises a
per-player *score* it's handed; it doesn't know or care what that score means:

```python
problem += pulp.lpSum(scores[p["id"]] * pick[p["id"]] for p in players)
```

`objective_scores()` computes the score for the chosen metric — `points`
(total_points), `value` (points-per-£m), or `xp` (Expected Points, reusing
`player_xp`). So the value and xP analytics *become* what the optimiser chases:

```
squad --objective points  → maximise last-season points   (default)
squad --objective value   → maximise points-per-£m         (leaves budget unspent)
squad --objective xp       → maximise expected points       (fixtures-aware)
```

The lesson: keep the solver a generic "maximise these scores"; decide *what the scores
are* outside it. Adding a 4th objective is then a new dict entry, not a solver change.

---

## The full 15-man squad (`--full`) — a new *caller*, not a new algorithm (ADR-012)

Real FPL isn't 11 players — it's the **15 you own**: 2 GK, 5 DEF, 5 MID, 3 FWD, ≤ £100M,
≤ 3 per club. The important lesson is how *little* had to change: `select_squad` already
takes `formation` and `budget` as **parameters**, so the full squad is just a different
set of arguments:

```
squad        → formation {GK:1, DEF:4, MID:4, FWD:2},  £80M    (the XI)
squad --full → formation {GK:2, DEF:5, MID:5, FWD:3},  £100M   (the 15)
```

No new objective, no new constraints, no new solver code — the generic core built in
ADR-008 paid off. This is the recurring project pattern: *add capability at the edge,
leave the core untouched.*

### The bench is the manager's job — and why

The model scores **all 15 equally**, so on its own `--full` spends nearly the whole
£100M on 15 strong players and leaves **no cheap bench**. That's deliberate: the manager
picks the bench, using the `--include` mechanism already built:

```
squad --full --include <cheap GK> <cheap DEF> <cheap MID> <cheap FWD>
```

Those four slots lock cheap, and the solver pours the rest into the best 11. Human
judgement (which cheap fodder is worth owning) stays with the human; the solver does the
optimising. A richer *two-tier* model — where the solver itself picks the bench by
scoring only a chosen XI — was considered and **rejected** for simplicity (ADR-012).

### An honest caveat about the number

For the XI, the points total is a fair guide to weekly return. For the **15**, the total
**counts bench players who won't actually score**, so it's a *squad-strength* proxy, not
a weekly total. The `--full` output says so plainly rather than letting the figure
mislead — a small but important piece of intellectual honesty.

---

## Declaring the bench (`--bench`) — annotation, and an honest number (ADR-013)

`--full` alone doesn't *know* which four are your bench. `--bench` lets the manager
**declare** it — name 1–4 players and they're marked `**` and sorted to the bottom:

```
squad --full --bench Dubravka Diop     # (--bench on its own also turns --full on)
```

The lesson is the same one a third time: **a benched player is forced in exactly like
`--include`** (`pick == 1`) — the *only* new work is a **tag** on the result, a **`**`
marker**, and **sorting the bench to the end**. Annotation and display, not optimisation.

### Why this makes the number honest

Because the manager declares the bench, we now know the *starters* — so the output shows
a **starters' points subtotal** next to the squad total:

```
Total: £100.0m · 2464 pts
Starters (13): 2337 pts
```

That directly answers the ADR-012 caveat: the squad total counts a non-scoring bench, but
the starters' subtotal doesn't. When you bench a full four, "Starters (11)" *is* your XI's
points — a fair weekly guide. Below four, it's labelled by count so it never oversells
itself. The visibility Tony wanted and the honesty problem turned out to be one fix.

### `--include` vs `--bench`

Both force a player into the squad. `--include` means "own this player" (starter or
bench — we can't tell). `--bench` means "own this player *and* sit them" — a clearer
intent that earns the `**` marker, the bottom of the list, and the honest subtotal.

---

## Common Mistakes

- **Assuming greedy = optimal.** It isn't, once a budget couples the choices.
- **Not handling infeasible.** Check the solver's status before reading a result.
- **Letting the dependency spread.** Keep PuLP inside the optimiser module.

---

## Best Practices

- Pressure-test the formulation with a small worked example before trusting it.
- Return the solver `status` so callers can report "no legal squad" clearly.
- Keep the objective swappable (points now; xP later) — a backlog item.

---

## Lessons Learned

- Optimisation flips the usual mindset: you write the *rules*, not the *search*.
- A one-line constraint (`≤ 3 per club`) can change the whole answer — the value is in
  stating the rules precisely.

---

## Related Documents

- [ADR-008 — Squad selector (ILP)](../06_Decisions/ADR-008-squad-selector.md)
- [ADR-012 — The full 15-man squad](../06_Decisions/ADR-012-full-squad.md)
- [ADR-013 — A declared bench](../06_Decisions/ADR-013-declared-bench.md)
- [Architecture §4 (optimisation component)](../03_Architecture/Architecture.md)
- [Chapter 21 — Analytics](./21_Analytics.md)
- Code: `src/analytics/optimizer.py`
