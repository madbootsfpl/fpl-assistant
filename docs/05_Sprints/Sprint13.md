# Sprint 013: Flexible Formations

**Dates:** 2026-08-02
**Status:** ✅ Complete
**Capacity:** ~2 working sessions (a constraint + display extension of the optimiser)
**Carried Over:** None (Sprint 012 closed clean)

---

### 🔎 Verified at planning (per the standing lesson)

Ran the actual comparison before planning — the best XI in **every** legal formation at
£80m (by solving each fixed shape):

| Formation | Best XI pts |
|---|---|
| **5-4-1** | **2043** ← best flexible |
| 4-5-1 | 2036 |
| 5-3-2 | 2035 |
| **4-4-2** | **2024** ← today's fixed default |
| 3-5-2 | 2009 |
| 4-3-3 | 2007 |
| 5-2-3 | 2005 |
| 3-4-3 | 2004 |

**The fixed 1-4-4-2 leaves 19 points on the table** (2043 − 2024). This both proves the
feature's value and confirms the legal ranges (GK 1; DEF 3–5; MID 2–5; FWD 1–3; outfield
10). Positions are ample (GK 62 · DEF 185 · MID 249 · FWD 68). **No new data or
dependency.** Still blocked (preseason): `form`, attack/defence strengths.

This sprint is Tony's Sprint 012 backlog pick — deferred from Sprint 011, now due.

---

### 🧭 Architecturally, what's new — constraints as *ranges*, policy at the edge

Today the optimiser forces an **exact** shape: `formation = {GK:1, DEF:4, MID:4, FWD:2}`,
each an equality. A *flexible* formation replaces the outfield equalities with **ranges**
plus a total:

```
GK  == 1
DEF in 3..5        MID in 2..5        FWD in 1..3
total == 11        → the solver picks the best legal shape
```

The design keeps the recurring pattern — **generic core, policy at the edge**:

- **`select_squad` learns ranges.** A formation value may be an exact int *or* a
  `(min, max)` tuple; a `size` says how many players in total. Exact ints still mean
  `== n`, so **the default and every existing caller are unchanged** — backward compatible.
- **The CLI decides the policy.** Plain `squad` now passes a *flexible* XI spec
  (`XI_FLEX`); `--formation 3-5-2` passes a *pinned* exact spec; `--full` still passes the
  exact 15-man shape. So "flexible is the new XI default" is a one-line decision in the
  handler, not a change to the solver.

Formations apply to the **starting XI** only — the 15-man squad has a fixed 2/5/5/3 shape,
so `--formation` with `--full` is rejected. The chosen shape is shown in the output
(e.g. "Optimal XI (5-4-1)").

#### The bench *is* the formation (connecting Sprint 012)

In the full squad the shape isn't chosen with `--formation` — it's **implied by the
bench**. You start 1 GK + 10 outfield, so your 4 bench are the backup GK + 3 outfield, and
whichever 3 you sit set the XI:

```
XI = (5 − benched DEF, 5 − benched MID, 3 − benched FWD)
bench 1 DEF, 1 MID, 1 FWD → 4-4-2     bench 0 DEF, 2 MID, 1 FWD → 5-3-2
```

So this sprint also makes that link **visible**: when a full 4-man bench is declared,
`--full` shows the implied shape — `Starters (11) — 4-4-2`. (Below a 4-man bench there's
no complete XI, so no formation is shown — the existing by-count label stands.) That's why
`--formation` and `--full` don't mix: in the full squad the bench already sets the shape.

---

### 🎯 Sprint Goal

**Objective:** Let `squad` pick the **best legal formation** instead of a fixed 1-4-4-2
(GK 1; DEF 3–5; MID 2–5; FWD 1–3; 11 total), with an optional `--formation D-M-F` to pin
a shape — and make the shape **visible** everywhere: the chosen XI shape, and (connecting
Sprint 012) the shape your declared bench implies in `--full`. Composes with objective,
budget, and include/exclude as before.

