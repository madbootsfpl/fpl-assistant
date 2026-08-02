# Sprint 003: Fixtures & Difficulty

**Dates:** 2026-08-01 to 2026-08-02
**Status:** ✅ Complete
**Capacity:** ~3–4 working sessions
**Carried Over:** 2 technical tasks from Sprints 001–002 — both cleared first (see Carry-over below)

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
- [x] **Carry-over tasks cleared first** (FK enforcement + Handbook bump) — see below
- [x] Fixtures model + FDR approach agreed (ADR-004) before feature code
- [x] `refresh` also fetches and stores fixtures
- [x] Foreign-key enforcement enabled on the schema
- [x] `fdr` ranks teams by average upcoming fixture difficulty
- [x] `fixtures --team ARS` lists a team's upcoming matches
- [x] Tests cover fixtures ingestion and the FDR calculation
- [x] Handbook kept in step with each story (not a end-of-sprint sweep)

---

### ⏫ Carry-over — DO FIRST (before any feature story)

These two technical tasks slipped in **both** Sprint 001 and Sprint 002. To stop a
third slip they are gated at the **start** of Sprint 003 — US-010 onwards does not
begin until both are done.

- [x] **Enable SQLite foreign-key enforcement** — `PRAGMA foreign_keys = ON` in
  `Storage`; verified full suite still passes (`0795c15`).
- [x] **Handbook bump for Sprint 002 work** — added chapters 20 (CLIs) and 21
  (Analytics) with real Sprint 002 code + badges (`9e143eb`).

> **Definition of Done (this sprint):** a feature story isn't "done" until the Handbook
> is updated for anything new it introduced. Handbook updates happen *inside* the story,
> per the Sprint 002 retro lesson.

---

### 📋 Sprint Backlog

#### User Stories & Features
| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-009 | Agree fixtures data model + FDR approach (ADR-004) | Critical | ✅ Complete | 0.5 session |
| US-010 | Fixtures ingestion (endpoint, `Fixture` model, table, extend `refresh`) | High | ✅ Complete | 1 session |
| US-011 | First FDR view — teams ranked by upcoming difficulty (`fdr` command) | High | ✅ Complete | 1 session |
| US-012 | Fixtures listing (`fixtures --team ARS`) | Medium | ✅ Complete | 0.5 session |

#### Technical Tasks & Maintenance
- [x] ADR-004 (fixtures/FDR) recorded + added to the ADR index - _Done (US-009)_
- [x] Update Architecture doc: fixtures entity + FK enforcement - _Done (US-009)_
- [x] Update `README.md` with the new commands - _Done (US-012)_

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

#### Session 1 - 2026-08-01 (Carry-over cleared)
* **Completed:** Both long-carried tasks done FIRST, per plan: SQLite FK enforcement (`PRAGMA foreign_keys = ON` + test, `0795c15`); Handbook chapters 20 (CLIs) and 21 (Analytics) from real Sprint 002 code (`9e143eb`). 30 tests passing.
* **Issues / Blockers:** None. The two tasks that slipped both prior sprints are now cleared before any feature work.
* **Next Steps:** US-009 — record ADR-004 (fixtures model + FDR approach) and design the fixtures schema.

#### Session 2 - 2026-08-01 (US-009: ADR-004 + fixtures schema)
* **Completed:** Recorded ADR-004 (FPL difficulty; derive-upcoming, no events table; 8-field fixtures schema) + added to the ADR index. Documented the `fixtures` entity in Architecture §6 (two FKs to teams). US-009 **complete** — no feature code yet.
* **Issues / Blockers:** None.
* **Next Steps:** US-010 — fixtures ingestion (Fixture model, table, extend refresh).

#### Session 3 - 2026-08-01 (US-010: fixtures ingestion)
* **Completed:** Added the fixtures path through every layer — `client.get_fixtures()` (with a shared `_get_json` helper, DRY refactor), `Fixture` model + `from_api`, `fixtures` table (two FKs to teams) + `save_fixtures`/`count_fixtures`, and extended `refresh` to store teams → players → fixtures (returns a 3-tuple now). 4 new tests (34 total). Verified live: refresh stored 564 players, 20 teams and **380 fixtures**; FK enforcement on fixtures tested. US-010 **complete**.
* **Issues / Blockers:** None. Handbook DoD considered — US-010 reused existing chapters (APIs/JSON/SQLite/models); it introduced no new *tool/topic*, so no new chapter needed.
* **Next Steps:** US-011 — first FDR view (per-team upcoming difficulty, `fdr` command).

