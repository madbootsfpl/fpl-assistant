# Sprint 040: One metric — unify the squad optimiser with xP (+ a squad-build `ask` intent)

**Dates:** 2026-08-04
**Status:** ✅ Complete (3/3 stories, retro done)
**Capacity:** ~2–3 working sessions (a gate + an optimiser fix + a Phase-4 intent)
**Carried Over:** None (Sprint 039 closed clean)

> **Direction (owner's Sprint-39 notes + leaning):** *"I build a squad for max points, it looks great,
> then `transfer` suggests moves that give more points — why weren't those in the squad? There should
> be no transfers that give extra points when nothing changed, or am I confused?"* → **answer it (Part
> A)**, then **more Phase 4 (Part B)**.

---

### 🔎 Verified at planning (the standing lesson — the inconsistency is real, and the fix is proven)

The owner is **not** confused — it's an **objective mismatch**, diagnosed on real data:

- **`squad --full` optimises `--objective points`** = last season's **total points** (`total_points`,
  backward-looking). `transfer`/`analyse`/`captain`/start-bench all rank by **xP** — next-5-GW,
  fixture-adjusted, historical-baseline, **xMins-weighted** (forward-looking). Different quantities →
  a squad best on last-year's-points is *not* best on next-5-GW-xP, so transfers "improve" it.
- **Even `squad --objective xp` wouldn't fix it today:** `objective_scores("xp", …)` calls
  `player_xp(players, upcoming)` with **defaults** — horizon **1**, **no** baseline/fallback, **no**
  xMins. So the optimiser's xP is a *degraded* metric that disagrees with the decision layer's xP.
- **The fix is proven** (worked example): build a 15-man squad on the **full** xP (horizon 5 + baseline
  + fallback + xMins) → its full-xP total is **305.8** and `transfer` finds **0** positive moves; build
  on today's degraded xP → **239.0** and `transfer` finds **5** (top +14.7). Unify the optimiser's xP
  with the decision layer → the squad is better *and* consistent.
- Still preseason; ClubElo up (intermittent).

---

### 🧭 What's new — one metric everywhere

The tool has quietly used two currencies: the optimiser spends `total_points` (or a degraded xP), the
recommendations speak full xP. This sprint makes **xP the single language** — the squad optimiser builds
on the exact xP the decision layer uses, so "the optimal squad" and "no free transfers" finally agree.
Then Part B extends Phase 4 by exposing that unified optimiser through `ask` (*"build me a squad"*).

---

### 🎯 Sprint Goal

**Objective (Part A):** the squad optimiser's `xp` objective uses the **same full xP** as the decision
layer (horizon + baseline/fallback + xMins), via one shared call so they can't diverge; the
points-vs-xP distinction is explained; a squad built on xP leaves `transfer` with nothing to suggest.
**(Part B):** an `ask "build me a squad [for £X]"` intent — grounded, xMins-aware, using that optimiser.

#### Success Criteria
- [ ] Approach agreed (**ADR-041**) before code — unify the optimiser's xP with the decision layer; the
      default-objective decision (keep `points`, or make `xp` default); the squad-build intent design
- [ ] **Consistency:** a squad built on the unified xP → `transfer` (same xP) finds **no positive moves**
      (proven at planning; locked by a test)
- [ ] The optimiser's `xp` objective = full xP (horizon/baseline/fallback/xMins), the **same** call
      `analyse`/`transfer` make (a shared helper — echoing `best_legal_xi`)
- [ ] The points-vs-xP difference is **explained** (a note / cross-link) so the default is understood
- [ ] **Part B:** `ask "build me a squad for £100m"` returns the optimal 15 (xMins-weighted xP), a
      structured squad table + narration + the ✓ trust line; budget parsed from the question
- [ ] Tests (unified objective; squad↔transfer consistency; budget parse; the intent) + live smoke
- [ ] Docs: ADR-041 + index, Architecture, Handbook/README, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-118 | **Gate.** Answer the question + decide the fix (**ADR-041**): unify the optimiser's `xp` objective with the decision layer's full xP (one shared call); the **default-objective** decision (points vs xp); the **explanation**; and the Part-B intent design. Pressure-test consistency (done: unified → 0 transfers) | Critical | ✅ Done | 0.5–1 session |
| US-119 | **One metric** — the `squad`/optimiser `xp` objective builds on the full shared xP (horizon + baseline/fallback + xMins); a squad on xP leaves `transfer` nothing; the points-vs-xP note. Tests + smoke | High | ✅ Done | 1 session |
| US-120 | **Phase 4: `ask "build me a squad [for £X]"`** — parse the budget; optimise the 15 on the unified xP; a squad detail table + grounded narration + ✓ line; `subjects`. Tests + smoke | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-041 recorded + added to the ADR index — _US-118_
- [ ] Update Architecture changelog (one xP metric; the squad-build intent) — _US-119/120_
- [ ] Update Handbook/README (points vs xP; `ask "build me a squad"`) — _US-120_
- [ ] Update PROJECT_STATUS — _US-120_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — the unified objective; squad-on-xP → 0 transfers; budget parse; the new
   intent; existing **365** stay green; no new dependency.
