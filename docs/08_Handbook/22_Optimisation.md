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
- [Architecture §4 (optimisation component)](../03_Architecture/Architecture.md)
- [Chapter 21 — Analytics](./21_Analytics.md)
- Code: `src/analytics/optimizer.py`
