# Sprint 009: External Data — ClubElo (team strength)

**Dates:** TBC
**Status:** Planned
**Capacity:** ~3–4 working sessions (a bigger sprint — first second data source)
**Carried Over:** None (Sprint 008 closed clean)

---

### 🔎 Verified at planning (per the Sprint 004 lesson)

Checked the **external source** itself before committing:
- **ClubElo is reachable** — `http://api.clubelo.com/<date>` returns clean CSV
  (`Rank, Club, Country, Level, Elo, From, To`); no API key. Verified 200 OK.
- **It's populated now** — real current Elo (e.g. Arsenal 2064, Man United 1915) —
  unlike FPL's preseason strengths (still 0).
- **Team-name matching:** 14/20 match FPL exactly; **6 need a mapping**
  (Coventry City↔Coventry, Hull City↔Hull, Ipswich Town↔Ipswich, Man Utd↔Man United,
  Nott'm Forest↔Forest, Spurs↔Tottenham). Both sides have exactly 20 clubs.

This sprint follows Tony's Sprint 008 reflection (what value would other data sources
add?) — starting **small and carefully** with one source.

---

### 🧭 Architecturally, what's new — the first *multi-source* design

Until now the app had **one** data source (FPL). Sprint 009 adds a **second**
(ClubElo). That's a real step-up, and it introduces two new ideas:

1. **A second ingestion path** — a ClubElo client + a team-name mapping + storing Elo
   on the `teams` table (via the migration pattern).
