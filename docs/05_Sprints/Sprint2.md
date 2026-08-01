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
- [ ] A CLI decision is agreed (ADR-003) before the interactive code is written
- [ ] `refresh` re-fetches and re-stores data as an explicit command (viewing no longer forces a network call)
- [ ] Players can be **searched** by name
- [ ] Players can be **filtered** by position, team, and max price
- [ ] A **Points-per-£m** value column is calculated and can sort the table
- [ ] Tests cover the new analytics and filtering (offline)

---

### 📋 Sprint Backlog

#### User Stories & Features
| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-005 | Agree CLI/interaction design + analytics placement (ADR-003) + command skeleton | Critical | Planned | 1 session |
| US-006 | Manual `refresh` command — separate fetching from viewing | High | Planned | 0.5 session |
| US-007 | Points-per-£m value metric (analytics layer) + value column/sort | High | Planned | 1 session |
| US-008 | Search & filter players (name, position, team, max price) | Medium | Planned | 1 session |

#### Technical Tasks & Maintenance
- [ ] Update Architecture doc: add the interaction (CLI) layer + analytics layer - _Planned_
- [ ] Record ADR-003 (CLI approach) in `06_Decisions/` and add to the ADR index - _Planned_
- [ ] Consider enabling SQLite foreign-key enforcement (Sprint 001 retro action) - _Planned_
- [ ] Update Handbook (CLI note; bump the analytics chapter when first used) - _Planned_
- [ ] Update `README.md` with the new commands - _Planned_

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

**Proposed follow-on (Sprint 003):** fixtures ingestion + a first Fixture Difficulty view (begins Roadmap Phase 2 proper).

**Completion Date:** [YYYY-MM-DD]
**Final Notes:**
