# Architectural Decision Record: Multi-week xP (fixture horizon)

**Decision ID:** ADR-007
**Date:** 2026-08-02
**Status:** Accepted
**Superseded By / Replaces:** N/A (extends ADR-006)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

xP v0 (ADR-006) estimates a player's expected points for their team's *next single*
fixture. A Sprint 005 reflection asked whether to look at xP *across a number of
fixtures*. This sprint extends xP to a **horizon** — the next N fixtures — so decisions
can weigh a *run* of games. A planning-time data check confirmed the inputs
(`points_per_game`, fixtures, FDR) are all present; no new data is needed.

#### Decision Drivers
- **Useful for planning** — "who scores most over the next month?"
- **Reuse** — extend xP/FDR, don't rebuild.
- **Honest** — don't present a misleading comparison to FPL's `ep_next`.

---

### 💡 Decisions

**1. Aggregation — SUM.** A player's multi-week xP is the **sum** of their per-fixture
xP over the next N fixtures:
```
xP_total = points_per_game × Σ multiplier(difficulty_i)   over every fixture in the next N gameweeks
```
Chosen over an average because the total is the actionable quantity for planning, and
it **rewards fixture volume** — a double-gameweek team (more fixtures in the window)
naturally rises.

**2. Horizon unit — next N *gameweeks*.** The horizon is the next N gameweeks; xP sums
every fixture the team plays within them. This is what actually captures double/blank
gameweeks: a DGW team has *two* fixtures in one gameweek (both summed → higher xP), a
BGW team has none in a gameweek (fewer terms → lower xP).

*(Correction: US-021 first wrote "next N fixtures", but per-team fixture-count gives
every team exactly N fixtures and so can't capture DGW. Caught during US-022 and
corrected to gameweeks — the same intent, the right mechanism. In preseason there are
no DGWs, so the two are numerically identical for current data.)*

**3. `ep_next` comparability.** FPL's `ep_next` is a *single*-gameweek number, so it is
only comparable to our xP at **N=1**. At N>1 it is shown as "—" (with a note), rather
than placed misleadingly beside an N-fixture sum.

**4. Default horizon.** `xp --next` defaults to **1**, reproducing today's single-GW
behaviour exactly; `--next 5` opts into the horizon.

**5. Short horizons.** If a team has fewer than N upcoming fixtures (season end), sum
over what's available and show the actual fixture count.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** A planning-friendly "points over the next N" metric; double gameweeks
  surface for free; pure reuse of xP + FDR + fixtures.
* **Negative / Trade-offs:** Sums are large (≈ N × ppg) and no longer comparable to
  FPL's single-GW `ep_next`; a double gameweek is captured only by fixture *count*, not
  true gameweek alignment.
* **Risks & Mitigations:**
  - *Misleading `ep_next` at N>1* → shown only at N=1.
  - *Large numbers look odd* → label the output as a total over N fixtures.

---

### 🛠 Implementation & Migration
* **Components Affected:** Analytics (xP horizon), CLI (`xp --next`), UI (label), Docs
* **Action Items:**
  - [x] Record the design (US-021)
  - [ ] Multi-week xP analytics — next-N difficulties per team, sum per-fixture xP (US-022)
  - [ ] `xp --next N` command + label the horizon (US-023)
  - [ ] (Deferred) true DGW/BGW gameweek alignment; form/expected-minutes

---

### 🔄 Review & Reconsideration
* **Review Date:** When double/blank gameweeks become relevant (season underway)
* **Triggers for Reconsideration:**
  - [ ] Need true gameweek alignment (DGW/BGW) rather than fixture count
  - [ ] Want a per-fixture average alongside the total

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-021 (this), US-022/023
- **External Docs:** [ADR-006](./ADR-006-expected-points-v0.md) · [Architecture §6](../03_Architecture/Architecture.md) · [Sprint 006](../05_Sprints/Sprint6.md)
