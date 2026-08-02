# Sprint 010: Squad Objective Toggle

**Dates:** 2026-08-02
**Status:** ✅ Complete
**Capacity:** ~2–3 working sessions (a focused extension of the optimiser)
**Carried Over:** None (Sprint 009 closed clean)

---

### 🔎 Verified at planning (per the standing lesson)

The objectives use data already present: `total_points` and `price` (both 564/564),
and — for the xP objective — upcoming fixtures + `player_xp` (built in Sprint 005). No
new data or dependency. Still blocked (preseason): `form`, attack/defence strengths.

This sprint is Tony's Sprint 009 pick from the backlog.

---

### 🧭 Architecturally, what's new — a pluggable objective

Until now the squad optimiser hard-codes one goal: maximise last-season `total_points`.
Sprint 010 makes the objective **pluggable** — the optimiser maximises *any* per-player
score, and a small helper computes that score for the chosen metric:

```
squad --objective points   → total_points          (today's default)
squad --objective value    → points-per-£m          (points ÷ price)
squad --objective xp        → expected points        (reuses player_xp)
```

This **connects the analytics to the decision engine** — the value and xP metrics you
built become what the optimiser optimises. Structurally: the optimiser stays generic
("maximise these scores"), and *what* the scores are is decided outside it.

*Not an objective:* **elo** — it's team strength (used by the FDR), not a player score,
and can't be summed across a squad. It stays in `fdr --type elo`.

---

### 🎯 Sprint Goal

**Objective:** Let the squad optimiser maximise the metric the user chooses — last-season
points (default), value (points-per-£m), or expected points (xP) — turning "best
historical squad" into "best squad for *this* goal".

