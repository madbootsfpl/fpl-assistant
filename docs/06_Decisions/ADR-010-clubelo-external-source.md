# Architectural Decision Record: ClubElo — First External Data Source

**Decision ID:** ADR-010
**Date:** 2026-08-02
**Status:** Accepted
**Superseded By / Replaces:** N/A
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

From a Sprint 008 reflection: what value would external data sources add? FPL's own
advanced signals (form, attack/defence strengths) are all zero in preseason, so we
add a **second source** to fill the gap — starting small with **ClubElo** (team Elo
ratings). This is the project's first *multi-source* design. A planning-time check
confirmed ClubElo is reachable (no key, CSV), populated now, and that team-name
matching is 14/20 exact + a 6-entry mapping.

#### Decision Drivers
- **Fills a real gap** — Elo is live team strength, unlike FPL's preseason zeros.
- **Small and safe** — one source, team-level, no new dependency.
- **Best-effort** — the app must keep working if the external source fails (Roadmap).

---

### 💡 Decisions

**1. Fetch.** `http://api.clubelo.com/<current-date>` → CSV
(`Rank, Club, Country, Level, Elo, From, To`). Filter `Country=ENG, Level=1`; parse
with the stdlib `csv` module. No API key; no new pip dependency.

**2. Name mapping.** 14 clubs match FPL's `name` exactly; the other 6 use an explicit
`{ClubElo → FPL}` table. An unmapped ENG level-1 club → **fail loudly** (so a silent
gap can't slip through).

| ClubElo | FPL |
|---|---|
| Coventry | Coventry City |
| Forest | Nott'm Forest |
| Hull | Hull City |
| Ipswich | Ipswich Town |
| Man United | Man Utd |
| Tottenham | Spurs |

**3. Storage.** A `teams.elo` column (REAL), added by the existing light migration.

**4. Graceful degradation.** ClubElo is *best-effort*: if the fetch/parse fails,
`refresh` logs it and **continues with FPL data**, leaving the existing `elo` values
**untouched** (a transient outage must not wipe good data). Every non-Elo feature is
unaffected.

**5. Elo → difficulty (rank bands).** Sort the 20 teams by Elo and split into 5 equal
bands of 4 → difficulty 1 (weakest opponents) … 5 (strongest). Always uses the full
1–5 and is directly comparable to the `fpl`/`custom` FDR. Chosen over linear min-max
(which clusters mid-table and is outlier-sensitive). Venue-agnostic in v0. Powers
`fdr --type elo`.

---

### 🧪 Worked examples (pressure-testing the mechanism)

| Case | Expected | Verifies |
|---|---|---|
| Map all 20 clubs | 14 exact + 6 via table → all resolve | mapping is complete |
| Unknown ENG level-1 club appears | Clear error, not dropped | fail-loud on gaps |
| ClubElo errors mid-`refresh` | FPL data still stored; `elo` untouched; app works | graceful degradation |
| `fdr --type elo`, a team missing Elo | that team's difficulty undefined, handled | no crash on partial data |
| Rank bands | Arsenal (2064) → 5, Hull (1533) → 1 | Elo→difficulty is correct |

---

### ⚖️ Consequences & Trade-offs

* **Positive:** Real team strength *now*; the first multi-source design + a reusable
  graceful-degradation pattern; a new FDR that works in preseason; no new dependency.
* **Negative / Trade-offs:** A second source to keep working; rank bands lose the fine
  Elo gaps within a band; venue (home/away Elo) not modelled in v0.
* **Risks & Mitigations:**
  - *ClubElo down / format change* → non-fatal; a test covers the failure path.
  - *Unmapped club* → fail loudly.

---

### 🛠 Implementation & Migration
* **Components Affected:** new ClubElo client + name mapping, Storage (`teams.elo`),
  ingestion (`refresh`), Analytics (Elo FDR), Docs
* **Action Items:**
  - [x] Record the design + mapping + worked examples (US-030)
  - [ ] ClubElo client + team-name mapping (US-031)
  - [ ] `teams.elo` migration + graceful `refresh` (US-032)
  - [ ] Elo-based FDR (`fdr --type elo`) + Handbook (US-033)
  - [ ] (Later) FBref xG/xA; home/away Elo

---

### 🔄 Review & Reconsideration
* **Review Date:** When a second external source (FBref) is added
* **Triggers for Reconsideration:**
  - [ ] Elo rank bands prove too coarse → revisit normalisation
  - [ ] Need venue-aware Elo (home advantage)

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-030 (this), US-031/032/033
- **External Docs:** [Data Sources](../10_Data_Sources/Data_Sources.md) · [Architecture](../03_Architecture/Architecture.md) · [Sprint 009](../05_Sprints/Sprint9.md) · [ADR-005 (custom FDR)](./ADR-005-custom-fdr.md)
