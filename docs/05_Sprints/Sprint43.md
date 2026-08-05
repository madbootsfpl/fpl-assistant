# Sprint 043: The differential — ownership data + a differential archetype

**Dates:** 2026-08-05
**Status:** ✅ Complete (3/3 stories, retro done)
**Capacity:** ~2–3 working sessions (a gate + an ownership ingest + the constraint)
**Carried Over:** None (Sprint 042 closed clean)

> **Direction (owner):** finish the archetype feature (ADR-043) with the **differential** — *"the other
> player type … we probably need to define that first and then include as an option."* It was defined
> and deferred last sprint (needs ownership data); this sprint ingests ownership and ships it.

---

### 🔎 Verified at planning (the standing lesson — and it shaped the definition)

- **Ownership is available + easy to ingest.** `selected_by_percent` is in `bootstrap-static`
  (e.g. Raya 30.8%); adding a `selected_by` column mirrors exactly how `chance` was added (model
  `from_api` + a storage column/migration + `get_players` SELECT + `refresh`).
- **The constraint bites — the optimal squad is template-heavy.** In the £100m xP-optimal 15, **9 of 15
  players are >10% owned** (João Pedro 54.6%, Raya 30.8%, Gabriel 25.9%, Semenyo 22%…); only 6 are
  ≤10%, 2 are ≤5%. So forcing more low-owned players genuinely tilts the squad away from template.
- **⚠ A bare ownership threshold conflates enablers with differentials.** Median ownership is **0.4%**;
  "≤10%" captures 92% of players — including the cheap bench fodder (Stach £6/1.4%, Truffert £5.5/4.7%).
  A manager's "differential" is a low-owned player *worth starting* (mid-price+), not an enabler. **So
  the gate must decide the definition:** ownership-only, or ownership **and** a price floor (e.g. ≥£5.5m)
  / an xP floor. *(This is the "verify at planning" catch — a naive `≤10%` would make "≥3 differentials"
  a no-op, since the optimal squad already has cheap low-owned fillers.)*
- Still preseason (0 GWs); ClubElo up (intermittent).

---

### 🧭 What's new — pick against the template, on purpose