2. **Manual smoke test done** — `squad --full --objective xp` then `transfer --squad …` shows no
   positive moves; `ask "build me a squad for £100m"` returns a sane 15 + ✓ line.
3. **Documentation updated & checked** — ADR-041 + index, Architecture, Handbook/README, sprint board +
   PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Unifying the optimiser's `xp` objective with the decision xP | Re-tuning ≥900-min partial-season baselines (GW1) |
| A squad-build `ask` intent | Chip strategy / transfer-path planning (Phase 5) |
| Explaining points vs xP; the default-objective call | Removing the `points` objective (kept; maybe not default) |
| Reusing `player_xp`, the optimiser, `render_squad`, the verifier | The full probabilistic xMins (Phase 5) |

**External Dependencies:** None beyond stored FPL data + the (optional) local LLM.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Changing the squad default surprises users | Med | Gate decision; if `xp` becomes default, keep `--objective points` + a clear note; explain the difference |
| The optimiser + decision layer drift again | Med | One shared xP call (like `best_legal_xi`); a consistency test locks squad-on-xp → 0 transfers |
| Budget parsing ("£100m", "100") is fiddly | Low | A small, tested parser (like `_transfer_count`); sensible default (£100m) |
| Squad-build intent overlaps `squad` command | Low | It *is* the command via NL — grounded, with the ✓ line; reuses `render_squad` |

---

### 🗝️ Gating decision (US-118 → ADR-041)

Settle before code — the diagnosis + fix are proven. Proposed (confirm/redirect at "start US-118"):

