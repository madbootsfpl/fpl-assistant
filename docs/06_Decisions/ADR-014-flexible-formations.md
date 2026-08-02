# Architectural Decision Record: Flexible Formations

**Decision ID:** ADR-014
**Date:** 2026-08-02
**Status:** Accepted
**Superseded By / Replaces:** N/A (extends ADR-008; connects ADR-013)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The optimiser forces the starting XI into an **exact** 1-4-4-2. But the best XI within a
budget often isn't a 4-4-2. A planning check solved *every* legal formation at £80m and
found the fixed shape leaves **19 points** on the table (best 5-4-1 = 2043 vs 4-4-2 =
2024). This decision lets `squad` pick the best legal formation, with an optional pin.

It also answers a question Tony raised: in the **full squad**, the formation isn't chosen
with a flag — it's **implied by the bench** (ADR-013). This ADR makes that link visible.

**No new data or dependency** (verified: positions ample; the +19 measured on real data).

#### Decision Drivers
- **Value** — a measured +19 points from picking the shape instead of fixing it.
- **Backward compatibility** — existing callers/tests must not change.
- **Keep the core generic** — the solver executes constraints; policy lives at the edge.
- **Visibility** — show the shape, including the one the bench implies.

---

### 💡 Decisions

**1. Ranges + `size`.** A formation value is an exact int (`== n`) or a `(min, max)`
tuple (`min ≤ Σ ≤ max`); a `size` argument fixes the total (`Σ all == size`).
`select_squad` normalises ints to `(n, n)`, so **exact formations behave exactly as
today**. `size` defaults to the sum of an all-exact formation, so existing callers that
pass exact shapes need not pass `size`.

**2. Legal XI ranges.** GK 1; DEF 3–5; MID 2–5; FWD 1–3; total 11 — the constant
`XI_FLEX`, size 11.

**3. Policy at the edge.** `select_squad`'s default stays the exact 1-4-4-2, so direct
callers and tests are unchanged. The **CLI** decides the policy:
- plain `squad` → `XI_FLEX` (flexible), size 11;
- `squad --formation D-M-F` → a pinned exact spec, size 11;
- `squad --full` → the exact `SQUAD_15`, size 15 (unchanged).

"Flexible is the new XI default" is thus a one-line choice in the handler, not a solver
change.

**4. `--formation D-M-F`.** Parse three ints (DEF-MID-FWD; GK implicit); validate each in
its legal range and that they sum to 10; else a clear error, no solve. Pins to an exact
spec.

**5. XI-only.** `--formation` with `--full` is an error — in the full squad the **bench**
sets the shape, so specifying it twice would conflict.

**6. The bench implies the formation (connecting ADR-013).** You start 1 GK + 10
outfield, so the 4 bench are the backup GK + 3 outfield, and:

```
XI = (5 − benched DEF, 5 − benched MID, 3 − benched FWD)
```

A shared helper `formation_str(players)` (count DEF-MID-FWD) drives **both** displays: the
XI output states its chosen shape ("Optimal XI (5-4-1)"); `--full` with a **full 4-man
bench** states the bench-implied shape ("Starters (11) — 4-4-2"). Below a 4-man bench
there's no complete XI, so no shape is shown (the ADR-013 by-count label stands). We
**display** the implied shape; *validating* that a declared bench leaves a legal XI (e.g.
not sitting all three forwards) is deferred — display, don't police.

---

### 🧪 Worked examples (pressure-testing — run on real data)

**Flexible beats fixed.** Best XI in every legal formation at £80m:

```
5-4-1: 2043   4-5-1: 2036   5-3-2: 2035   4-4-2: 2024  ← today's fixed default
3-5-2: 2009   4-3-3: 2007   5-2-3: 2005   3-4-3: 2004
```

Plain `squad` should now return **5-4-1 (2043)**, +19 over the fixed 4-4-2; and
`squad --formation 4-4-2` should reproduce the old **2024** XI exactly (the regression
anchor).

**Bench implies the shape.** Reproducing the ADR-013 example — bench Dubravka + Diop +
Hughes + Kusi-Asare (1 GK, 1 DEF, 1 MID, 1 FWD) → `formation_str(starters)` returns
**4-4-2** over the 11 non-bench players. The same helper, both displays.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** `squad` finds a better XI (a measured +19); the shape is visible
  everywhere; the full-squad bench and the XI formation are unified as one concept; the
  solver stays a generic constraint executor.
* **Negative / Trade-offs:** Plain `squad` now returns a different (better-or-equal) XI
  than before — an intended change, not a regression. The bench-implied shape is shown but
  not validated (an illegal bench isn't flagged yet).
* **Risks & Mitigations:**
  - *Range support disturbs callers* → default stays exact 1-4-4-2; exact ints mean `== n`.
  - *Behaviour change* → `--formation 4-4-2` reproduces the old XI; a regression test pins it.
  - *Bad `--formation` string* → parse + validate, clear error, no solve.

---

### 🛠 Implementation & Migration
* **Components Affected:** optimiser (`select_squad` gains range/`size` support; default
  unchanged), CLI (`XI_FLEX` default, `--formation` parse/validate, XI-only guard),
  display (`formation_str`; XI shape + bench-implied shape), Docs.
* **Action Items:**
  - [x] Record the design + worked examples + the bench↔formation link (US-042)
  - [ ] `select_squad` ranges/`size` + CLI `--formation` + `render_squad` shapes (US-043)
  - [ ] (Backlog) validate a declared bench yields a *legal* XI; per-GW formation

---

### 🔄 Review & Reconsideration
* **Review Date:** If managers want an illegal bench flagged, or a per-gameweek shape.
* **Triggers for Reconsideration:**
  - [ ] Demand to *police* the bench's legality → add validation.
  - [ ] Want the solver to choose the XI within `--full` → revisit two-tier (ADR-012).

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-042 (this), US-043
- **External Docs:** [ADR-008 (squad selector)](./ADR-008-squad-selector.md) · [ADR-012 (full squad)](./ADR-012-full-squad.md) · [ADR-013 (declared bench)](./ADR-013-declared-bench.md) · [Sprint 013](../05_Sprints/Sprint13.md)
