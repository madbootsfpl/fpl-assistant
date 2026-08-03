# Sprint 018: Clean-Sheet / Defensive-Solidity Lens (xGC)

**Dates:** 2026-08-03
**Status:** ✅ Complete
**Capacity:** ~2 working sessions (a metric + view on data already stored — no ingest)
**Carried Over:** None (Sprint 017 closed clean)

---

### 🔎 Verified at planning (per the standing lesson)

The companion to `defcon` — clean-sheet prospects from **expected goals conceded** (xGC),
which we've stored since Sprint 014 but never surfaced:

- **No new ingest.** We already store `xgc` (`expected_goals_conceded`) and `minutes`, so
  `xGC/90` is computed — and it **matches FPL's own `expected_goals_conceded_per_90` exactly**
  (Raya 0.74, Calafiori 0.52 — computed = FPL to the decimal). Verified, so we compute from
  stored data rather than ingest a redundant field.
- **The metric is sensible — and team-driven.** Lowest xGC/90 (best solidity): Calafiori 0.52,
  J.Timber 0.64, Saliba 0.70, Gabriel 0.72, Raya (GK) 0.74 — **5 of the top 6 are Arsenal**.
  So xGC really ranks **team defences**, surfaced via their defenders/keepers.
- **GKs finally get a lens** — excluded from `defcon`, they belong here (a clean sheet is 4 pts
  for GK/DEF).

**No new dependency.** Preseason caveat as ever (last-season, auto-updates on refresh).
This sprint is Tony's Sprint 017 pick — completing the defensive picture.

---

### 🧭 Architecturally, what's new — almost nothing (and that's the point)

`overperf` and `defcon` each needed a full-stack slice (ingest → migrate → view). This one
needs **only a metric + a view**, because the data is already stored. That's the dividend of
the Sprint-14 ingest: `xgc` was banked long ago; now we spend it.

```
xGC/90 = expected_goals_conceded × 90 ÷ minutes      (computed; == FPL's per-90 field)
```

Lower xGC/90 → the team concedes fewer expected goals while the player is on → **higher
clean-sheet probability**. Ranked **ascending** (best solidity first), minutes-gated (≥ 900,
as `overperf`/`defcon`). It completes the defensive story: **`defcon`** = the DefCon-action
points source; **`cleansheet`** = the clean-sheet points source — the two ways defenders and
keepers score.

**The honest framing (baked in):** xGC is a **team** signal shown per player. So the view
effectively ranks *team defences* — you act on it by picking that team's cheapest nailed
starter. We state this so it isn't mistaken for an individual-defending metric.

---

### 🎯 Sprint Goal

**Objective:** Add a `cleansheet` view — rank defenders and goalkeepers by expected goals
conceded per 90 (lowest = best clean-sheet prospects), minutes-gated — completing the
defensive picture alongside `defcon`.

