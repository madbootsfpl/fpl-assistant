# Architectural Decision Record: Expected Points (xP v0)

**Decision ID:** ADR-006
**Date:** 2026-08-02
**Status:** Accepted
**Superseded By / Replaces:** N/A
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Sprint 005 builds the project's first **Expected Points (xP)** metric — the Roadmap's
"single source of truth" for future recommendations. A planning-time data check found
`points_per_game`, `status` and FPL's own `ep_next` are populated, while `form` (0/564)
and the attack/defence strengths (0/20) are not (preseason). So we design a **simple
v0** from the data we have, and defer the rest.

xP is also the project's first **cross-domain** metric: it combines a *player's*
scoring rate with a *fixture's* difficulty.

#### Decision Drivers
- **Keep it simple / honest to the data** — a transparent heuristic, not a full model.
- **Reuse** — use the Sprint 004 FDR as the difficulty input.
- **Learning** — a metric that joins two analytics domains.

---

### 💡 Decisions

**1. Formula (gentle fixture weighting).**
```
multiplier = 1 + (3 − difficulty) × 0.10      # diff 1 → 1.20 … diff 3 → 1.00 … diff 5 → 0.80
xP_next    = points_per_game × multiplier
```
Difficulty is neutral at 3 and swings xP by ±20% at the extremes — modest, because
difficulty is only one factor (form, minutes come later). Chosen over a stronger ±40%.

**2. Difficulty source.** Reuse the `--type custom|fpl` seam from Sprint 004 (default
`fpl`), so xP can be driven by our FDR or FPL's.

**3. Horizon.** The next *single* gameweek (each player's team's next upcoming fixture).
Multi-week and double/blank gameweeks are deferred.

**4. Availability.** If `status != 'a'` (injured/suspended/unavailable), xP = 0, so the
player sinks in the ranking. `chance_of_playing` is barely populated, so `status` is the
clean v0 signal.

**5. Baseline is last-season data.** `points_per_game` (and `total_points`, `minutes`)
in `bootstrap-static` are last season's, carried forward. So xP v0's baseline *is*
last-season performance, and it **auto-updates on `refresh`** as the new season plays —
no code change needed. `points_per_game`/`ep_next` arrive as strings; convert to float
at the `from_api` boundary.

**6. Comparison.** Show FPL's own `ep_next` alongside our xP (mirrors `custom` vs `fpl`
for FDR).

---

### ⚖️ Consequences & Trade-offs

* **Positive:** A transparent, explainable xP that reuses the FDR; the first metric to
  join player and fixture analytics; a baseline that self-updates into the new season.
* **Negative / Trade-offs:** It's a heuristic — no form, no expected-minutes modelling,
  single gameweek only. The baseline is prior-season until the new season plays.
* **Risks & Mitigations:**
  - *Player → next fixture with DGW/BGW* → v0 uses the next single fixture; note it.
  - *Heuristic multiplier* → explicit constant; compare against FPL `ep_next`.

---

### 🛠 Implementation & Migration
* **Components Affected:** Models (`Player`), Storage (columns + migration), Analytics
  (xP, cross-domain), CLI (`xp`), Docs
* **Action Items:**
  - [x] Record the design + data finding (US-017)
  - [ ] Store `points_per_game`, `status`, `ep_next` via the `ALTER TABLE` migration (US-018)
  - [ ] xP analytics — ppg × next-fixture difficulty (US-019)
  - [ ] `xp` command + compare vs `ep_next` (US-020)
  - [ ] (Deferred) form, expected minutes, multi-week, DGW/BGW

---

### 🔄 Review & Reconsideration
* **Review Date:** When `form` populates (season underway)
* **Triggers for Reconsideration:**
  - [ ] `form` / expected-minutes data available → richer xP
  - [ ] xP proves too coarse vs FPL's `ep_next` → refine the model

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-017 (this), US-018/019/020
- **External Docs:** [ADR-005](./ADR-005-custom-fdr.md) · [Architecture §6](../03_Architecture/Architecture.md) · [Sprint 005](../05_Sprints/Sprint5.md) · [Roadmap Phase 2 (xP Engine)](../04_Roadmap/Roadmap.md)
