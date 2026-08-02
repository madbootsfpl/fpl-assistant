# Sprint 008: Squad Selector — Include / Exclude

**Dates:** 2026-08-02
**Status:** ✅ Complete
**Capacity:** ~2–3 working sessions (a focused extension of the optimiser)
**Carried Over:** None (Sprint 007 closed clean)

---

### 🔎 Data verified at planning (per the Sprint 004 lesson)

Checked live `bootstrap-static`: the selector's inputs (`total_points`, `now_cost`,
`element_type`, `team`, `web_name`) are all 564/564 populated — no new data needed.
**Key finding:** `web_name` is **not unique** — 14 names are shared by more than one
player (e.g. "Wilson" ×3). So `--include Wilson` is ambiguous, and name resolution
must handle that. Still blocked (preseason): `form` (0/564) and attack/defence
strengths (0/20).

This sprint is **Tony's Sprint 007 idea**: pick the best XI *around* the user's choices.

---

### 🧭 Architecturally, what's new

Two small additions, both contained:

1. **Fixed decisions in the ILP.** "Must include" and "must exclude" are the simplest
   possible constraints — force `pick[p] = 1` for a favourite, `pick[p] = 0` for a
   dislike, then solve as normal. The solver builds the optimal XI around them.
2. **Name resolution** — a new step that turns user-typed names into player ids,
   handling the 14 ambiguous `web_name`s (input parsing/validation at the edge).

```
--include Haaland  --exclude Salah
        │ resolve names → ids (handle ambiguous / not-found)
        ▼
select_squad(players, budget, include_ids, exclude_ids)
        │  pick[included] = 1,  pick[excluded] = 0,  then maximise as before
        ▼
the optimal XI built around the user's choices
```

---

### 🎯 Sprint Goal

**Objective:** Let the user force players **in** (favourites) or **out** (dislikes),
and have the optimiser build the best legal XI around those choices — reporting
clearly when a name is ambiguous or the choices make a squad impossible.

