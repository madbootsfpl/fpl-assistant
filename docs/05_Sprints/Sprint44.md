# Sprint 044: XI vs bench xP — a comparable squad-build breakout

**Dates:** 2026-08-05
**Status:** ✅ Complete (3/3 stories, retro done)
**Capacity:** ~2 working sessions (a gate + a display breakout across two surfaces)
**Carried Over:** None (Sprint 043 closed clean)

> **Direction (owner's Sprint-43 note):** *"When building a squad, break out the top-11 xP players vs the
> bench players' xP over the next 5 GW. This enables a good comparison across a few iterations of a team,
> so you can see the score differences."*

---

### 🔎 Verified at planning (the standing lesson)

- **The breakout works and is revealing.** Auto-deriving the best XI (via the existing `best_legal_xi`)
  and splitting xP:
  - unconstrained → **XI 233.6 · bench 72.2** (15-total 305.8);
  - `--differential 5` → **XI 233.5 · bench 68.2** (301.7) — differentials cost the **bench**, ~0 in the
    XI;
  - `--premium 3` → **XI 226.1 · bench 67.9** (294.0) — premiums cost real XI points.
  So the **XI xP** is the meaningful comparison number, and the 15-total *hides* where the cost lands
  (differentials looked 4× dearer than they are).
- **Pure reuse.** `best_legal_xi(selected, xp_by_id)` (ADR-041) gives the XI from the 15; the render
  already shows a bench split for a *declared* bench (ADR-013) — this extends it to an **auto-derived**
  best XI and adds an explicit **bench xP** line. No new analytics, no new dependency.
- **Save is untouched.** The auto-XI is **display-only** (passed to the renderer); it does not change the
  saved `bench_ids` (`--save`/`--load` behave as today).
- Still preseason (0 GWs); ClubElo up (intermittent).

---

### 🧭 What's new — the number that actually scores

`squad --full` and `ask "build me a squad"` show a 15-total xP that includes a bench which won't score —
so two builds are hard to compare. This sprint adds a **Starting XI xP** and **Bench xP** breakout
(auto-deriving the best legal XI when no bench is declared), so you can line up iterations and read the
weekly-relevant difference at a glance — and see that, say, three differentials cost you almost nothing
in the XI.

---

### 🎯 Sprint Goal

**Objective:** under `--objective xp`, a full squad build (CLI `squad --full` and `ask "build me a
squad"`) shows a **Starting XI xP** and **Bench xP** breakout — the XI auto-derived via `best_legal_xi`
when no bench is declared (a declared bench uses its own split). Display-only; save unchanged.

#### Success Criteria
- [ ] Approach agreed at the gate (likely **no new ADR** — a display completion under ADR-031/041) —
      auto-derive the best XI for the breakout; decouple from save; both surfaces
- [ ] `squad --full` (xp) shows `Starting XI: N xP` **and** `Bench: M xP`, the XI auto-derived; bench
      rows marked; the 15-total note stays honest
- [ ] `ask "build me a squad …"` shows the same breakout
- [ ] A **declared** bench (`--bench`) still uses its own XI/bench split (unchanged)
- [ ] Non-xp objectives (`points`/`value`/`xgi`) unchanged; existing 384 stay green
- [ ] Tests (the XI/bench xP split; auto vs declared; byte-identical for other objectives) + live smoke
- [ ] Docs: Architecture changelog, Handbook/README, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-130 | **Gate.** The breakout design: auto-derive the best XI (`best_legal_xi`) for `--full` (xp) when no bench is declared; show `Starting XI xP` + `Bench xP`; keep it display-only (save untouched); apply to CLI + `ask`. Confirm no new ADR (under ADR-031/041); pressure-test (done) | Critical | ✅ Done | 0.5 session |
| US-131 | **CLI breakout** — `render_squad` shows `Starting XI: N xP` + `Bench: M xP` from an `xi_ids` it's given (or the declared bench); `cmd_squad` computes the auto-XI for `--full` (xp). Tests + smoke | High | ✅ Done | 1 session |
| US-132 | **`ask` breakout** — `_decide_build_squad` computes the auto-XI and passes it to `render_squad`; the facts note the XI/bench xP so the narration can compare. Tests + smoke + docs | High | ✅ Done | 0.5–1 session |

#### Technical Tasks & Maintenance
- [ ] Update Architecture changelog (the XI/bench xP breakout) — _US-131_
- [ ] Update Handbook/README (comparing builds by XI xP) — _US-132_
- [ ] Update PROJECT_STATUS — _US-132_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — the XI/bench xP split (auto + declared); other objectives byte-identical;
   existing **384** stay green; no new dependency.
2. **Manual smoke test done** — `squad --full` and `ask "build me a squad"` show `Starting XI xP` +
   `Bench xP`; two iterations (e.g. plain vs `--differential 5`) are comparable and show the XI cost
   lands on the bench; `--bench` still uses the declared split; `--objective points` unchanged.
3. **Documentation updated & checked** — Architecture, Handbook/README, sprint board + PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| A `Starting XI xP` / `Bench xP` breakout (auto or declared) | A bench-aware *optimiser* (maximise XI, cheap fodder) — later |
| Reuse `best_legal_xi`; display-only | Changing `--save`/`--load` bench behaviour |
| CLI `squad --full` + `ask "build me a squad"` | A side-by-side "compare two builds" command — later |

**External Dependencies:** None.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Auto-XI vs declared-bench confusion | Low | A declared `--bench` keeps its own split; auto-XI only when none declared; the labels say which |
| Changing squad output surprises users | Low | Additive (two subtotal lines) under `--objective xp`; other objectives unchanged; a test locks it |
| Auto-XI leaks into save | Med | Display-only — `xi_ids` passed to the renderer; `--save` still records the declared bench (a test) |
| Best-XI ≠ best-possible-XI (15 chosen on total) | Low | Out of scope (a bench-aware optimiser is later); the breakout still compares builds faithfully |

---

### 🗝️ Gating decision (US-130)

Settle before code — the approach is probed. Proposed (confirm/redirect at "start US-130"):

1. **Auto-derive** the best XI for a `--full` build (xp objective) via `best_legal_xi(selected,
   xp_by_id)` when **no bench is declared**; a declared `--bench` uses its complement (as today).
2. **Show two subtotals** — `Starting XI: N xP` and `Bench: M xP` — plus the existing bench markers; the
   15-total line + its "bench won't score" note stay.
3. **Display-only** — `cmd_squad`/`_decide_build_squad` pass `xi_ids` to `render_squad`; `--save`/`--load`
   are untouched.
4. **No new ADR** — a display completion of the analyse XI/bench pattern (ADR-031) on the unified xP
   (ADR-041). (Confirm; write a short ADR only if the behaviour change warrants.)

**Worked example (already run):** plain → XI 233.6 / bench 72.2; `--differential 5` → XI 233.5 / bench
68.2 (the tilt cost lands on the bench); `--premium 3` → XI 226.1 / bench 67.9.

---

### 📝 Session Progress Log

- **US-130 (gate) ✅** — Design confirmed, **no new ADR** (a display completion of the analyse XI/bench
  pattern, ADR-031, on the unified xP, ADR-041). Key mechanic verified against the code: `--save` reads
  `p["bench"]` (cli.py:320) and `render_squad` runs *before* save — so passing an **`xi_ids`** to the
  renderer (which computes the XI/bench split **without mutating `p["bench"]`**) keeps the auto-XI
  **display-only**, leaving `--save`/`--load` untouched. Settled: `cmd_squad`/`_decide_build_squad`
  compute `xi_ids` (declared bench's complement, else `best_legal_xi(selected, xp_by_id)`) and pass it;
  `render_squad` shows `Starting XI: N xP` + `Bench: M xP` under `--objective xp`, bench rows sorted last
  + marked; other objectives unchanged. Worked example (run at planning): plain → XI 233.6 / bench 72.2;
  `--differential 5` → XI 233.5 / bench 68.2 (the tilt cost lands on the bench); `--premium 3` → XI 226.1
  / bench 67.9.
- **US-131 (CLI breakout) ✅** — `render_squad` gained an `xi_ids` param: it splits the 15 into XI
  (in `xi_ids`, else the declared-bench complement) and bench, sorts bench last, and under
  `--objective xp` prints **`Starting XI (11) — <shape>: projected N xP`** + **`Bench (4): projected M
  xP`**. `cmd_squad` auto-derives `xi_ids = best_legal_xi(selected, xp)` for a `--full` xp build with **no
  declared bench** — **display-only** (it doesn't touch `p["bench"]`, so `--save` records an empty bench,
  verified). A declared `--bench` drives its own split; other objectives are unchanged. **+2 tests**
  (the breakout + bench-last from `xi_ids`; no breakout for non-xp objectives) → suite **384 → 386**;
  ruff clean; no new dependency. **Smoke:** `squad --full` → *Starting XI (11) — 4-4-2: 233.6 xP · Bench
  (4): 72.2 xP*; `--differential 5` → *XI 233.5 / Bench 68.2* (the tilt lands on the bench); `--bench …`
  → its own split (XI 13 / Bench 2); `--save` bench = `[]`.
- **US-132 (`ask` breakout) ✅** — `_decide_build_squad` computes `xi_ids = best_legal_xi(picks, xp)`,
  passes it to `render_squad` (same breakout), and adds `starting_XI_points_over_5_gameweeks` +
  `bench_points_over_5_gameweeks` to the grounded facts. The narration task was steered to *state the XI's
  projected points* — which **fixed the recurring build-narration ⚠**: the LLM now cites the grounded
  233.6 / 72.2 (✓) instead of inventing a cost split (a nice knock-on — the Sprint-042 follow-up, closed
  for free). No new tests needed beyond the US-131 render coverage + the live smoke; suite stays **386**;
  ruff clean. **Smoke:** `ask "build me a squad for £100m"` → the XI/bench breakout in the table *and*
  the narration ("starting XI ~233.6 points … bench ~72.2"), ✓ trust line. Docs: Architecture, README.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — the owner's XI/bench xP breakout. **US-130** — the gate (design
  confirmed, no new ADR; the display-only mechanic verified against the save flow). **US-131** — the CLI
  breakout (`render_squad` `xi_ids` split + subtotals; `cmd_squad` auto-XI). **US-132** — the `ask`
  breakout + grounded narration, which also fixed the recurring build-narration ⚠. Tests 384 → **386**;
  **no new ADR, no new dependency**.
* **Carried Forward:** None. (A bench-aware *optimiser* — maximise the XI with cheap fodder — remains a
  future item; a side-by-side "compare two builds" command likewise.)
* **Key Artifacts / Decisions:** `render_squad(xi_ids=…)`; the auto-XI via `best_legal_xi`; the
  XI/bench facts + the steered narration task.

#### Retrospective
* **What Went Well?**
  - **Pure reuse, big value.** The breakout is `best_legal_xi` (already there) + a render split — no new
    analytics — yet it makes builds genuinely comparable and revealed that differentials cost the
    *bench*, not the XI (the 15-total hid that).
  - **Display-only, verified.** Checking the save flow first (it reads `p["bench"]`, runs after render)
    let me pass `xi_ids` without mutating anything — so `--save` is provably untouched.
  - **A bonus bug-fix for free.** Putting XI/bench points in the facts *and* steering the task to state
    them fixed the recurring build-narration ⚠ (the Sprint-042 follow-up) — the LLM now cites the
    grounded numbers (✓) instead of inventing a cost split.
  - **Lean and honest sizing.** A display feature scoped as a gate + two small stories, no ADR padding.
* **What Could Be Improved?**
  - **The XI shown is the best-of-the-built-15, not the best-possible XI** (the 15 is chosen on the
    15-total). A bench-aware optimiser would maximise the XI directly — a bigger, later piece.
  - **The narration is only as grounded as the facts allow.** The fix here was to add the number the
    user cares about; the general lesson is "give the LLM the fact it will otherwise invent".
* **Lessons Learned?**
  - Show the number that matters (XI xP), not a proxy (15-total) — the display is where comparison happens.
  - Verify the coupling before you decouple: reading the save flow made "display-only" provable.
  - To quiet a hallucination, supply the missing fact and point the task at it — better than a stricter rule.
* **Action Items for Next:**
  - [ ] (Backlog) a bench-aware squad optimiser (maximise XI xP with cheap fodder); a "compare two builds".
  - [ ] Keep supplying the fact the LLM would otherwise invent.
  - [ ] Keep the 3-part DoD.

---

**Proposed follow-on:** owner to steer — a bench-aware optimiser / "compare builds", more Phase 4 (an
intent classifier / chat), the web UI (Phase 2), or wait for GW1 for Data Hardening + the full Phase-5
xMins.

**Completion Date:** 2026-08-05
**Final Notes:** Squad builds now show the weekly-relevant Starting XI xP vs the non-scoring Bench xP,
from the CLI and in plain English — iterations are comparable at a glance, and the differential's cost is
visibly on the bench. A pure-reuse feature that also closed a lingering narration ⚠. Sprint outcome:
**Successful** — 3/3 stories, zero roll-over, DoD held (44th).
