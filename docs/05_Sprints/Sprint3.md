# Sprint 003: Fixtures & Difficulty

**Dates:** TBC
**Status:** Planned
**Capacity:** ~3–4 working sessions
**Carried Over:** 2 technical tasks from Sprints 001–002 (see Carry-over below)

---

### 🧭 Architecturally, what's new

Every story so far has revolved around **one entity: players**. Sprint 003 introduces
a **second: fixtures** — matches, from a new FPL endpoint (`/fixtures/`). The same
layered pattern applies for the new entity:

```
/fixtures/ → client → Fixture.from_api → storage (new table) → analytics (FDR) → display → CLI (fdr / fixtures)
```

Two firsts worth naming:

1. **Real relationships → foreign keys become meaningful.** A fixture references *two*
   teams (home and away). That's exactly the case FK enforcement protects — so this is
   finally the right moment to turn on `PRAGMA foreign_keys = ON`.
2. **Aggregating analytics.** Points-per-£m was *per row*. Fixture Difficulty is *per
   team, across several fixtures* — the analytics layer learns to summarise a group,
   not just transform a row.

**Scope discipline:** the Roadmap eventually wants a *custom* FDR (separate Attack /
Defense, home/away weighting). Sprint 003 does **not** build that. It ships a first,
honest FDR using **FPL's own difficulty numbers** — the simplest thing that gives
insight. Custom FDR is a later sprint.

---

### 🎯 Sprint Goal

**Objective:** Bring fixtures into the app and give the first fixture-based insight —
rank teams by how easy or hard their upcoming matches are, so player decisions can
start accounting for *who they play*, not just past points.

#### Success Criteria
- [ ] **Carry-over tasks cleared first** (FK enforcement + Handbook bump) — see below
- [ ] Fixtures model + FDR approach agreed (ADR-004) before feature code
- [ ] `refresh` also fetches and stores fixtures
- [ ] Foreign-key enforcement enabled on the schema
- [ ] `fdr` ranks teams by average upcoming fixture difficulty
- [ ] `fixtures --team ARS` lists a team's upcoming matches
- [ ] Tests cover fixtures ingestion and the FDR calculation
- [ ] Handbook kept in step with each story (not a end-of-sprint sweep)

---

### ⏫ Carry-over — DO FIRST (before any feature story)

These two technical tasks slipped in **both** Sprint 001 and Sprint 002. To stop a
third slip they are gated at the **start** of Sprint 003 — US-010 onwards does not
begin until both are done.

- [ ] **Enable SQLite foreign-key enforcement** — `PRAGMA foreign_keys = ON` in
  `Storage`; verify the full suite still passes (save order is already teams-first).
- [ ] **Handbook bump for Sprint 002 work** — document the CLI and analytics that are
  now used (new chapters or additions), and update the relevant badges.

> **Definition of Done (this sprint):** a feature story isn't "done" until the Handbook
> is updated for anything new it introduced. Handbook updates happen *inside* the story,
> per the Sprint 002 retro lesson.

---

### 📋 Sprint Backlog

#### User Stories & Features
| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-009 | Agree fixtures data model + FDR approach (ADR-004) | Critical | Planned | 0.5 session |
| US-010 | Fixtures ingestion (endpoint, `Fixture` model, table, extend `refresh`) | High | Planned | 1 session |
| US-011 | First FDR view — teams ranked by upcoming difficulty (`fdr` command) | High | Planned | 1 session |
| US-012 | Fixtures listing (`fixtures --team ARS`) | Medium | Planned | 0.5 session |

#### Technical Tasks & Maintenance
- [ ] ADR-004 (fixtures/FDR) recorded + added to the ADR index - _Planned_
- [ ] Update Architecture doc: fixtures entity + FK enforcement - _Planned_
- [ ] Update `README.md` with the new commands - _Planned_

_(FK enforcement and the Handbook bump are tracked under Carry-over above, not here,
so they can't hide in the tech-task list again.)_

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| • Fixtures from `/fixtures/` | • Live / in-play data |
| • FDR using **FPL's own** difficulty | • Custom Attack/Defense FDR, home/away weighting → later |
| • "Upcoming" = unfinished fixtures | • Double / blank gameweek handling → later |
| • Per-team average difficulty over next N | • xG/xA, form, xP |

**External Dependencies:**
- [ ] FPL `/fixtures/` endpoint
- [ ] Sprint 002 storage/models/CLI (done); Python stdlib only

---

### ⚠️ Risks & Mitigations

| Risk | Impact (High/Med/Low) | Mitigation Strategy |
|---|---|---|
| Enabling FKs breaks existing saves | Med | Save order is already teams-first; add a test; enable + verify full suite (carry-over, done first) |
| Fixtures with no gameweek yet (null `event`) | Med | Treat as not-upcoming; handle null explicitly |
| Difficulty is per-side (home vs away) | Med | Compute from the team's own perspective (home → team_h_difficulty, else team_a) |
| FDR scope balloons into a custom model | Med | v1 uses FPL difficulty only; custom FDR is a later sprint |

---

### 🗝️ Gating decision (US-009 → ADR-004)

Two things to settle before building. Both **confirmed** during planning:

1. **FDR source:** use **FPL's own `team_h/a_difficulty`** for v1 — ships insight now;
   a custom rating is a later sprint.
2. **"Upcoming" without a gameweek table:** derive upcoming from **unfinished fixtures
   ordered by gameweek**, rather than storing a separate `events`/gameweeks table yet.

Recorded as **ADR-004** at sprint start.

---

### 📝 Session Progress Log

#### Session 1 - [Date]
* **Completed:**
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

**Proposed follow-on (Sprint 004):** custom FDR (Attack/Defense split, home/away), or begin the xP engine.

**Completion Date:** [YYYY-MM-DD]
**Final Notes:**