1. **Unify the xP objective.** `objective_scores("xp", …)` (and the `squad` command's xp path) build on
   the **full** xP the decision layer uses — horizon (`--next`), historical baseline + the low-evidence
   fallback (ADR-040), and **xMins** (ADR-038, with `--no-xmins`). One shared call so the optimiser and
   the recommendations can't disagree. Proven: a squad on this xP → `transfer` finds 0 moves.
2. **The default objective.** *Recommended:* make **`xp` the default** `squad` objective (it's the
   forward-looking metric the whole tool speaks, and it makes `squad` consistent with `transfer`),
   keeping `--objective points` for the season-total view. *(Confirm/redirect — this changes
   `squad --full` output.)*
3. **Explain it.** A note on the squad output / handbook: `points` = last-season total (proven value);
   `xp` = expected points next N GW (fixtures + minutes) — the metric the recommendations use.
4. **Part B intent.** `ask "build me a squad [for £X]"` → parse the budget (default £100m), optimise the
   15 on the unified xP, render the squad (reuse `render_squad`) as structured detail, narrate + verify
   (`subjects` = the squad). Grounded + optional like every intent. *(Alternative Part B if preferred: a
   smarter router — "start X or Y" → compare.)*

**Worked example (already run):** squad on full xP → total 305.8, `transfer` finds 0; squad on degraded
xP → 239.0, `transfer` finds 5 (top +14.7).

---

### 📝 Session Progress Log

- **US-118 (gate) ✅** — Recorded **ADR-041**, design proven on the live DB and one owner decision
  settled:
  - **Root cause confirmed:** `squad --full` optimised `points` (last-season total); `transfer` ranks
    by full xP; even `--objective xp` used a *degraded* xP (`player_xp(players, upcoming)` — horizon 1,
    no baseline/fallback/xMins). The full-xP recipe is duplicated across the decision commands.
  - **Consistency proven:** a 15 built on the **full** xP → total **305.8**, `transfer` finds **0**;
    on the degraded xP → **239.0**, `transfer` finds **5** (top +14.7).
  - **Owner decision:** `xp` becomes the **default** `squad` objective (xMins-weighted; `--no-xmins`
    for raw); `--objective points` kept for the season-total view.
  Settled: one shared `decision_xp(players, upcoming, history_by_code, *, source, horizon,
  minutes_weighted)` recipe used by `squad` + `analyse`/`transfer`/`ask` (can't drift); the points-vs-xP
  note; and Part B — `ask "build me a squad [for £X]"` on the unified optimiser. ADR-041 indexed.
- **US-119 (one metric) ✅** — Added `decision_xp(players, upcoming, history_by_code, *, source, horizon,
  minutes_weighted)` in `xp.py` (the one full-xP recipe: baseline + fallback + xMins). Routed `squad`'s
  **xp** objective, `cmd_analyse`, and `cmd_transfer` through it (removing the triplicated
  baseline/weight assembly); **flipped the `squad` default to `xp`** and added `--no-xmins` to `squad`;
  a points-vs-xP **note** in `render_squad`. **+2 tests** (default is xp / `points` still selectable; an
  xp-optimal squad → `suggest_transfers` returns `[]`, the consistency invariant) + one updated → suite
  **365 → 366**; ruff clean; no new dependency. **Live smoke:** `squad --full` now reads *objective: xp*
  with the note; building an xp squad → `transfer` shows **"No positive-gain transfers"** (the owner's
  expected consistency); `--objective points` still works.
- **US-120 (Phase 4: build-a-squad intent) ✅** — Routed `build_squad` (keywords `build`/`wildcard`/`best
  squad`…, after start_bench so it doesn't steal "start from my squad"). `_squad_budget` parses
  `£100m`/`85m` (default £100m); `_decide_build_squad` optimises the 15 on the unified `decision_xp`,
  renders via `render_squad` as the structured detail, narrates + verifies (`subjects` = the 15). Also
  finished routing `ask`'s `_squad_xp`/`_decide_compare` through `decision_xp` (DRY). **Found + fixed a
  latent grounding bug:** a `£` fact was JSON-escaped to `£`, whose `00`/`3` polluted the number set
  and wrongly flagged `£100.0m` — `verify_grounding`/`_build_prompt` now pass `ensure_ascii=False`
  (build_squad's £ facts were the first to expose it). **+3 tests** (routing precedence; budget parse;
  the £ verifier fix) → suite **366 → 369**; ruff clean; no new dependency. **Live smoke:** `ask "build
  me a squad for £100m"` returns the optimal xP 15 + the notes, narrates the standout picks, and shows
  the **✓ trust line**.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories, answering the owner's *"why does `transfer` improve my optimal
  squad?"* **US-118** — ADR-041 (diagnosis + the unify/default/intent decisions; consistency proven).
  **US-119** — `decision_xp` (one full-xP recipe) used by `squad`/`analyse`/`transfer`/`ask`; `xp` the
  default `squad` objective; an xp-optimal squad → 0 transfers (locked by a test). **US-120** —
  `ask "build me a squad [for £X]"`; and a latent grounding-verifier `£` bug fixed. Tests 365 → **369**;
  one ADR; **no new dependency**.
* **Carried Forward:** None. (Showing xP in the squad table's column — instead of last-season Pts — is a
  small follow-up; a note covers it for now.)
* **Key Artifacts / Decisions:** ADR-041; `decision_xp`; `xp` the default squad objective;
  `_decide_build_squad` + `_squad_budget`; the `ensure_ascii=False` grounding fix.

#### Retrospective
* **What Went Well?**
  - **The owner's question had a clean, provable answer.** Two metrics were in play (last-season points
    vs forward xP); unifying them made a *better* squad (305.8 vs 239.0) and zero free transfers — the
    consistency he expected, proven on real data before code.
  - **Consistency made structural, again.** `decision_xp` is the one place xP is defined now (as
    `best_legal_xi` was for the XI) — the optimiser and the recommendations can't drift, and the DRY
    fell out for free (three duplicated assemblies removed).
  - **A new feature surfaced an old bug.** `build_squad`'s `£` facts exposed a latent
    `verify_grounding` flaw (JSON-escaped `£` polluting the number set) — the same pattern as Enes Ünal
    last sprint: exercise a new shape and the dormant defect shows.
* **What Could Be Improved?**
  - **The squad table still shows last-season Pts** while optimising xP — a note bridges it, but showing
    xP in the column would be clearer. A small follow-up.
  - **Routing keywords keep growing** (`build`, `wildcard`, …) — fine for six intents, but a more
    robust intent classifier will be worth it if this keeps expanding.
* **Lessons Learned?**
  - When two tools disagree, check they're optimising the *same quantity* first — the metric, not the code.
  - One shared function beats two that coincide — make consistency impossible to break.
  - Ship a new input shape and re-run the checks: it flushes out latent bugs (the `£` escape).
* **Action Items for Next:**
  - [ ] (Backlog) show xP in the squad table when `--objective xp`; consider an intent classifier.
  - [ ] (GW1) the deferred partial-season baseline tuning; the full Phase-5 xMins.
  - [ ] Keep the gate probe broad; keep the 3-part DoD.

---

**Proposed follow-on:** owner to steer — more Phase 4, the web UI (Phase 2), or wait for GW1 for Data
Hardening + the full Phase-5 xMins.

**Completion Date:** 2026-08-04
**Final Notes:** One xP metric everywhere — `squad`, `analyse`, `transfer`, and `ask` can no longer
disagree, and the owner's "no free transfers" holds by construction. `ask` gained a build capability,
and a dormant grounding bug is gone. Sprint outcome: **Successful** — 3/3 stories, zero roll-over, DoD
held (40th).
