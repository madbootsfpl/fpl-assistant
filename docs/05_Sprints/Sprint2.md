# Sprint 002: Insight & Interaction

**Dates:** TBC
**Status:** Planned
**Capacity:** ~3–4 working sessions
**Carried Over:** None

---

### 🧭 Architecturally, what's new

Sprint 001 was a straight line: run the app → it does the whole pipeline → prints a
table. Sprint 002 changes the app from *"do one fixed thing"* into *"respond to what
the user asks"*, and introduces the project's first analytics. Two new pieces:

1. **An interaction (CLI) layer** — the user needs to drive the app (search, filter,
   refresh, view). How that works is a genuine design decision, so it is the gating
   story (US-005), just as agreeing the architecture was for Sprint 001.
2. **The analytics layer** (`src/analytics/`) — Points-per-£m is the first *derived*
   metric: the first number the project calculates itself rather than reading from
   FPL. This begins Roadmap Phase 2.

The layering rule still holds: analytics reads from **storage**, never the API; the
CLI orchestrates but contains no logic itself; only `refresh` touches the network.

```
                 ┌─ search / filter ─┐
CLI (commands) → analytics (value)  → reads Storage (SQLite) → display
       └─ refresh → FplClient → Storage (the ONLY path that hits the API)
```

---

### 🎯 Sprint Goal

**Objective:** Turn the static player dump into an *interactive* tool that gives real
FPL insight — let the user refresh, search, filter, and rank players by value
(Points-per-£m) from the command line.

#### Success Criteria
- [x] A CLI decision is agreed (ADR-003) before the interactive code is written
- [x] `refresh` re-fetches and re-stores data as an explicit command (viewing no longer forces a network call)
- [ ] Players can be **searched** by name
- [ ] Players can be **filtered** by position, team, and max price
- [x] A **Points-per-£m** value column is calculated and can sort the table
- [ ] Tests cover the new analytics and filtering (offline)

---

### 📋 Sprint Backlog

#### User Stories & Features
| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-005 | Agree CLI/interaction design + analytics placement (ADR-003) + command skeleton | Critical | ✅ Complete | 1 session |
| US-006 | Manual `refresh` command — separate fetching from viewing | High | ✅ Complete | 0.5 session |
| US-007 | Points-per-£m value metric (analytics layer) + value column/sort | High | ✅ Complete | 1 session |
| US-008 | Search & filter players (name, position, team, max price) | Medium | Planned | 1 session |

#### Technical Tasks & Maintenance
- [x] Update Architecture doc: add the interaction (CLI) layer + analytics layer - _Done (US-005)_
- [x] Record ADR-003 (CLI approach) in `06_Decisions/` and add to the ADR index - _Done (US-005)_
- [ ] Consider enabling SQLite foreign-key enforcement (Sprint 001 retro action) - _Planned_
- [ ] Update Handbook (CLI note; bump the analytics chapter when first used) - _Planned_
- [x] Update `README.md` with the new commands - _Done (US-005)_

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| • CLI commands: refresh, table, search, filter | • Web UI / FastAPI (still deferred, ADR-002) |
| • One value metric: Points-per-£m | • Form, xG/xA, FDR, xP → later Phase 2 |
| • Read from local SQLite | • Fixtures, historical data, captain/transfer advice |
| • Sort by points or value | • Multi-week planning, optimisation |

**External Dependencies:**
- [ ] Sprint 001 storage/models (done)
- [ ] `argparse` (Python standard library — no new packages expected)

---

### ⚠️ Risks & Mitigations

| Risk | Impact (High/Med/Low) | Mitigation Strategy |
|---|---|---|
| Analytics scope balloons (form, xG…) | Med | Hard-limit to Points-per-£m this sprint |
| Divide-by-zero in value calc (price 0/None) | Med | Guard the calculation; treat as 0/None value explicitly |
| CLI over-engineering (interactive TUI, menus) | Med | Recommend plain `argparse` subcommands; keep it simple |
| Running `table` before any `refresh` (empty DB) | Low | Friendly "no data yet — run `refresh`" message |
| Every command hitting the API | Med | Only `refresh` touches the network; all views read the DB |

---

### 🗝️ Gating decision (US-005)

How the user drives the app. **Recommendation:** plain `argparse` subcommands, e.g.

```text
python app.py refresh
python app.py table --sort value
python app.py search haaland
python app.py filter --pos MID --max-price 8
```

Simple, stdlib, no new dependency, and it fits "console-first" (ADR-002). The
alternative (an interactive menu/TUI) is more complexity than a single-user
learning tool needs yet. To be confirmed and recorded as **ADR-003** at sprint start.

---

### 📝 Session Progress Log

#### Session 1 - 2026-08-01 (US-005: CLI skeleton + ADR-003)
* **Completed:** ADR-003 (argparse subcommands, in `src/cli.py`, thin `app.py`; analytics → `src/analytics/`). Built `src/cli.py` interaction layer with `refresh`/`table`/`search`/`filter` subcommands; `table` works (reads DB, `--limit`), others stubbed for their stories. Slimmed `app.py` to a launcher. Updated Architecture §4 (two new layers), ADR index, README. 5 new tests (14 total, all passing). Verified: `--help`, `table --limit 5`, `refresh` stub all work. US-005 **complete**.
* **Issues / Blockers:** None. Note: `python app.py` no longer auto-fetches (by design) — `refresh` (US-006) will restore fetching via its own command.
* **Next Steps:** US-006 (implement the real `refresh` command).

#### Session 2 - 2026-08-01 (US-006: real refresh command)
* **Completed:** Added `src/ingest.py` (`refresh(store, client=None)` — the ingestion orchestration coordinating client → mapping → storage, injectable client for tests); wired `cmd_refresh` to call it with graceful `FplApiError` handling. 1 new test (15 total). Verified live: `refresh` stored 564 players / 20 teams; `table` shows the refreshed data. US-006 **complete**.
* **Issues / Blockers:** None.
* **Next Steps:** US-007 (Points-per-£m value metric — the first analytics).

#### Session 3 - 2026-08-01 (US-007: Points-per-£m — first analytics)
* **Completed:** Added `src/analytics/` (`value.py`: `points_per_million` + `rank_players`), the project's first derived metric. Undefined value (price 0/missing) → `None`, shown as "—" and sorted last. Added a Val/£m column to the table and a `--sort points|value` option. 6 new tests (24 total). Verified live: `--sort value` surfaces cheap high-scorers (e.g. Truffert £5.5m, 30.0/£m) that a points-only view hides. US-007 **complete**.
* **Issues / Blockers:** None.
* **Next Steps:** US-008 (search & filter players).

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

**Proposed follow-on (Sprint 003):** fixtures ingestion + a first Fixture Difficulty view (begins Roadmap Phase 2 proper).

**Completion Date:** [YYYY-MM-DD]
**Final Notes:**