2. **Graceful degradation** — external sources are *best-effort* (Roadmap: "must
   degrade gracefully"). If ClubElo is down or changes, `refresh` logs it and carries
   on with FPL data; every existing feature still works. Elo only powers the new bits.

```
refresh:
   FPL  → players, teams, fixtures        (required — as today)
   ClubElo → team Elo                     (best-effort — failure is non-fatal)
             │ map 20 clubs (14 exact + 6-entry table)
             ▼
        teams.elo  →  an Elo-based FDR (fdr --type elo)
```

No new dependency — `requests` + the stdlib `csv` module.

---

### 🎯 Sprint Goal

**Objective:** Bring **real team strength (ClubElo Elo)** into the app as a second,
gracefully-degrading data source, and use it to power an **Elo-based FDR** — giving a
team-difficulty rating that works *now* (unlike FPL's preseason strengths).

#### Success Criteria
- [x] ClubElo integration approach agreed (ADR-010) before feature code
- [x] A ClubElo client fetches Elo; all 20 teams map to FPL (14 exact + 6 mapped)
- [ ] `teams.elo` stored (via the migration pattern)
- [ ] `refresh` fetches ClubElo **gracefully** — if it fails, FPL data still loads and the app works
- [ ] `fdr --type elo` ranks teams' upcoming difficulty from opponent Elo
- [ ] Tests cover the client/mapping, graceful degradation, and the Elo FDR (offline)
- [ ] **Manual smoke test** run before the sprint is closed (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-030 | Agree ClubElo approach (ADR-010): endpoint/format, Elo storage, name mapping, graceful degradation, Elo→difficulty | Critical | ✅ Complete | 0.5 session |
| US-031 | ClubElo client + team-name mapping — fetch Elo, map 20 clubs to FPL teams | High | ✅ Complete | 1 session |
| US-032 | Store `teams.elo` (migration) + extend `refresh` with graceful degradation | High | Planned | 1 session |
| US-033 | Elo-based FDR (`fdr --type elo`) + Handbook chapter (external data / graceful degradation) + README | High | Planned | 1 session |

#### Technical Tasks & Maintenance
- [x] ADR-010 recorded + added to the ADR index - _Done (US-030)_
- [x] Update Architecture doc: second data source + graceful-degradation note - _Done (US-030)_
- [ ] `docs/10_Data_Sources` note that ClubElo is now integrated - _Planned_
- [ ] Update `README.md` with `fdr --type elo` - _Planned_

---

### ✅ Definition of Done (this sprint)

Same 3-part DoD that has held for eight sprints — a story isn't done until:
1. **Automated tests pass** (and cover the new logic).
2. **Manual smoke test done** — run the real command, eyeball the output, check `--help`.
3. **Documentation updated & checked** — Handbook, Architecture, ADR + index, README,
   sprint board + PROJECT_STATUS, as applicable (Charter Documentation Rules).

A "smoke test" + "docs touched" note goes in the session log for each feature story.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| ClubElo team Elo as a second source | FBref xG/xA (player-level) → later sprint |
| Graceful degradation (best-effort) | Other sources (API-Football, etc.) |
| Elo-based FDR (`fdr --type elo`) | Home/away Elo adjustment (v0 venue-agnostic) |
| Team-name mapping (14 + 6) | Elo history / trends |

**External Dependencies:**
- [ ] **ClubElo** (`api.clubelo.com`) — no key; parsed with stdlib `csv`
- [ ] Existing FPL data; no new pip dependency

---

### ⚠️ Risks & Mitigations

| Risk | Impact (High/Med/Low) | Mitigation Strategy |
|---|---|---|
| ClubElo unavailable / format changes | High | **Graceful degradation** — non-fatal; FPL data still loads; a test covers the failure path |
| Team-name mismatch (6 known) | Med | A small explicit mapping table (verified at planning); fail loudly if an unmapped club appears |
| Elo scale (~1500–2100) vs FDR 1–5 | Med | Normalise opponent Elo to a 1–5 difficulty (rank-based bands); decide method in ADR-010 |
| Data staleness / date endpoint | Low | Fetch the current date's ratings; store as best-effort |
| Multi-source complexity creep | Med | One source only; Elo is team-level; FBref/xG deferred |

---

### 🗝️ Gating decision (US-030 → ADR-010)

Settle before building (pressure-test with a worked example, per the standing lesson):
1. **Fetch** — `api.clubelo.com/<current-date>`, filter Country=ENG & Level=1; parse CSV.
2. **Mapping** — 14 exact + a 6-entry `{ClubElo → FPL}` table; unmapped club → clear error.
3. **Storage** — a `teams.elo` column (REAL), added by the existing migration.
4. **Graceful degradation** — ClubElo failure is logged, non-fatal; Elo left as-is/NULL.
5. **Elo → difficulty** — normalise opponent Elo to 1–5 (rank bands); venue-agnostic v0.

---

### 📝 Session Progress Log

#### Session 1 - 2026-08-02 (US-030: ADR-010 — ClubElo design)
* **Completed:** Recorded ADR-010: fetch `api.clubelo.com/<date>` CSV (ENG level-1, stdlib csv); 14 exact + a 6-entry `{ClubElo→FPL}` mapping (unmapped → fail loudly); `teams.elo` via migration; **graceful degradation** (ClubElo failure non-fatal, keep last-known Elo); **Elo → 1–5 rank bands** (4 teams per band). **Pressure-tested with worked examples** (map 20 clubs; unknown club errors; graceful failure; Arsenal→5 / Hull→1). Added to ADR index; Architecture note (second source + graceful degradation) + changelog. US-030 **complete** — no feature code.
* **Manual smoke test:** N/A (docs-only gate story).
* **Docs touched:** ADR-010 (new) + index, Architecture §4/changelog, Sprint9 board, PROJECT_STATUS.
* **Issues / Blockers:** None. (Planning verified reachability + the 6-team mapping; formulation pressure-tested.)
* **Next Steps:** US-031 — the ClubElo client + team-name mapping.

#### Session 2 - 2026-08-02 (US-031: ClubElo client + mapping)
* **Completed:** Added `src/api/clubelo.py` — `EloClient.get_elo_csv()` (fetch CSV, `ClubEloError` on failure), `parse_english_elo()` (ENG top-division only), the `{ClubElo→FPL}` table + `map_elo_to_teams()` (returns `(elo_by_team_id, unmapped)`). `config.CLUBELO_BASE_URL`. 5 offline tests via a CSV fixture (100 total). Self-contained module — the FPL side is untouched. US-031 **complete**.
* **Manual smoke test:** ✅ Live ClubElo → mapped **20/20** FPL teams, unmapped empty (ARS 2064, MCI 1971, …).
* **Docs touched:** Sprint9 board, PROJECT_STATUS. (Handbook external-data chapter comes in US-033; Architecture in US-030.)
* **Issues / Blockers:** None.
* **Next Steps:** US-032 — store `teams.elo` (migration) + extend `refresh` with graceful degradation.

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

**Proposed follow-on (Sprint 010):** FBref xG/xA (player-level, harder name matching)
now the multi-source pattern exists; or an Elo-based squad objective.

**Completion Date:** [YYYY-MM-DD]
**Final Notes:**
