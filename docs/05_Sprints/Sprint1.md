# Sprint 001: Foundations & First Data Slice

**Dates:** 2026-08-01 (single-day sprint across sessions 2–5)
**Status:** ✅ Complete
**Capacity:** ~3–4 working sessions
**Carried Over:** None (first sprint)

---

### 🎯 Sprint Goal

**Objective:** Establish the project's technical foundation and prove one complete vertical slice — connect to the official FPL API, persist player data locally, and display it — so that every later analytics feature has a working data pipeline to build on.

#### Success Criteria
- [x] Architecture document (v0.1) exists and is agreed before feature code is written
- [x] App fetches live data from the FPL `bootstrap-static` endpoint
- [x] Player data is stored locally (SQLite) rather than re-fetched every run
- [x] A basic player table can be displayed to the user
- [x] Repo hygiene in place (clean git tree, tests run, README updated)
- [x] Developer can explain how the data flows end-to-end _(self-assessed by Tony, 2026-08-01)_

---

### 📋 Sprint Backlog

#### User Stories & Features
| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-001 | Agree architecture v0.1 (module layout, data flow, SQLite schema) | Critical | ✅ Complete | 1 session |
| US-002 | FPL API client — fetch `bootstrap-static` player data | High | ✅ Complete | 1 session |
| US-003 | Persist players to local SQLite cache | High | ✅ Complete | 0.5 session |
| US-004 | Display a basic player table (name, team, position, price, points) | Medium | ✅ Complete | 0.5 session |

#### Technical Tasks & Maintenance
- [x] Commit the pending docs reorg (deleted root `PROJECT_STATUS.md`, new `docs/00_Project/` copy, untracked `07_Templates/`) - _Owner: Claude / Done (`5b53cef`)_
- [x] Confirm venv + `requirements.txt` (add `requests`, `pytest`) - _Done (US-002)_
- [x] Add first `pytest` test for the API client (against a saved sample response) - _Done (US-002)_
- [x] Update `README.md` with run instructions - _Done (US-002)_
- [x] Record ADR-001 and ADR-002 in `06_Decisions/` for the two open Roadmap questions (internal-tool vs multi-user; UI approach) - _Done (`d67c085`)_

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

#### Session 2 - 2026-08-01 (Planning & Architecture)
* **Completed:** Sprint 001 plan written; PROJECT_STATUS updated; Architecture v0.1 drafted and **agreed**; ADR-001 and ADR-002 recorded; journal/glossary updated; Developer Handbook created. US-001 **complete**.
* **Issues / Blockers:** None.
* **Next Steps:** Begin US-002 (FPL API client — fetch `bootstrap-static`).

_(Session 1 was environment setup, logged in the [Dev Journal](../01_Journal/FPL_Assistant_Dev_Journal_Session1.md) before this sprint began.)_

#### Session 3 - 2026-08-01 (US-002: FPL API client)
* **Completed:** Built `src/api/client.py` (`FplClient` + `FplApiError`) and `src/config.py`; added `requests`/`pytest` to `requirements.txt`; wrote first offline `pytest` (2 tests, passing) using a trimmed fixture; wired `app.py` to fetch and report counts; updated README with run instructions. Verified live: fetched 564 players across 20 teams. US-002 **complete**.
* **Issues / Blockers:** `src/api` existed as a stray empty file rather than a directory — replaced it with a proper package.
* **Next Steps:** US-003 (persist players to local SQLite).

#### Session 4 - 2026-08-01 (US-003: SQLite persistence)
* **Completed:** Added `Team`/`Player` dataclasses with `from_api()` mappers (position label + `now_cost/10` price); `src/storage.py` `Storage` class with upsert on FPL id and `data/fpl.db` (gitignored); wired `app.py` to fetch → map → store. 4 new tests (models + storage, incl. upsert idempotency), 6 passing total. Verified live: stored 564 players / 20 teams; ran twice, counts stayed constant (upsert works). US-003 **complete**.
* **Issues / Blockers:** None.
* **Next Steps:** US-004 (display a basic player table from the stored data).

#### Session 5 - 2026-08-01 (US-004: display player table)
* **Completed:** Added `src/ui/table.py` (`render_player_table`, pure formatting, top-20 default with truncation + footer); `get_players()` now LEFT JOINs teams for the short_name; wired `app.py` to print the table from the DB. 3 new tests (9 passing total). Verified live: full fetch → store → display slice prints an aligned top-20 table. US-004 **complete** — all four sprint stories done.
* **Issues / Blockers:** None. (Noted: live 2026-season data has several players sharing one team_id — a data quirk, not a code issue.)
* **Next Steps:** Sprint 001 review & retrospective; then Sprint 002 (search, filter, Points-per-£m, manual refresh).

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All four stories — US-001 (architecture v0.1 agreed), US-002 (FPL API client), US-003 (SQLite persistence), US-004 (player table). The complete fetch → store → display vertical slice runs live (`python app.py`: 564 players / 20 teams, top-20 table). 9 tests passing, all offline.
* **Carried Forward:** None. Full scope delivered.
* **Key Artifacts / Decisions:** Architecture v0.1; ADR-001 (single-user) & ADR-002 (console-first UI); Developer Handbook; code in `src/{api,models,ui}` + `src/storage.py`; commits `5b53cef`→`12e0860`.

#### Retrospective
* **What Went Well?**
  - Design-first paid off: agreeing the architecture and scope before coding kept the sprint to 4 tight stories with zero roll-over.
  - The layered design held up end-to-end — client/storage/display each stayed ignorant of the others, exactly as drawn in Architecture §3.
  - Tests are fast and offline (mocked HTTP + temp DBs), so no live API calls or rate-limit risk in CI.
  - Small, well-messaged commits — one story per commit — kept history readable.
  - Confirm-first (what/why/risks) before each story surfaced real decisions (mapping location, storage shape, row limit) instead of guessing.
* **What Could Be Improved?**
  - The sprint doc drifted from reality mid-way and needed a "sync with reality" pass — better to update status/checkboxes as work lands.
  - A stray `src/api` placeholder file (not a directory) briefly blocked the package layout — worth a quick scaffold sanity-check next time.
  - Dates started as "TBC"; setting them up front would have been cleaner.
* **Lessons Learned?**
  - Writing decisions down (ADRs) *before* coding made scope obvious and stopped the sprint ballooning.
  - Upsert-on-id gives idempotent refreshes — proven by running the app twice with unchanged counts.
  - Keeping the presentation layer pure (returns a string, no I/O) made it trivially testable and swap-able.
  - "Fetch once, read locally" is the reason the app works offline — the core value of separating fetch/store/display.
* **Action Items for Next Sprint (002):**
  - [ ] Build search, filter, Points-per-£m, and manual refresh (the deferred Session 1 journal items).
  - [ ] Bump Developer Handbook badges to 💻 for topics now genuinely used (APIs, JSON, SQLite, Testing).
  - [ ] Consider enabling SQLite foreign-key enforcement (currently team_id is unenforced).
  - [ ] Keep the sprint board in step with the work as it lands, not after.

---

**Proposed follow-on (Sprint 002):** search, filter, Points-per-£m calculation, and manual data refresh — the remaining items from the Session 1 journal's draft list.

**Completion Date:** 2026-08-01
**Final Notes:** First working slice of the project. Foundation (architecture, decisions, layered code, tests, handbook) is in place for analytics work to build on. Sprint outcome: **Successful** — 4/4 stories delivered, no roll-over.