#### Success Criteria
- [x] Approach agreed (**ADR-019**) before feature code
- [x] A metric computes `xGC/90 = xgc × 90 / minutes` (matches FPL's per-90 field)
- [x] A `cleansheet` view ranks DEF + GK by xGC/90 **ascending**, minutes-gated, `--pos`/`--limit`
- [x] The view shows xGC/90, minutes, position, team; lowest (best) first
- [x] The **team-level** caveat is stated (it ranks team defences, shown per player)
- [x] Handles None/zero minutes safely (no divide-by-zero; None xgc skipped, not coerced)
- [x] Existing views/objectives unchanged
- [x] Tests cover the maths, the sort direction, the minutes gate, and the view (offline)
- [x] **Manual smoke test** run before the sprint is closed (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-056 | Agree the approach (**ADR-019**): `xGC/90 = xgc × 90 / minutes` (computed, no ingest), lower = better, DEF+GK scope, the minutes gate, the team-level caveat, the `cleansheet` view — pressure-test with a worked example | Critical | ✅ Complete | 0.5 session |
| US-057 | The metric + the `cleansheet` view: an analytics function (xGC/90, minutes-gated, ascending) + a ranked view + the `cleansheet` command. Tests + smoke test | High | ✅ Complete | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-019 recorded + added to the ADR index — _US-056_
- [ ] Update Architecture doc (changelog; note xgc is now surfaced) — _US-056_
- [ ] Update `README.md` + `--help` with `cleansheet` — _US-057_
- [ ] Handbook — a short section on the clean-sheet / xGC lens (+ the team-level caveat) — _US-057_

---

### ✅ Definition of Done (this sprint)

The same 3-part DoD that has held for seventeen sprints — a story isn't done until:
1. **Automated tests pass** (and cover the new logic).
2. **Manual smoke test done** — run the real command, eyeball the output, check `--help`.
3. **Documentation updated & checked** — Handbook, Architecture, ADR + index, README,
   sprint board + PROJECT_STATUS, as applicable (Charter Documentation Rules).

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| xGC/90 clean-sheet lens for DEF + GK | A team-level table (this is shown per player) |
| Computed from stored `xgc` + `minutes` | Ingesting `expected_goals_conceded_per_90` (redundant) |
| A minutes-gated `cleansheet` ranked view | A clean-sheet *probability* model / a squad objective |
| The team-level caveat in the output | Combining with DefCon into one "defensive value" score |

**External Dependencies:**
- [ ] FPL API (already used) + PuLP; **no new dependency, no new ingest** (verified above)

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Read as individual defending, not team | Med | State the team-level caveat in the output + docs; it ranks team defences |
| Divide-by-zero on 0 minutes | Low | The ≥ 900 minutes gate excludes them; a test covers a 0-minute case |
| Computed value drifts from FPL's | Low | Verified `xgc × 90 / minutes` == FPL's per-90 field exactly; a test pins the formula |
| Preseason values are last-season | Low | Same as every FPL number; auto-updates on refresh — stated |
| Sort direction (ascending) confusion | Low | Lowest = best is stated in the header; a test pins the order |

---

### 🗝️ Gating decision (US-056 → ADR-019)

Settle before building — **pressure-test with a worked example** (per the standing lesson).
Proposed answers (Tony to confirm/redirect):

1. **The metric.** `xGC/90 = expected_goals_conceded × 90 / minutes`, computed from stored
   fields (verified == FPL's `expected_goals_conceded_per_90`). Lower = better.
2. **Scope.** DEF + GK (the clean-sheet earners, 4 pts). `--pos` can narrow further; MID (1 pt
   for a clean sheet) are out of the default view.
3. **Minutes gate.** `minutes ≥ 900`, as `overperf`/`defcon`.
4. **Ordering & caveat.** Ranked **ascending** (best solidity first); the output states it's a
   **team** signal shown per player (it ranks team defences).
5. **View.** `cleansheet` shows player / team / pos / minutes / xGC-90, `--pos` / `--limit`.

**Worked example to verify at the gate:** on real data, `cleansheet` should top out with
Calafiori (0.52), J.Timber (0.64), Saliba (0.70), Gabriel (0.72), Raya (GK, 0.74) — best
solidity — visibly clustered on the meanest defence (Arsenal), confirming the metric *and* the
team-level nature before any feature code.

---

### 📝 Session Progress Log

#### Session 1 — 2026-08-03 (US-056: ADR-019 — clean-sheet / solidity lens)
* **Completed:** Recorded **ADR-019**: `xGC/90 = expected_goals_conceded × 90 / minutes`,
  **computed** from the stored `xgc` + `minutes` (no ingest), ranking DEF+GK **ascending**
  (lowest = best solidity), minutes-gated (≥ 900). **Pressure-tested on real data:** verified
  the computed value equals FPL's `expected_goals_conceded_per_90` to the decimal (so compute,
  don't ingest); best solidity Calafiori 0.52 / Timber 0.64 / Saliba 0.70 / Gabriel 0.72 /
  Raya (GK) 0.74 — **5 of the top 6 Arsenal**, confirming it ranks *team* defences (the stated
  caveat). GKs get a lens (excluded from `defcon`). Added to the ADR index; Architecture §12
  changelog. US-056 **complete** — no feature code.
* **Manual smoke test:** N/A (docs-only gate story). The worked example *is* the verification.
* **Docs touched:** ADR-019 (new) + index, Architecture changelog, Sprint18 board, PROJECT_STATUS.
* **Issues / Blockers:** None. (Compute-vs-ingest decision verified against FPL's own field.)
* **Next Steps:** US-057 — the metric + the `cleansheet` view.

#### Session 2 — 2026-08-03 (US-057: the metric + the `cleansheet` view)
* **Completed:** New `analytics/cleansheet.py` — `defensive_solidity(players, min_minutes=900)`
  computes `xgc90 = xgc × 90 / minutes` for DEF+GK, minutes-gated, sorted **ascending**; a
  missing `xgc` is **skipped** (not coerced to 0, which would falsely rank as best). No model/
  storage change — `xgc` + `minutes` already stored. `ui/cleansheet.py` renders the ranked list
  + the team-level caveat. CLI: `cleansheet` command (`--pos`, `--limit`, `--min-minutes`).
  **+9 tests → 190 total, all green** (maths, ascending sort, DEF/GK-only, minutes gate,
  None-xgc-skipped, render + caveat, parse). US-057 **complete** — Sprint 018 done.
* **Manual smoke test:** ✅ `cleansheet` → Calafiori 0.52 / Timber 0.64 / Saliba 0.70 / Gabriel
  0.72 / Raya 0.74 (matches the gate; all Arsenal — the team nature visible); `--pos GK` → Raya
  / Donnarumma / Alisson; caveat printed; `--help` shows the options.
* **Docs touched:** README, Handbook Ch20 + Ch25 (clean-sheet section), cli `--help`, Sprint18
  board, PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** Sprint 018 review & retrospective.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** Both stories — US-056 (ADR-019) and US-057 (the metric + `cleansheet` view).
  A clean-sheet / solidity lens ranking DEF+GK by `xGC/90` (lowest = best), minutes-gated —
  the companion to `defcon`. Tests grew 181 → **190**. **No ingest, no migration, no
  dependency** — computed from data stored since Sprint 014.
* **Carried Forward:** None. Backlog: exact DefCon points (season-blocked); a clean-sheet
  *probability* model; a combined "defensive value" (DefCon + clean sheet) score/objective.
* **Key Artifacts / Decisions:** ADR-019 (computed xGC/90, verified == FPL; DEF+GK; team-level
  caveat); `analytics/cleansheet.py`; the `cleansheet` view; Handbook Ch25 section.

#### Retrospective
* **What Went Well?**
  - **Banked data paid off.** `xgc` was ingested in Sprint 014 and spent now — so this was a
    *metric + view only*, the lightest feature sprint in a while. Infrastructure earning its keep.
  - **The defensive picture is complete.** `defcon` (actions) + `cleansheet` (solidity) mirror
    the attacking pair (`xg` + `overperf`) — a well-rounded analytics layer.
  - **Compute-vs-ingest decided by evidence.** Verifying `xgc × 90 / minutes` == FPL's field
    let us skip a redundant ingest with confidence.
  - **A sharp edge caught early.** Unlike `overperf`/`defcon` (where 0 is neutral), here 0 =
    "best" — so a missing `xgc` had to be *skipped*, not coerced. Spotted in the walkthrough.
* **What Could Be Improved?**
  - It's a team signal shown per player — honest, but a true *team* table might read cleaner
    (backlog).
  - Four "ranking" views now share a table shape (`xg`, `overperf`, `defcon`, `cleansheet`); a
    shared renderer is increasingly worth extracting.
* **Lessons Learned?**
  - Ingesting a field early (even before it's used) makes a later feature almost free.
  - The right None-handling depends on the metric's direction — 0 isn't always neutral.
  - A good pair of lenses (attack/defence, actions/solidity) tells a fuller story than either alone.
* **Action Items for Next Sprint (019):**
  - [ ] Consider: a combined defensive-value view/objective, a shared table renderer (tech
    debt), or another backlog pick — check data first.
  - [ ] Keep probe-at-planning + gate + 3-part DoD.

---

**Proposed follow-on (Sprint 019):** a combined "defensive value" (DefCon + clean sheet) lens
or objective, a shared table renderer (tidy the four ranking views), or another backlog pick.

**Completion Date:** 2026-08-03
**Final Notes:** The clean-sheet companion to `defcon` — the lightest sprint in a while,
because `xgc` was banked back in Sprint 014. The defensive picture is now complete. Sprint
outcome: **Successful** — 2/2 stories, zero roll-over, DoD held.
