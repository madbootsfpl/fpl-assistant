# Sprint 001: Foundations & First Data Slice

**Dates:** TBC (proposed 1–2 week / 3–4 session sprint)
**Status:** Planned
**Capacity:** ~3–4 working sessions
**Carried Over:** None (first sprint)

---

### 🎯 Sprint Goal

**Objective:** Establish the project's technical foundation and prove one complete vertical slice — connect to the official FPL API, persist player data locally, and display it — so that every later analytics feature has a working data pipeline to build on.

#### Success Criteria
- [ ] Architecture document (v0.1) exists and is agreed before feature code is written
- [ ] App fetches live data from the FPL `bootstrap-static` endpoint
- [ ] Player data is stored locally (SQLite) rather than re-fetched every run
- [ ] A basic player table can be displayed to the user
- [ ] Repo hygiene in place (clean git tree, tests run, README updated)
- [ ] Developer can explain how the data flows end-to-end

---

### 📋 Sprint Backlog

#### User Stories & Features
| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-001 | Agree architecture v0.1 (module layout, data flow, SQLite schema) | Critical | Planned | 1 session |
| US-002 | FPL API client — fetch `bootstrap-static` player data | High | Planned | 1 session |
| US-003 | Persist players to local SQLite cache | High | Planned | 0.5 session |
| US-004 | Display a basic player table (name, team, position, price, points) | Medium | Planned | 0.5 session |

#### Technical Tasks & Maintenance
- [ ] Commit the pending docs reorg (deleted root `PROJECT_STATUS.md`, new `docs/00_Project/` copy, untracked `07_Templates/`) - _Owner: Claude / Planned_
- [ ] Confirm venv + `requirements.txt` (add `requests`, `pytest`) - _Planned_
- [ ] Add first `pytest` test for the API client (against a saved sample response) - _Planned_
- [ ] Update `README.md` with run instructions - _Planned_
- [ ] Record ADR-001 in `06_Decisions/` for the two open Roadmap questions (internal-tool vs multi-user; UI approach) - _Planned_

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| • Architecture v0.1 doc | • Any analytics (xG, FDR, xP) → Roadmap Phase 2 |
| • Read-only static FPL endpoint (`bootstrap-static`) | • User-auth endpoints (`/my-team/`) → later in Phase 1 |
| • SQLite storage of players | • Fixtures / historical backfill → later Sprint |
| • Minimal player table display | • Points-per-£m, search, filter → next Sprint |
| • Basic tests + README | • Web UI framework / React → deferred |

**External Dependencies:**
- [ ] Official FPL API (`https://fantasy.premierleague.com/api/bootstrap-static/`) availability
- [ ] Python packages: `requests`, `pytest` (and stdlib `sqlite3`)

---

### ⚠️ Risks & Mitigations

| Risk | Impact (High/Med/Low) | Mitigation Strategy |
|---|---|---|
| Building features before architecture is agreed | High | US-001 gates all other stories; no feature code until v0.1 doc approved |
| FPL API rate-limiting / 429s | Med | Cache to SQLite; save a sample response for tests to avoid live calls |
| FPL API schema changes / undocumented fields | Med | Pin to `bootstrap-static` only; map a small explicit set of fields |
| Scope creep (journal lists 8 items) | Med | Hard-limit to 4 stories; defer search/filter/PPM to Sprint 002 |
| Over-engineering vs "keep it simple" | Low | Simplest working slice; no ORM, no web framework yet |

---

### 📝 Session Progress Log

#### Session 1 - [Date]
* **Completed:**
* **Issues / Blockers:**
* **Next Steps:**

#### Session 2 - [Date]
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

**Proposed follow-on (Sprint 002):** search, filter, Points-per-£m calculation, and manual data refresh — the remaining items from the Session 1 journal's draft list.

**Completion Date:** [YYYY-MM-DD]
**Final Notes:**
