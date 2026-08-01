# Architectural Decision Record: Fixtures Data Model & FDR Approach

**Decision ID:** ADR-004
**Date:** 2026-08-01
**Status:** Accepted
**Superseded By / Replaces:** N/A
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Sprint 003 introduces the project's second data entity — **fixtures** (matches) —
and the first fixture-based insight, a Fixture Difficulty Rating (FDR) view. Before
building, we must agree the fixtures data model and how "difficulty" and "upcoming"
are defined, so the ingestion (US-010), FDR view (US-011) and listing (US-012) build
on a settled shape.

#### Decision Drivers (Key Requirements)
- **Keep it simple / ship insight** — a first useful FDR, not a research model.
- **Data integrity** — a fixture references two teams; those references must be valid.
- **Don't over-build** — the Roadmap's custom FDR is a later sprint.

---

### 💡 Options Considered

#### FDR source
- **Option 1 (Chosen): use FPL's own `team_h_difficulty` / `team_a_difficulty`.**
  Simple, already in the payload, gives immediate insight.
- **Option 2: build a custom Attack/Defense FDR now.** More accurate long-term, but
  a large piece of work (home/away weighting, recent form) — premature this sprint.

#### Defining "upcoming"
- **Option 1 (Chosen): derive from unfinished fixtures ordered by gameweek.** No new
  storage; enough for a next-N-fixtures view.
- **Option 2: store a separate `events`/gameweeks table.** Richer (current/next GW
  flags, blank/double GWs) but more than v1 needs.

#### Fixtures schema
Store only the fields we use (same discipline as `players`):
`id`, `event` (nullable), `team_h`, `team_a`, `team_h_difficulty`,
`team_a_difficulty`, `finished`, `kickoff_time` (nullable).

---

### 🎯 Decision & Justification

**Chosen:** FPL's own difficulty numbers; derive "upcoming" from unfinished fixtures
ordered by gameweek (no events table yet); the 8-field schema above.

**Reasoning:** This is the simplest path that produces a genuinely useful FDR view
this sprint, while leaving the door open for a custom rating later. Difficulty is
stored **per side** (home/away) because FDR depends on perspective — a match easy for
the home team can be hard for the away team; US-011 picks the right side per team.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** A first fixture-based insight ships quickly on a small, clear schema.
* **Negative / Trade-offs:** FPL's difficulty is coarse (1–5, static); a custom model
  would be more accurate. Blank/double gameweeks and current-GW flags aren't modelled
  yet (no events table).
* **Risks & Mitigations:**
  - *Null `event`* (unscheduled fixtures) → nullable column; treated as not-upcoming.
  - *FK enforcement rejects a fixture* → save order is teams → fixtures.

---

### 🛠 Implementation & Migration
* **Components Affected:** Storage (new `fixtures` table + two FKs), Ingestion
  (extend `refresh`), Analytics (FDR), CLI (`fdr`, `fixtures`), Docs
* **Action Items:**
  - [x] Record schema in Architecture §6 (US-009)
  - [ ] Fixtures ingestion + table + extend `refresh` (US-010)
  - [ ] FDR view — per-team average upcoming difficulty (US-011)
  - [ ] Fixtures listing (US-012)

---

### 🔄 Review & Reconsideration
* **Review Date:** When a custom FDR is considered (Sprint 004+)
* **Triggers for Reconsideration:**
  - [ ] Need for Attack/Defense split or home/away weighting
  - [ ] Need to model blank/double gameweeks or current/next GW → an events table

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-009 (this), US-010/011/012
- **External Docs:** [Architecture §6](../03_Architecture/Architecture.md) · [Roadmap Phase 2](../04_Roadmap/Roadmap.md) · [Sprint 003](../05_Sprints/Sprint3.md)