The squad builder can shape by price (low-cost / premium); this adds the third archetype the owner
named — the **differential**: a low-owned player you pick *instead of* the popular template option, to
gain rank when it hits. It needs a new datum (ownership), a sensible definition (not just "cheap and
unowned"), and the same min-count constraint pattern the price bands use — then it drops the
"coming soon" note and completes ADR-043.

---

### 🎯 Sprint Goal

**Objective:** ingest `selected_by_percent`; define the **differential** (low ownership + *worth
starting* — pinned at the gate); add a differential min-count constraint to `select_squad`, surfaced as
`squad --full --differential N` and the already-parsed NL count; a differential build tilts the squad
away from template. The "coming soon" note is removed.

#### Success Criteria
- [ ] Approach agreed (**ADR-044**) — the differential definition (ownership threshold + whether a price/xP
      floor); the ingest schema; the `select_squad` constraint; the CLI/NL surface. Pressure-tested (it bites)
- [ ] **Ownership ingested** — `players.selected_by` populated by `refresh` (model + storage + SELECT)
- [ ] `select_squad` honours a **differential minimum** (≥N players meeting the definition); byte-identical
      without it; infeasible → a clear message
- [ ] `squad --full --differential 2` and `ask "build me a squad with 2 differentials"` tilt the squad
      (the "coming soon" note gone); grounded + verified
- [ ] Tests (the ingest; the constraint bites; infeasibility; the parser already exists) + live smoke
- [ ] Docs: ADR-044 + index, Architecture, Handbook/README, PROJECT_STATUS; Backlog item closed

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-127 | **Gate.** Differential design (**ADR-044**): the definition (ownership ≤10% + *worth-starting* floor — pin on data); the ownership ingest schema; the `select_squad` differential constraint; the CLI/NL surface. Pressure-test that it bites (template-heavy optimal squad) | Critical | ✅ Done | 0.5–1 session |
| US-128 | **Ownership ingest** — a `selected_by` field on the player model (`from_api` ← `selected_by_percent`) + a storage column/migration + `get_players` SELECT; `refresh` populates it. Tests | High | ✅ Done | 1 session |
| US-129 | **The differential constraint** — `select_squad` takes a differential minimum (per the definition); `squad --full --differential N`; wire the NL count (drop "coming soon"); infeasible → a clear message. Tests + smoke + docs | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-044 recorded + added to the ADR index — _US-127_
- [ ] Update Architecture changelog (ownership; the differential) — _US-128/129_
- [ ] Update Handbook/README (`--differential`; the multi-faceted `ask`) — _US-129_
- [ ] Update PROJECT_STATUS; close the Backlog "Differential archetype" item — _US-129_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — ownership ingest (`from_api`/save/read); the differential constraint bites
   + infeasibility; byte-identical without it; existing **380** stay green; no new dependency.
2. **Manual smoke test done** — `refresh` populates ownership; `squad --full --differential 3` and
   `ask "… with 2 differentials"` tilt the squad away from template (lower-owned picks in); the
   "coming soon" note is gone; an over-ask gives a clear message.
3. **Documentation updated & checked** — ADR-044 + index, Architecture, Handbook/README, sprint board +
   PROJECT_STATUS; the Backlog differential item closed.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Ingest `selected_by_percent`; a differential archetype + constraint | Ownership *trends* (rising/falling) — later |
| CLI `--differential N` + NL (the count already parses) | Per-position differentials ("a differential forward") — later |
| Reuse the ADR-043 band/constraint pattern + `build_squad` | Effective-ownership / captaincy-adjusted metrics — later |

**External Dependencies:** `bootstrap-static` `selected_by_percent` (already fetched by `refresh`).

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| **A naive ≤10% is a no-op** (enablers already qualify) | High | The gate pins a *worth-starting* definition (a price/xP floor) so "≥N differentials" actually bites; a worked example proves it |
| Over-asking differentials tanks xP | Med | Expected (the user's choice); the objective still picks the best qualifying players; a clear infeasible message |
| Ownership not populated (old DB) | Low | `refresh` populates it; the constraint degrades (no qualifiers) → a clear message; `None` ≠ a differential |
| Threshold is a judgement call | Low | Pin on data (excludes the 9 template players in the optimal squad); document + make it tunable |

---

### 🗝️ Gating decision (US-127 → ADR-044)

Settle before code — the data is probed. Proposed (confirm/redirect at "start US-127"):

1. **Definition.** A **differential** = `selected_by_percent ≤ 10%` **and** *worth starting* — a price
   floor (**≥ £5.5m**, excluding the £4–4.5 enabler tier) so "≥N differentials" tilts the *real* picks,
   not the bench fodder. (Both thresholds tunable; pinned because they exclude the 9 >10%-owned template
   players in the optimal squad and the cheap fillers.) *Confirm/redirect — ownership-only vs +price floor.*
2. **Ingest.** `Player.selected_by` (float) from `selected_by_percent`; a `selected_by REAL` column +
   migration + `get_players` SELECT; `refresh` populates it. `None` for a player without data.
3. **Constraint.** `select_squad(..., min_differentials=N)` (with the definition's thresholds as module
   constants) → `Σ pick[p] (selected_by ≤ 10 and price ≥ 5.5) ≥ N`; the xP objective picks the best
   qualifiers. Absent → today's behaviour. Infeasible → a clear message.
4. **Surface.** CLI `--differential N`; `build_squad` already parses the count — wire it and **remove the
   "coming soon" note**. Grounded + optional.

**Worked example (to run at the gate):** confirm the optimal squad has ~template picks >10%, and that
`--differential 4` forces ≥4 low-owned worth-starting players in (a real tilt), while a huge count →
infeasible.

---

### 📝 Session Progress Log

- **US-127 (gate) ✅** — Recorded **ADR-044** after a walk-through that **changed the definition**. The
  probe on the live API + optimal squad showed: it's template-heavy (9/15 >10% owned), but a naive
  `≤10%` is a **no-op** — the optimal squad already holds 6 ≤10% (incl. mid-price enablers Truffert 4.7%,
  Stach 1.4%), so "≥3 differentials" wouldn't change anything. **≤5% is the sweet spot** (optimal squad
  has only 2 ≤5% → "≥3" bites). **Owner chose ≤5%.** Settled: differential = `selected_by_percent ≤ 5.0`
  (`DIFFERENTIAL_MAX_OWNERSHIP`, tunable; no price/xP floor — the xP objective picks the best qualifiers);
  ingest `selected_by` (mirrors `chance`); `select_squad(min_differentials=N)` → one ILP line; CLI
  `--differential N` + wire `build_squad`'s existing parse (drop "coming soon"); combinable with
  `--cheap`/`--premium`; over-ask / no data → a clear message. ADR-044 indexed.
- **US-128 (ownership ingest) ✅** — Added `Player.selected_by` (`from_api` ← `selected_by_percent`, a
  string → float via `_to_float`) + a `selected_by REAL` storage column (`_MIGRATIONS` + CREATE + the
  UPSERT columns/values/ON CONFLICT + the save tuple); `get_players`' `SELECT p.*` carries it through.
  A line-for-line mirror of how `chance` was added. **+2 tests** (`from_api` parses ownership / absent →
  None; save + `get_players` round-trip) → suite **380 → 382**; ruff clean; no new dependency. **Smoke:**
  `refresh` populated **568/568** players (Haaland 75%, João Pedro 54.6%…); **422 players ≤5%** in the
  pool — plenty to force differentials.
- **US-129 (the differential constraint) ✅** — `select_squad` gained `min_differentials=N` → one ILP
  line (`Σ pick[p] (selected_by ≤ 5%) ≥ N`; a `_selected_by` accessor handles sqlite Rows / dicts;
  players with no ownership don't count); byte-identical when absent. `squad --full --differential N`
  wires it (infeasible → a clear message with the counts); `build_squad` passes the already-parsed count
  and the **"coming soon" note is removed**; the requested structure joins the grounded facts. **+3
  tests** (a differential is forced in while staying optimal; infeasible without any ≤5% players; the
  CLI flag) → suite **382 → 384**; ruff clean; no new dependency. **Live smoke:** `--differential 5` →
  the squad's ≤5%-owned count rises **2 → 5** at a small **tilt cost** (305.8 → 301.7 xP); `ask "build me
  a squad with 3 differentials"` tilts off-template (no "coming soon"). **Backlog differential item
  closed** — the archetype trio (low-cost / premium / differential) is complete.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — the differential completes the archetype trio. **US-127** — ADR-044
  (a walk-through that flipped the definition to ≤5%). **US-128** — the ownership ingest
  (`selected_by`, a `chance`-style mirror). **US-129** — `min_differentials` in `select_squad` +
  `--differential N` + the NL wiring (the "coming soon" note gone). Tests 380 → **384**; one ADR; **no
  new dependency**. Backlog differential item closed.
* **Carried Forward:** None.
* **Key Artifacts / Decisions:** ADR-044 (≤5% definition); `Player.selected_by` + the storage column;
  `min_differentials` + `DIFFERENTIAL_MAX_OWNERSHIP`; `_selected_by`.

#### Retrospective
* **What Went Well?**
  - **The walk-through changed the definition — and saved a silent no-op.** My planned ≤10% would have
    left "≥3 differentials" already satisfied (the optimal squad has 6 low-owned enablers), so nothing
    would change and the owner would rightly ask "why?". The probe → ≤5% (optimal has 2) → it bites.
    "Verify at planning" caught it *and* the owner made the call.
  - **The ingest was a copy.** Adding `selected_by` was a line-for-line mirror of `chance` — model +
    storage + migration + `SELECT *` carries it. Low-risk data work.
  - **The constraint was one ILP line.** The ADR-043 min-count pattern generalised to ownership with a
    single line; combinable with `--cheap`/`--premium`; byte-identical when absent.
  - **The tilt is honest and visible.** `--differential 5` trades 305.8 → 301.7 xP for 2 → 5 off-template
    picks — exactly what a differential strategy *is*, and the squad table shows it.
* **What Could Be Improved?**
  - **Differentials are rarely infeasible alone** (422 players ≤5%) — the infeasible path only bites when
    combined with premiums/budget. Fine, but the interesting failures are combinations.
  - **The threshold is a single global %.** Per-position or effective-ownership differentials are a
    later refinement the constraint interface already supports.
* **Lessons Learned?**
  - Pin a threshold on what actually *changes the output*, not a textbook heuristic — ≤10% looked right
    and did nothing.
  - A new datum is cheap when you mirror an existing field's path end-to-end.
  - Let the objective do the quality work — force *count*, and xP picks the *best* qualifiers.
* **Action Items for Next:**
  - [ ] (Backlog) per-position / effective-ownership differentials; ownership *trends*.
  - [ ] (Polish) the build-narration prompt (to reduce ⚠ fabrications, from Sprint 042).
  - [ ] Keep the walk-through-before-gate habit; keep the 3-part DoD.

---

**Proposed follow-on:** owner to steer — more Phase 4 (an intent classifier / chat), the web UI (Phase
2), or wait for GW1 for Data Hardening + the full Phase-5 xMins.

**Completion Date:** 2026-08-05
**Final Notes:** The archetype trio is complete — a squad can be shaped by low-cost, premium, *and*
differential, from the CLI and in plain English, staying xP-optimal given the constraints. The
walk-through was the sprint's pivot: it turned a plausible-but-toothless ≤10% into a ≤5% that bites.
Sprint outcome: **Successful** — 3/3 stories, zero roll-over, DoD held (43rd).
