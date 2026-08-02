# Sprint 006: Multi-week xP

**Dates:** TBC
**Status:** Planned
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

**Objective:** Rank players by expected points **over the next N fixtures**, not just
the next one — so decisions can weigh a *run* of games.

#### Success Criteria
- [ ] Multi-week xP approach agreed (ADR-007) before feature code
- [ ] xP summed correctly over a team's next N fixtures (each fixture's multiplier applied)
- [ ] `xp --next N` works; `--next 1` reproduces today's single-GW behaviour
- [ ] Output is clearly labelled as a total over N fixtures; `ep_next` handled honestly at N>1
- [ ] Tests cover the multi-week sum (incl. a team with fewer than N fixtures)
- [ ] **Manual smoke test** run before the sprint is closed (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-021 | Agree multi-week xP (ADR-007): sum over next N fixtures; horizon = next N *fixtures* (DGW/BGW alignment deferred); `ep_next` comparable only at N=1; default N | Critical | Planned | 0.5 session |
| US-022 | Multi-week xP analytics — next-N difficulties per team, sum per-fixture xP | High | Planned | 1 session |
| US-023 | `xp --next N` command + label the horizon + Handbook/README | High | Planned | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-007 recorded + added to the ADR index - _Planned_
- [ ] Update Architecture doc (if the xP note needs the horizon) - _Planned_
- [ ] Update `README.md` with `xp --next` - _Planned_

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

**Proposed follow-on (Sprint 007):** richer xP (form + expected minutes) and/or the
Attack/Defence FDR split, once the season populates them.

**Completion Date:** [YYYY-MM-DD]
**Final Notes:**
