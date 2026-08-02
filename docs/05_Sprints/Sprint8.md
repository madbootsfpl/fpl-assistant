# Sprint 008: Squad Selector — Include / Exclude

**Dates:** TBC
**Status:** Planned
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
- [ ] Include/exclude approach agreed (ADR-009) before feature code
- [ ] `select_squad` accepts include/exclude and fixes those picks (in / out)
- [ ] Names resolve to players; ambiguous names (e.g. "Wilson") are reported with candidates and can be disambiguated
- [ ] `squad --include X --exclude Y` builds the XI around the choices; forced picks are marked
- [ ] Impossible choices (conflict, over-budget, too many for a position) are reported clearly, not crashed
- [ ] Tests cover force-in, force-out, ambiguity, conflict, and infeasible-forced
- [ ] **Manual smoke test** run before the sprint is closed (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-027 | Agree include/exclude approach (ADR-009): name resolution + disambiguation, fixed picks, validation, infeasibility | Critical | Planned | 0.5 session |
| US-028 | Extend optimiser — `select_squad(include, exclude)` fixes picks; a `resolve_players(players, names)` helper (ambiguous / not-found) | High | Planned | 1 session |
| US-029 | `squad --include … --exclude …` command + mark forced picks + Handbook/README | High | Planned | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-009 recorded + added to the ADR index - _Planned_
- [ ] Update Architecture doc if needed (name-resolution note) - _Planned_
- [ ] Update `README.md` with `squad --include/--exclude` - _Planned_

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

#### Session 1 - [Date]
* **Completed:**
* **Manual smoke test:**
* **Docs touched:**
* **Issues / Blockers:**
* **Next Steps:**

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:**
* **Carried Forward:**
* **Key Artifacts / Decisions:**

#### Retrospective
* **What Went Well?**
* **What Could Be Improved?**
* **Lessons Learned:**
* **Action Items for Next Sprint:**

---

**Proposed follow-on (Sprint 009):** 15-man squad / flexible formations / xP-based
objective (backlog), plus the deferred data-dependent work once the season starts.

**Completion Date:** [YYYY-MM-DD]
**Final Notes:**
