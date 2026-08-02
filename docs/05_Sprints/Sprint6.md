# Sprint 006: Multi-week xP

**Dates:** 2026-08-02
**Status:** ✅ Complete
**Capacity:** ~2–3 working sessions (a focused extension of xP)
**Carried Over:** None (Sprint 005 closed clean)

---

### 🔎 Data verified at planning (per the Sprint 004 lesson)

Checked live `bootstrap-static`: `points_per_game` (400/564), fixtures + FDR are all
present — multi-week xP needs no new data. **Still blocked (preseason):** `form`
(0/564) and attack/defence strengths (0/20), so richer xP and the Attack/Defence FDR
split remain deferred.

This sprint follows a **planning-time reflection from Sprint 005** ("should we look at
xP across a number of fixtures?") — a data-supported next step.

---

### 🧭 Architecturally, what's new — a horizon

xP v0 (Sprint 005) looked at a player's *next single* fixture. Sprint 006 extends it to
a **horizon** — the sum of expected points across the team's next N fixtures:

```
v0 (next GW):   xP = points_per_game × multiplier(next fixture difficulty)
multi-week:     xP = points_per_game × Σ multiplier(difficulty_i)   over the next N fixtures
```

A subtle bonus: because it counts *fixtures*, a team with **two games in the window**
(a double gameweek) naturally scores higher — the first hint of DGW-awareness, without
building full gameweek logic yet. It reuses everything: the xP calc, the FDR `_view`
seam (custom/fpl), and the fixtures data.

---

### 🎯 Sprint Goal

**Objective:** Rank players by expected points **over the next N gameweeks**, not just
the next one — so decisions can weigh a *run* of games (and double gameweeks).

#### Success Criteria
- [x] Multi-week xP approach agreed (ADR-007) before feature code
- [x] xP summed correctly over a team's fixtures in the next N gameweeks (DGW-aware)
- [x] `xp --next N` works; `--next 1` reproduces today's single-GW behaviour
- [x] Output is clearly labelled as a total over N gameweeks; `ep_next` hidden at N>1
- [x] Tests cover the multi-week sum (incl. a double gameweek and a blank)
- [x] **Manual smoke test** run before the sprint is closed (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-021 | Agree multi-week xP (ADR-007): sum over next N fixtures; horizon = next N *fixtures* (DGW/BGW alignment deferred); `ep_next` comparable only at N=1; default N | Critical | ✅ Complete | 0.5 session |
| US-022 | Multi-week xP analytics — next-N difficulties per team, sum per-fixture xP | High | ✅ Complete | 1 session |
| US-023 | `xp --next N` command + label the horizon + Handbook/README | High | ✅ Complete | 1 session |

#### Technical Tasks & Maintenance
- [x] ADR-007 recorded + added to the ADR index - _Done (US-021)_
- [x] Update Architecture doc (if the xP note needs the horizon) - _Done (US-021)_
- [x] Update `README.md` with `xp --next` - _Done (US-023)_

---

### ✅ Definition of Done (this sprint)

Same 3-part DoD that has held for five sprints — a story isn't done until:
1. **Automated tests pass** (and cover the new logic).
2. **Manual smoke test done** — run the real command, eyeball the output, check `--help`.
3. **Documentation updated & checked** — Handbook, Architecture, ADR + index, README,
   sprint board + PROJECT_STATUS, as applicable (Charter Documentation Rules).

A "smoke test" + "docs touched" note goes in the session log for each feature story.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Sum xP over the next N fixtures | Recent form / expected minutes (blocked) |
| DGW captured by fixture *count* | True DGW/BGW gameweek alignment |
| `xp --next N` (default 1 = today's behaviour) | Attack/Defence FDR (blocked) |
| Reuse xP, FDR, fixtures | Transfer / captain recommendations |

**External Dependencies:**
- [ ] `points_per_game` + fixtures + FDR (all present, already fetched)
- [ ] Sprint 005 xP (done); Python stdlib only

---

### ⚠️ Risks & Mitigations

| Risk | Impact (High/Med/Low) | Mitigation Strategy |
|---|---|---|
| Big sums (≈ N × ppg) look odd | Med | Label the column/footer clearly as "total over next N fixtures" |
| `ep_next` (next GW) not comparable to an N-fixture sum | Med | Settle in ADR-007: show `ep_next` only at N=1, or label it "next GW"; decide |
| A team has fewer than N upcoming fixtures (season end) | Low | Sum over what's available; note the actual count shown |
| Reuses tested xP/FDR | Low | Extend, don't rewrite; full suite stays green |

---

### 🗝️ Gating decision (US-021 → ADR-007)

Settle before building:
1. **Aggregation** — **sum** xP over the next N fixtures (total expected points), not average.
2. **Horizon unit** — next N *fixtures* (captures DGW by count); true gameweek alignment deferred.
3. **`ep_next` comparability** — meaningful only at N=1; decide how to present at N>1.
4. **Default N** — `--next` default 1, preserving today's single-GW behaviour.

---

### 📝 Session Progress Log

#### Session 1 - 2026-08-02 (US-021: ADR-007 — multi-week xP design)
* **Completed:** Recorded ADR-007: xP over a horizon = **sum** of per-fixture xP over the next N *fixtures* (captures DGW by count; true DGW/BGW alignment deferred); `xp --next` defaults to 1 (today's behaviour); `ep_next` shown only at N=1 (not comparable to an N-fixture sum); short horizons sum over what's available. Added to ADR index; Architecture xP note + changelog updated. US-021 **complete** — no feature code.
* **Manual smoke test:** N/A (docs-only gate story).
* **Docs touched:** ADR-007 (new) + index, Architecture §6/changelog, Sprint6 board, PROJECT_STATUS.
* **Issues / Blockers:** None. (Data verified at planning.)
* **Next Steps:** US-022 — multi-week xP analytics (next-N difficulties per team, sum per-fixture xP).

#### Session 2 - 2026-08-02 (US-022: multi-week xP analytics)
* **Completed:** Extended `player_xp(..., horizon=N)` to sum per-fixture xP over the team's fixtures in the next N gameweeks (via `_horizon_difficulties`, reusing `_view`). **Caught and corrected an ADR-007 design flaw**: the horizon must be next N *gameweeks*, not *fixtures* — per-team fixture-count can't capture DGW (every team gets N). Amended ADR-007 + Architecture wording. 4 new tests incl. a double-gameweek test (75 total). US-022 **complete**.
* **Manual smoke test:** ✅ `player_xp` horizon 1 (games=1, xP 7.4) vs horizon 5 (games=5, xP 34.2) on real data.
* **Docs touched:** ADR-007 (corrected), Architecture note/changelog, Sprint6 goal/criteria, PROJECT_STATUS.
* **Issues / Blockers:** The ADR-007 mislabel — caught before building (per the "check assumptions" lesson), corrected in place.
* **Next Steps:** US-023 — the `xp --next N` command + label the horizon.

#### Session 3 - 2026-08-02 (US-023: the xp --next command)
* **Completed:** Added `xp --next N` (default 1); threaded `horizon` to `player_xp` + the renderer. `render_xp_table` gained a **Games** column and shows FPL's `ep_next` only at N=1 (hidden with an explaining note at N>1, per ADR-007). Updated the `--help` example, Ch20 command list, README. 4 tests updated/added (76 total). US-023 **complete** — all Sprint 006 stories done.
* **Manual smoke test:** ✅ `xp --next 1` (FPL shown, Games 1) vs `xp --next 5` (Games 5, xP ~34, FPL hidden). Rankings reorder by the run of fixtures.
* **Docs touched:** Handbook Ch20, README, cli `--help`, Sprint6 board, PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** Sprint 006 review & retrospective.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-021 (ADR-007), US-022 (multi-week analytics), US-023 (the `xp --next N` command). xP now sums over the next N gameweeks, is DGW-aware, and hides FPL's `ep_next` at N>1. Tests grew 73 → 76. This sprint came from a Sprint 005 reflection.
* **Carried Forward:** None. Form/expected-minutes xP and Attack/Defence FDR remain deferred (data-dependent).
* **Key Artifacts / Decisions:** ADR-007 (multi-week xP, corrected to a gameweek horizon); `player_xp(..., horizon=N)`; commits `ab423a4`→`7dae4ee`.

#### Retrospective
* **What Went Well?**
  - The sprint came from **Tony's own reflection** — direction driven by his instinct.
  - **A design flaw was caught before building.** ADR-007 first said "next N fixtures" (which can't capture DGW); working through US-022 exposed it and it was corrected to "next N gameweeks" — no wrong code shipped.
  - Honest presentation: FPL's `ep_next` shown only where it's comparable (N=1), hidden with a note otherwise.
  - Pure reuse again — the horizon threaded through tested xP/FDR seams.
  - The 3-part DoD held for every story.
* **What Could Be Improved?**
  - **A recorded decision isn't a verified one.** The ADR-007 flaw survived the gate story (US-021) and was only caught at implementation. A quick worked example when writing an ADR mechanism would have caught it earlier.
* **Lessons Learned?**
  - Pressure-test an ADR's *mechanism* against its *intent* (a worked example), not just the intent — "captures DGW" needed checking against "next N fixtures".
  - Catching a flaw before code is cheap; the discipline is to look.
  - Horizon design: a gameweek window (not a per-team fixture count) is what captures double/blank gameweeks.
* **Action Items for Next Sprint (007):**
  - [ ] Sanity-check each ADR mechanism with a worked example at write time.
  - [ ] Refine xP with `form` + expected minutes, or the Attack/Defence FDR split (both data-dependent — check first).
  - [ ] Keep verifying data at plan time + the 3-part DoD.

---

**Proposed follow-on (Sprint 007):** richer xP (form + expected minutes) and/or the
Attack/Defence FDR split, once the season populates them.

**Completion Date:** 2026-08-02
**Final Notes:** Tony's own idea, shipped: xP now weighs a *run* of games, and is
double-gameweek-aware. The standout was catching a flawed ADR before it became code.
Sprint outcome: **Successful** — 3/3 stories, zero roll-over, DoD held.