#### Success Criteria
- [x] Flexible-formation approach agreed (**ADR-014**) before feature code
- [x] `select_squad` accepts range formations (`(min,max)`) + a `size`; exact ints
      still mean `== n` (existing callers/tests unchanged)
- [x] Plain `squad` picks the **best legal formation** (the 5-4-1 above appears)
- [x] `squad --formation 3-5-2` pins the shape; bad input → clear error, no crash
- [x] `--formation` with `--full` is rejected with a clear message (XI-only)
- [x] The output **states the chosen formation** (e.g. "Optimal XI (5-4-1)")
- [x] In `--full` with a **4-man bench**, the output shows the **bench-implied** shape
      (e.g. "Starters (11) — 4-4-2"); below 4 benched, no shape (the by-count label stands)
- [x] `--formation 4-4-2` reproduces today's fixed-XI result (regression anchor)
- [x] Composes with `--objective`, `--budget`, `--include`, `--exclude`
- [x] Tests cover ranges, the pin, the parser/validation, and the `--full` rejection
- [x] **Manual smoke test** run before the sprint is closed (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-042 | Agree the flexible-formation design (**ADR-014**): ranges + `size` in `select_squad`; `XI_FLEX` default at the CLI; `--formation D-M-F` parse/validate; XI-only (reject with `--full`); legal ranges; show the chosen shape — pressure-test with a worked example | Critical | ✅ Complete | 0.5 session |
| US-043 | Implement flexible formations: `select_squad` range/`size` support; CLI passes `XI_FLEX` by default + parses/validates `--formation`; `render_squad` states the shape — both the chosen XI shape *and* the bench-implied shape in `--full` (shared `formation_str` helper). Tests + smoke test | High | ✅ Complete | 1–1.5 session |

#### Technical Tasks & Maintenance
- [ ] ADR-014 recorded + added to the ADR index — _US-042_
- [ ] Update Architecture doc (range-constraint note + changelog) — _US-042_
- [ ] Update `README.md` + `--help` with `--formation` + the flexible default — _US-043_
- [ ] Handbook Ch 22 (Optimisation) — add the flexible-formation section — _US-043_
- [ ] Tidy `docs/Backlog.md` (flexible formations done; drop the stale done items) — _US-043_

---

### ✅ Definition of Done (this sprint)

The same 3-part DoD that has held for twelve sprints — a story isn't done until:
1. **Automated tests pass** (and cover the new logic).
2. **Manual smoke test done** — run the real command, eyeball the output, check `--help`.
3. **Documentation updated & checked** — Handbook, Architecture, ADR + index, README,
   sprint board + PROJECT_STATUS, as applicable (Charter Documentation Rules).

A "smoke test" + "docs touched" note goes in the session log for each feature story.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Flexible XI (DEF 3–5, MID 2–5, FWD 1–3, 11) | Formations for the 15-man squad (fixed 2/5/5/3) |
| Optional `--formation D-M-F` pin | Picking a formation *per gameweek* / auto-subs |
| Show the chosen shape (XI) + bench-implied shape (`--full`) | Validating the bench yields a *legal* XI (later) |
| Composes with objective/budget/include/exclude | A solver-chosen XI *within* `--full` (rejected two-tier) |

**External Dependencies:**
- [ ] Existing players data + PuLP; no new data or dependency (verified above)

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Plain `squad` output changes (flexible ≠ 4-4-2) | Med | **Intended improvement** (+19 pts here); `--formation 4-4-2` reproduces the old result — a regression test pins it |
| Range support could disturb existing callers | Med | `select_squad` default stays exact 1-4-4-2; exact ints still mean `== n`; the CLI opts into flexibility — existing optimiser tests unchanged |
| Bad `--formation` string (e.g. `6-3-1`, `foo`) | Low | Parse + validate (3 ints; DEF/MID/FWD in range; sum 10) → clear error, no solve |
| `--formation` misused with `--full` | Low | Rejected up front with a clear message (XI-only) |
| A "size required" gap for range formations | Low | `size` defaults derive from exact shapes; the CLI passes `size=11` for the flexible XI explicitly |

---

### 🗝️ Gating decision (US-042 → ADR-014)

Settle before building — **pressure-test with a worked example** (per the standing
lesson). Proposed answers (Tony to confirm/redirect):

1. **Ranges + size.** A formation value is an exact int (`== n`) or a `(min, max)` tuple
   (`min ≤ Σ ≤ max`); `size` fixes the total (`Σ all == size`). `select_squad` normalises
   ints to `(n, n)`, so exact formations behave exactly as today.
2. **Legal XI ranges.** GK 1; DEF 3–5; MID 2–5; FWD 1–3; total 11 — `XI_FLEX`, size 11.
3. **Policy at the edge.** The CLI passes `XI_FLEX` for plain `squad`, a pinned exact
   spec for `--formation`, and the exact `SQUAD_15` for `--full`. `select_squad`'s default
   stays the exact 1-4-4-2 (so direct callers/tests don't change).
4. **`--formation D-M-F`.** Parse three ints (DEF-MID-FWD, GK implicit); validate each in
   range and sum = 10; else a clear error. Pins to an exact spec.
5. **XI-only.** `--formation` with `--full` is an error — in the full squad the **bench**
   sets the shape, so specifying it twice would conflict.
6. **Display.** A shared `formation_str(players)` (count DEF-MID-FWD) drives both: the XI
   output states its chosen shape ("Optimal XI (5-4-1)"); `--full` with a full 4-man bench
   states the **bench-implied** shape ("Starters (11) — 4-4-2"). A legal XI needs the bench
   to be the backup GK + 3 outfield; below that, no shape is shown (by-count label stands).
   *Validating* an illegal bench is deferred (out of scope) — for now we display, not police.

**Worked example to verify at the gate:** on real data, plain `squad` should now return
the **5-4-1** (2043 pts) rather than 4-4-2 (2024) — the +19 the fixed shape was leaving
behind — while `squad --formation 4-4-2` reproduces the old 2024 XI exactly. Confirms both
the flexible default and the regression anchor *before* code.

---

### 📝 Session Progress Log

#### Session 1 — 2026-08-02 (US-042: ADR-014 — the flexible-formation design)
* **Completed:** Recorded **ADR-014**: `select_squad` gains range (`(min,max)`) + `size`
  support with exact ints normalised to `(n,n)` (default and existing callers unchanged);
  the CLI opts into the flexible XI (`XI_FLEX`: GK 1/DEF 3–5/MID 2–5/FWD 1–3, size 11),
  parses/validates `--formation D-M-F`, and rejects it with `--full`. A shared
  `formation_str(players)` shows both the chosen XI shape and the bench-implied shape in
  `--full` (connecting ADR-013). **Pressure-tested on real data before writing:** best
  flexible **5-4-1 = 2043** vs fixed **4-4-2 = 2024** (+19); and a 1/1/1/1 declared bench
  → `formation_str` reads **4-4-2** over the 11 starters. Added to the ADR index;
  Architecture §12 changelog note. US-042 **complete** — no feature code.
* **Manual smoke test:** N/A (docs-only gate story). The two worked examples *are* the
  verification — run live against `data/fpl.db`.
* **Docs touched:** ADR-014 (new) + index, Architecture changelog, Sprint13 board.
* **Issues / Blockers:** None. (Data verified; the +19 and the bench-implied shape proven.)
* **Next Steps:** US-043 — `select_squad` ranges/`size` + CLI `--formation` + `render_squad`
  shapes.

#### Session 2 — 2026-08-02 (US-043: flexible formations)
* **Completed:** `squad` now picks the best legal formation. `select_squad` gained
  `size` + a `_formation_bounds` helper (int → `(n,n)`, tuple → range; range without
  `size` raises); the exact-count loop became range constraints + `total == size`. The
  **default and all existing callers are unchanged** (exact ints still mean `== n`). CLI:
  `XI_FLEX` is the XI default; a pure `parse_formation()` validates `--formation D-M-F`
  (3 ints, in-range, sum 10); `--formation` with `--full`/`--bench` is rejected (the bench
  sets the shape). `render_squad` shows the shape via a shared `formation_str()` — the
  chosen XI ("Optimal XI (5-4-1)") and the bench-implied XI ("Starters (11) — 4-4-2").
  **+11 tests → 145 total, all green.** US-043 **complete**.
* **Manual smoke test:** ✅ `squad` → 5-4-1 / 2043; `--formation 4-4-2` → the old 2024
  (regression holds); `--formation 3-5-2` → pinned; `--formation 6-3-1` and `foo` → clear
  errors; `--formation 3-5-2 --full` → rejected; `--full --bench <4>` → "Starters (11) —
  4-4-2"; `--help` shows `--formation`.
* **Docs touched:** Handbook Ch20 + Ch22, README, Backlog (tidied — done items + new
  follow-ons), Sprint13 board, PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** Sprint 013 review & retrospective.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** Both stories — US-042 (ADR-014) and US-043 (`squad --formation` + the
  flexible default). `squad` now finds the best legal formation (a measured **+19 pts**),
  a pin is available, and the bench-implied shape is shown in `--full` — connecting the
  bench (Sprint 012) to the formation. Tests grew 134 → **145**. No optimiser *model*
  rewrite, no new dependency.
* **Carried Forward:** None. Backlog: validate a bench yields a legal XI, bench order, a
  saved squad, FBref xG/xA, plus season-dependent FPL work.
* **Key Artifacts / Decisions:** ADR-014 (ranges + `size`; policy at the edge; XI-only
  `--formation`; bench↔formation); `_formation_bounds`; `XI_FLEX`; `parse_formation`;
  shared `formation_str`.

#### Retrospective
* **What Went Well?**
  - **A load-bearing constraint changed for almost nothing.** Turning the formation
    equalities into ranges was `int → (n,n)` + one `total == size` line; everything else
    was policy at the CLI edge. The generic core held a fourth straight sprint.
  - **Tony's question shaped the design.** "Does the bench set the formation?" turned two
    parallel features into one connected idea — a single `formation_str` shows both the
    chosen XI shape and the bench-implied shape.
  - **Value was measured, not assumed.** The planning check proved +19 pts (5-4-1 vs
    4-4-2) *before* any code — the standing lesson at its best.
  - Backward-compat was explicit (default unchanged; a `4-4-2` regression anchor); the
    3-part DoD held (13th sprint).
* **What Could Be Improved?**
  - The bench-implied shape is *shown* but not *validated* — an illegal declared bench
    (e.g. all three forwards) isn't flagged yet (captured as a backlog follow-on).
  - The `squad` command now carries six options; still coherent, but the surface is wide
    enough that a future grouping/tidy could help.
* **Lessons Learned?**
  - Model variability as data (a range), not as new code paths — the solver already knew
    how to handle it.
  - A default that reproduces old behaviour (exact `int` → `== n`) makes a risky change
    safe — the same no-op-default lesson as ADR-011.
  - Answering "how do two features interact?" often reveals they're one idea in two views.
* **Action Items for Next Sprint (014):**
  - [ ] Consider: validating a legal bench, bench order, a saved squad, FBref xG/xA, or
    season-dependent FPL work once it starts — check data first, as always.
  - [ ] Keep pressure-testing ADR mechanisms + the 3-part DoD.

---

**Proposed follow-on (Sprint 014):** validate a declared bench yields a legal XI, bench
order, a saved/persistent squad, FBref xG/xA (spike-first), or data-dependent FPL work
once the season starts.

**Completion Date:** 2026-08-02
**Final Notes:** `squad` picks its shape now — a measured +19 pts — and the bench and the
formation are one idea, thanks to Tony's question. Sprint outcome: **Successful** — 2/2
stories, zero roll-over, DoD held.