#### Success Criteria
- [x] Include/exclude approach agreed (ADR-009) before feature code
- [x] `select_squad` accepts include/exclude and fixes those picks (in / out)
- [x] Names resolve to players; ambiguous names (e.g. "Wilson") are reported with candidates and can be disambiguated
- [x] `squad --include X --exclude Y` builds the XI around the choices; forced picks are marked
- [x] Impossible choices (conflict, over-budget, too many for a position) are reported clearly, not crashed
- [x] Tests cover force-in, force-out, ambiguity, conflict, and infeasible-forced
- [x] **Manual smoke test** run before the sprint is closed (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-027 | Agree include/exclude approach (ADR-009): name resolution + disambiguation, fixed picks, validation, infeasibility | Critical | ✅ Complete | 0.5 session |
| US-028 | Extend optimiser — `select_squad(include, exclude)` fixes picks; a `resolve_players(players, names)` helper (ambiguous / not-found) | High | ✅ Complete | 1 session |
| US-029 | `squad --include … --exclude …` command + mark forced picks + Handbook/README | High | ✅ Complete | 1 session |

#### Technical Tasks & Maintenance
- [x] ADR-009 recorded + added to the ADR index - _Done (US-027)_
- [x] Update Architecture doc if needed (name-resolution note) - _Done (US-027)_
- [x] Update `README.md` with `squad --include/--exclude` - _Done (US-029)_

---

### ✅ Definition of Done (this sprint)

Same 3-part DoD that has held for seven sprints — a story isn't done until:
1. **Automated tests pass** (and cover the new logic).
2. **Manual smoke test done** — run the real command, eyeball the output, check `--help`.
3. **Documentation updated & checked** — Handbook, Architecture, ADR + index, README,
   sprint board + PROJECT_STATUS, as applicable (Charter Documentation Rules).

A "smoke test" + "docs touched" note goes in the session log for each feature story.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Force players in/out by name | Partial / fuzzy name matching (backlog) |
| Disambiguate shared names | Forcing by position/club counts |
| Reuse the tested ILP optimiser | 15-man squad / flexible formations (backlog) |
| Clear errors (ambiguous, conflict, infeasible) | xP-based objective (backlog) |

**External Dependencies:**
- [ ] Existing players/teams data + PuLP (no new fetch, schema, or dependency)

---

### ⚠️ Risks & Mitigations

| Risk | Impact (High/Med/Low) | Mitigation Strategy |
|---|---|---|
| Ambiguous names (14 shared `web_name`s) | High | Resolve exactly; if >1 match, list candidates (name + team) and require disambiguation |
| Forcing too many for a position (e.g. 2 GK) or over budget | Med | The ILP returns infeasible; report a clear message |
| Include + exclude the same player | Med | Detect the conflict up front and error |
| Reuses tested optimiser | Low | Extend `select_squad`; full suite stays green |

---

### 🗝️ Gating decision (US-027 → ADR-009)

Settle before building (and pressure-test with a worked example, per the Sprint 006/007 lesson):
1. **Name matching** — exact `web_name` (case-insensitive). Recommended over partial
   matching (partial risks forcing the *wrong* player).
2. **Disambiguation** — for the 14 shared names, a `Name:TEAM` form (e.g. `Wilson:NFO`);
   otherwise list candidates and ask the user to be specific.
3. **Validation** — conflict (in + out), over-budget forced set, too many for a
   position → clear errors / infeasible message.
4. **Output** — mark which players in the XI were forced in.

---

### 📝 Session Progress Log

#### Session 1 - 2026-08-02 (US-027: ADR-009 — include/exclude design)
* **Completed:** Recorded ADR-009: forced picks (`pick=1`/`0`); exact case-insensitive `web_name` matching with a `Name:TEAM` form for the 14 shared names; validation (not-found / ambiguous / include-exclude conflict pre-checks; formation & budget violations reported as the solver's Infeasible). **Pressure-tested with worked examples** (2 GKs → infeasible; £13M force cascades budget; exclude top scorer; Wilson ×3 → candidates listed) — per the Sprint 006/007 lesson. Added to ADR index; Architecture §4 note + changelog. US-027 **complete** — no feature code.
* **Manual smoke test:** N/A (docs-only gate story).
* **Docs touched:** ADR-009 (new) + index, Architecture §4/changelog, Sprint8 board, PROJECT_STATUS.
* **Issues / Blockers:** None. (Data verified at planning surfaced the non-unique web_name; formulation pressure-tested.)
* **Next Steps:** US-028 — extend the optimiser (`select_squad(include, exclude)`) + a name resolver.

#### Session 2 - 2026-08-02 (US-028: optimiser + resolver)
* **Completed:** Extended `select_squad(..., include_ids, exclude_ids)` — forced picks (`pick=1`/`0`) + a `forced` flag on selected players. Added `resolve_players(players, names)` — exact `web_name` (case-insensitive) with `Name:TEAM` disambiguation; returns (ids, errors) for not-found / ambiguous. Handbook Ch22 gains a forcing-choices section. 7 new tests (92 total). US-028 **complete** — command is US-029.
* **Manual smoke test:** ✅ Excluded B.Fernandes + force-included Garner on real data → XI rebuilt around both (Garner marked forced), 1991 pts / £78.0m; resolution returned no errors.
* **Docs touched:** Handbook Ch22, Sprint8 board, PROJECT_STATUS. (Architecture covered in US-027.)
* **Issues / Blockers:** None.
* **Next Steps:** US-029 — the `squad --include … --exclude …` command.

#### Session 3 - 2026-08-02 (US-029: the include/exclude command)
* **Completed:** `squad --include … --exclude …` — the handler resolves names → ids, pre-checks the include/exclude conflict (clear message with names), prints resolver errors or solves + displays. `render_squad` marks forced picks (`*` + note). Added to Ch20/README. 3 tests (parse lists + defaults; render forced marker; 95 total). US-029 **complete** — all Sprint 008 stories done.
* **Manual smoke test:** ✅ `squad --include Garner --exclude B.Fernandes` → XI rebuilt, Garner marked `*` (1991 pts / £78.0m); `squad --include Wilson` → lists the 3 Wilsons with the Name:TEAM hint; `--help` shows the options.
* **Docs touched:** Handbook Ch20, README, Sprint8 board, PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** Sprint 008 review & retrospective.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-027 (ADR-009), US-028 (optimiser forced picks + name resolver), US-029 (the `squad --include/--exclude` command). The tool now builds the optimal XI *around the user's chosen players*, and handles ambiguous names honestly. Tests grew 85 → 95. No new data or dependency.
* **Carried Forward:** None. Backlog unchanged (15-man squad, flexible formations, xP objective, PuLP-4.0 migration, fuzzy matching).
* **Key Artifacts / Decisions:** ADR-009 (include/exclude + `Name:TEAM` resolution, with worked examples); `resolve_players`; forced-pick flag; commits `2f86194`→`438658e`.

#### Retrospective
* **What Went Well?**
  - **Tony's Sprint 007 idea shipped** — from a retro note to a working feature.
  - **The data check pointed at the real work.** Forcing picks was trivial (6 lines); the effort was name resolution — which the plan-time `web_name` uniqueness check had already flagged.
  - The gate story pressure-tested ADR-009 with worked examples (4th sprint running) — no design flaw slipped.
  - "Resolve at the edge, then optimise" kept the solver clean; the solver validated the forced set for free.
  - The 3-part DoD held (8th sprint).
* **What Could Be Improved?**
  - `Name:TEAM` is a little verbose, and multi-word names need shell quoting — usable, but fuzzy matching (backlog) would be friendlier.
  - Objective is still last-season points and the formation is fixed — obvious next refinements.
* **Lessons Learned?**
  - Verify data at planning and it tells you *where the effort will go* — here, the input, not the algorithm.
  - Validate at the boundary (resolve names first) so the core stays simple.
  - In an ILP, "must include / exclude" are the simplest constraints, and the solver checks feasibility for free.
* **Action Items for Next Sprint (009):**
  - [ ] Consider: 15-man squad, flexible formations, xP-based objective, or fuzzy name matching (backlog).
  - [ ] Revisit data-dependent work (form/expected-minutes xP, Attack/Defence FDR) once the season starts — check data first.
  - [ ] Keep pressure-testing ADR mechanisms + the 3-part DoD.

---

**Proposed follow-on (Sprint 009):** 15-man squad / flexible formations / xP-based
objective (backlog), plus the deferred data-dependent work once the season starts.

**Completion Date:** 2026-08-02
**Final Notes:** Tony's idea, shipped: the assistant now recommends the optimal XI
*around your picks*. The plan-time data check again pointed at the real work (name
resolution, not the optimisation). Sprint outcome: **Successful** — 3/3 stories, zero
roll-over, DoD held.
