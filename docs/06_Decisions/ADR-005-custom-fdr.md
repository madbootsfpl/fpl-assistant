# Architectural Decision Record: Custom (Overall) Fixture Difficulty

**Decision ID:** ADR-005
**Date:** 2026-08-02
**Status:** Accepted
**Superseded By / Replaces:** N/A (extends the FPL-difficulty FDR from ADR-004)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Sprint 004 sets out to compute the app's *own* fixture difficulty instead of using
FPL's coarse published value (ADR-004). A planning check of live `bootstrap-static`
data (2026-08-02, preseason) found the granular strength fields
(`strength_attack_*`, `strength_defence_*`) are **all zero across all 20 teams** —
FPL doesn't publish them until the season is underway. Only
`strength_overall_home/away` (a 1–5 scale) is populated.

So the intended Attack/Defence split isn't buildable yet. We must decide the design of
a **custom *overall* FDR** from the data we do have.

#### Decision Drivers
- **Honest to the data** — build only what the available fields support.
- **Keep it simple / build on Sprint 003** — reuse fixtures, teams, the `_view` helper.
- **Learning value** — a transparent, extendable formula; a real schema-evolution.

---

### 💡 Decisions

**1. Data source.** Use `strength_overall_home/away` (1–5). The Attack/Defence split is
**deferred** until FPL populates `strength_attack_*` / `strength_defence_*` (season
start — re-check the fields before starting it).

**2. Formula (opponent strength only, home/away aware).** A team's difficulty facing an
opponent is the opponent's overall strength *at the venue the opponent plays*:

```
my team HOME → opponent away → difficulty = opponent.strength_overall_away
my team AWAY → opponent home → difficulty = opponent.strength_overall_home
```

A team's custom FDR is the average of that over its next N fixtures. Chosen over a
"strength gap (opponent − own)" formula because it's simpler, stays on the 1–5 scale,
and is directly comparable to FPL's FDR.

**3. Coexistence.** Custom FDR is added as `fdr --type custom`; FPL's stays as
`--type fpl` (the default). Keeping both allows side-by-side comparison.

**4. Presentation.** Values stay on the 1–5 scale; averages shown to one decimal place.
No normalisation needed.

**5. Schema evolution (light migration).** The `teams` table already exists in the
cache, and `CREATE TABLE IF NOT EXISTS` won't add columns to it. On startup, check
`PRAGMA table_info(teams)` and `ALTER TABLE teams ADD COLUMN ...` for any missing
strength column. Chosen over recreating the cache because it preserves data and
teaches the real-world migration pattern.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** A transparent, home/away-aware difficulty we control and can extend;
  a real (if small) schema migration; FPL's version retained for comparison.
* **Negative / Trade-offs:** Because both derive from overall strength, custom FDR may
  land close to FPL's — the value this sprint is the *transparent, extendable* formula
  and the groundwork, not a dramatically different number.
* **Risks & Mitigations:**
  - *Home/away backwards* → a test pins the direction.
  - *Attack/Defence data appears mid-sprint* → out of scope; revisit for the split.

---

### 🛠 Implementation & Migration
* **Components Affected:** Storage (teams columns + migration), Models (`Team`),
  Analytics (custom FDR), CLI (`fdr --type`), Docs
* **Action Items:**
  - [x] Record the design + preseason finding (US-013)
  - [ ] Store `strength_overall_home/away` with a light migration (US-014)
  - [ ] Custom FDR analytics + `fdr --type custom|fpl` (US-015)
  - [ ] Per-match custom difficulty in `fixtures --team` (US-016)
  - [ ] (Deferred) Attack/Defence split once strengths populate

---

### 🔄 Review & Reconsideration
* **Review Date:** When the season starts and `strength_attack_*` / `strength_defence_*`
  populate
* **Triggers for Reconsideration:**
  - [ ] Granular strengths become available → build the Attack/Defence split
  - [ ] Custom FDR proves too close to FPL's to be worth keeping separate

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-013 (this), US-014/015/016
- **External Docs:** [ADR-004](./ADR-004-fixtures-and-fdr.md) · [Architecture §6](../03_Architecture/Architecture.md) · [Sprint 004](../05_Sprints/Sprint4.md) · memory: `fpl-preseason-strength-data`