#### Session 4 - 2026-08-01 (US-011: first FDR view)
* **Completed:** First *aggregating* analytics — `storage.get_upcoming_fixtures()` (unfinished, joined to team names), `analytics/fdr.py` `team_fdr()` (per-team average difficulty from each team's own perspective, ranked easiest-first), `ui/fdr.py` renderer, and the `fdr --next N` command. 8 new tests (42 total). Handbook DoD met: updated Chapter 21 (Analytics) with the aggregate/perspective concepts + FDR example. Verified live: `fdr --next 5` ranks teams (LIV easiest, 2.6) with next opponents. US-011 **complete**.
* **Issues / Blockers:** None.
* **Next Steps:** US-012 — fixtures listing (`fixtures --team ARS`), the last Sprint 003 story.

#### Session 5 - 2026-08-01 (US-012: fixtures listing)
* **Completed:** `fixtures --team ARS` — extended `get_upcoming_fixtures(team=...)` (SQL filter), added `team_schedule()` + a shared `_view()` perspective helper (refactored `team_fdr` to reuse it — FDR tests stayed green), `ui/fixtures.py` renderer, and the command. Updated README with all commands. 4 new tests (46 total). US-012 **complete** — all four Sprint 003 feature stories done.
* **Issues / Blockers:** None. Handbook DoD met: US-012 reused documented concepts (SQL filter, perspective in Ch21), no new chapter needed.
* **Next Steps:** Sprint 003 review & retrospective.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** Both carry-over tasks (FK enforcement, Handbook chapters 20/21) + all four stories — US-009 (ADR-004), US-010 (fixtures ingestion), US-011 (FDR view), US-012 (fixtures listing) — plus a `--help` discoverability fix found in testing. The app now has two data entities, two analytics metrics, and six commands. Tests grew 29 → 46, all offline.
* **Carried Forward:** None. And no tech task slipped — the carry-over gate worked.
* **Key Artifacts / Decisions:** ADR-004 (fixtures/FDR); `fixtures` entity with two FKs + enforcement; `src/ingest.py` extended; `src/analytics/fdr.py` (first aggregating metric); commits `0795c15`→`b81a057`.

#### Retrospective
* **What Went Well?**
  - The carry-over gate worked — the two tasks that slipped in Sprints 001 *and* 002 were done first, and nothing slipped this sprint.
  - Adding a whole new entity (fixtures) was *boring* — it flowed through each layer exactly like players. The strongest evidence yet that the layering pays off.
  - DRY refactors (`_get_json`, `_view`) were chosen and paid off immediately; tests proved the FDR refactor safe (identical output, green suite).
  - The storage-vs-analytics boundary held again: filter/query in storage, compute in analytics.
  - Handbook stayed in step (Ch21 updated inside US-011), per the DoD.
* **What Could Be Improved?**
  - Manual testing caught a `--help` discoverability gap that automated tests couldn't — a reminder to smoke-test the *experience*, not just behaviour.
  - `git add -A` once swept in `.claude/settings.local.json`; caught by reviewing `git status` before commit, now gitignored. Keep that discipline.
* **Lessons Learned?**
  - A well-layered design makes a new entity predictable to add — the boundaries did the thinking.
  - **Tests verify behaviour; manual testing verifies experience** (discoverability, help text, feel). Both are needed.
  - Refactor confidence comes from tests — the `_view` extraction was safe *because* the FDR tests would have caught a regression.
  - Gating carried tasks at sprint start (with a Definition of Done) actually stops slippage.
* **Action Items for Next Sprint (004):**
  - [ ] Choose direction: custom FDR (Attack/Defense split, home/away weighting) **or** begin the xP engine.
  - [ ] Add a short per-sprint manual smoke-test checklist (does the UX reveal the new features?).
  - [ ] Keep the staging discipline — review `git status` before every commit.

---

**Proposed follow-on (Sprint 004):** custom FDR (Attack/Defense split, home/away), or begin the xP engine.

**Completion Date:** 2026-08-02
**Final Notes:** The app gained a second data source (fixtures) and its first aggregating analytics (FDR) — decisions can now weigh *who a team plays*, not just past points. Sprint outcome: **Successful** — 4/4 stories, carry-over cleared, zero roll-over.