#### Success Criteria
- [x] Objective-toggle approach agreed (ADR-011) before feature code
- [x] The optimiser maximises a per-player score (defaults to points; same result as today)
- [x] `objective_scores()` computes points / value / xp scores from the players
- [x] `squad --objective points|value|xp` works and the output states the objective
- [x] Edge cases handled (price 0 for value; no fixtures for xp) — no crash
- [x] Tests cover each objective + the edge cases (offline)
- [x] **Manual smoke test** run before the sprint is closed (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-034 | Agree objective-toggle approach (ADR-011): objectives (points/value/xp), generic optimiser score, xp defaults, display | Critical | ✅ Complete | 0.5 session |
| US-035 | Optimiser takes a per-player `scores` objective + `objective_scores()` helper (points/value/xp; reuse `player_xp`) | High | ✅ Complete | 1 session |
| US-036 | `squad --objective …` command + display the objective + Handbook/README | High | ✅ Complete | 1 session |

#### Technical Tasks & Maintenance
- [x] ADR-011 recorded + added to the ADR index - _Done (US-034)_
- [x] Update Architecture doc if needed (pluggable objective note) - _Done (US-034)_
- [x] Update `README.md` with `squad --objective` - _Done (US-036)_

---

### ✅ Definition of Done (this sprint)

Same 3-part DoD that has held for nine sprints — a story isn't done until:
1. **Automated tests pass** (and cover the new logic).
2. **Manual smoke test done** — run the real command, eyeball the output, check `--help`.
3. **Documentation updated & checked** — Handbook, Architecture, ADR + index, README,
   sprint board + PROJECT_STATUS, as applicable (Charter Documentation Rules).

A "smoke test" + "docs touched" note goes in the session log for each feature story.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Objectives: points, value, xp | An `elo` objective (team-level, not a player score) |
| Reuse `player_xp` for the xp objective | Form-based xP (preseason-blocked) |
| Works with include/exclude and budget | Multi-objective / weighted blends |
| State the objective in the output | 15-man squad, formations (backlog) |

**External Dependencies:**
- [ ] Existing players/fixtures data + PuLP; no new data or dependency

---

### ⚠️ Risks & Mitigations

| Risk | Impact (High/Med/Low) | Mitigation Strategy |
|---|---|---|
| Value objective divide-by-zero (price 0) | Med | Guard (undefined value → score 0); a test covers it |
| xp objective needs fixtures | Med | Compute via `player_xp`; if none, xp is 0 (degenerate but no crash) — note it |
| Optimiser now maximises floats | Low | PuLP/CBC handle real coefficients fine |
| Coupling squad → xp analytics | Low | Scores computed *outside* the optimiser; it stays generic |

---

### 🗝️ Gating decision (US-034 → ADR-011)

Settle before building (pressure-test with a worked example, per the standing lesson):
1. **Objectives** — points (default), value (points ÷ price), xp (via `player_xp`).
   Elo excluded (team-level).
2. **Generic optimiser** — `select_squad(..., scores=None)` maximises `Σ scores[p]·pick[p]`;
   `scores` defaults to `total_points` (so today's result is unchanged).
3. **xp objective defaults** — next single gameweek, `fpl` difficulty for v0 (extending
   to `--type`/`--next` is a backlog item).
4. **Display** — the output states the objective; consider showing the score used.

---

### 📝 Session Progress Log

#### Session 1 - 2026-08-02 (US-034: ADR-011 — objective toggle)
* **Completed:** Recorded ADR-011: objectives points (default) / value (points ÷ price, guard 0) / xp (via `player_xp`, v0 next-GW/fpl); elo excluded (team-level). Generic optimiser `select_squad(..., scores=None)` maximises `Σ scores·pick` (default `total_points`, unchanged); `objective_scores()` computes the per-player score outside the optimiser; output states the objective. **Pressure-tested with a worked example** (2 FWD: points→A(10/£10), value→B(8/£4, ppm 2.0) — different picks; and scores=None reproduces today). Added to ADR index; Architecture §4 changelog note. US-034 **complete** — no feature code.
* **Manual smoke test:** N/A (docs-only gate story).
* **Docs touched:** ADR-011 (new) + index, Architecture changelog, Sprint10 board, PROJECT_STATUS.
* **Issues / Blockers:** None. (Data verified at planning; mechanism pressure-tested.)
* **Next Steps:** US-035 — generic optimiser score + `objective_scores()`.

#### Session 2 - 2026-08-02 (US-035: generic objective + objective_scores)
* **Completed:** `select_squad(..., scores=None)` now maximises a per-player score (default `total_points` → unchanged). `objective_scores(players, objective, upcoming)` computes points/value/xp (value guards price 0; xp reuses `player_xp`, which gained an `id`). 5 new tests incl. the objective-flips-the-pick + default-is-points regression (111 total). US-035 **complete** — command is US-036.
* **Manual smoke test:** ✅ Real points/value/xp squads differ sensibly — points £80.0m/2024, value £65.5m/1767 (leaves budget), xp £79.0m/1798 (fixtures-aware).
* **Docs touched:** Handbook Ch22 (pluggable objective), Sprint10 board, PROJECT_STATUS. (Architecture in US-034.)
* **Issues / Blockers:** None.
* **Next Steps:** US-036 — the `squad --objective …` command + display.

#### Session 3 - 2026-08-02 (US-036: the squad --objective command)
* **Completed:** `squad --objective points|value|xp` (default points) — the handler computes scores (fetching fixtures only for xp) and passes them to `select_squad`; `render_squad` states the objective. Added to `--help`, Ch20, README. 3 tests (parse + render). 114 total. US-036 **complete** — all Sprint 010 stories done.
* **Manual smoke test:** ✅ `--objective value` (£65.5m/1767), `--objective xp --include Haaland` (composes — Haaland forced, £80.0m/1738), `--help` shows the option.
* **Docs touched:** Handbook Ch20, README, cli `--help`, Sprint10 board, PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** Sprint 010 review & retrospective.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-034 (ADR-011), US-035 (generic optimiser + `objective_scores`), US-036 (`squad --objective`). The optimiser now maximises the metric the user chooses (points/value/xp), and it composes with include/exclude and budget. Tests grew 106 → 114. No new data/dependency.
* **Carried Forward:** None. Backlog: FBref xG/xA, 15-man squad/formations, `--type`/`--next` for the xp objective, plus season-dependent FPL work.
* **Key Artifacts / Decisions:** ADR-011 (pluggable objective, with a worked example); generic `select_squad(scores=...)`; `objective_scores()`; commits `8492126`→`560c1bd`.

#### Retrospective
* **What Went Well?**
  - **The whole toolkit converged** — value (Sprint 2) and xP (Sprint 5) now feed the optimiser (Sprint 7). Tony's backlog review picked the "tie it together" option.
  - **The generic-core / decide-at-the-edge pattern recurred** — the optimiser became a pure "maximise these scores" engine; the objective moved outside it.
  - **It composes** — objective + include/exclude + budget all work together, because each was built independently and tested.
  - The gate ADR was pressure-tested (6th sprint); the 3-part DoD held (10th sprint).
* **What Could Be Improved?**
  - The `xp` objective uses fixed v0 settings (next-GW, fpl); exposing `--type`/`--next` for it is a backlog item.
  - The squad display still shows the points column regardless of objective — a per-objective score column would be clearer (backlog).
* **Lessons Learned?**
  - Keep the core generic and push the meaning to the edge — the same pattern (seams, resolver, now objective) keeps paying off.
  - A default that's a true no-op (`scores=None` → points) makes an extension safe — proven by the regression test.
  - Composability is earned: independent, tested pieces combine without extra work.
* **Action Items for Next Sprint (011):**
  - [ ] Consider: FBref xG/xA (player-level), 15-man squad / formations, or `--type`/`--next` for the xp objective.
  - [ ] Revisit data-dependent FPL work (form / attack-defence) once the season starts — check data first.
  - [ ] Keep pressure-testing ADR mechanisms + the 3-part DoD.

---

**Proposed follow-on (Sprint 011):** FBref xG/xA (player-level), 15-man squad / flexible
formations, or the data-dependent FPL work once the season starts.

**Completion Date:** 2026-08-02
**Final Notes:** The toolkit came together — value and xP now drive the squad
optimiser. From Tony's backlog review. Sprint outcome: **Successful** — 3/3 stories,
zero roll-over, DoD held.
