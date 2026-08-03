# Architectural Decision Record: Defensive Contribution (DefCon reliability)

**Decision ID:** ADR-018
**Date:** 2026-08-03
**Status:** Accepted
**Superseded By / Replaces:** N/A (a defensive analog to ADR-017)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

FPL now awards **Defensive Contribution (DefCon)** points — 2 pts/match for clearing a
threshold of defensive actions — and it has become a major points source, especially for
defenders and defensive midfielders (sorting the value table now shows no forwards in the
top 20). Tony asked for a defensive analog to `overperf` (ADR-017).

A planning probe confirmed the data supports a reliability metric — and, crucially, that a
threshold comparison is *valid*.

#### Decision Drivers
- **Decision-relevant** — DefCon reliability now drives real value; managers want it surfaced.
- **Data-honest** — verify the field means what we think before comparing to a threshold.
- **Reuse the seams** — model `_to_float`, the generic migration, the `overperf` minutes gate.

---

### 💡 Decisions

**1. The metric — a margin vs the threshold.** There is no "expected DefCon", but there is a
natural reference: the per-match threshold a player must clear. So:

```
margin = defensive_contribution_per_90 − threshold[pos]
```

Positive margin → on average clears the bar → a reliable DefCon-point earner; the larger the
margin, the more reliably. Ranked by margin (descending).

**2. Thresholds (FPL rules).** DEF **10** (CBIT: clearances+blocks+interceptions+tackles);
MID/FWD **12** (CBIT + recoveries); **GK excluded** (not DefCon-eligible — they score via
saves / clean sheets). Named constants, confirmable against FPL's published rules.

**3. Minutes gate.** `minutes ≥ 900`, exactly as `overperf` (ADR-017) — a per-90 rate off a
tiny sample is noise, and the gate drops preseason glitches.

**4. Scope: a ranked list, not two ends.** Unlike `overperf`, a defensive "under-performer"
isn't meaningful — a forward with a low DefCon count isn't *failing*, it isn't his job. So
the `defcon` view is a single ranked list of the reliable earners, showing per-90 / threshold
/ margin + the action components (CBIT, tackles, recoveries).

**5. Ingest.** `defensive_contribution`, `defensive_contribution_per_90`,
`clearances_blocks_interceptions`, `tackles`, `recoveries` via `Player.from_api` + the generic
migration.

**Not in scope:** exact DefCon *points* earned (needs per-match data — a backlog item); a
`--objective defcon`; combining DefCon with attacking over/under.

---

### 🧪 Worked example (pressure-testing — run on real data)

**The field is position-correct** (so the threshold comparison is valid) — verified:
- DEF (Senesi, Gabriel): `defensive_contribution` == **CBIT** (recoveries excluded).
- MID (Anderson, Garner): `defensive_contribution` == **CBIT + recoveries**.

**Top DefCon reliability** (per-90 − threshold, minutes ≥ 900, GK excluded):

| Player | Pos | per-90 | threshold | margin |
|---|---|--:|--:|--:|
| Gomes | MID | 15.8 | 12 | +3.8 |
| Wieffer | DEF | 12.7 | 10 | +2.7 |
| Anderson | MID | 13.9 | 12 | +1.9 |
| Senesi | DEF | 11.5 | 10 | +1.5 |

- **0 forwards** in the top 20 — confirms Tony's value-table observation from the underlying data.
- **Only 23 of 248** minutes-qualified players clear their bar (margin ≥ 0) — reliable DefCon
  earners are *scarce*, so the metric surfaces a small, actionable set. This confirms both the
  metric and the single-ranked-list design before any feature code.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** Surfaces a now-major, scarce value driver (reliable DefCon earners) from data
  we already fetch — no new dependency, reusing the model/migration/gate/view seams. A
  defensive counterpart to the attacking `overperf`/`xg` lenses.
* **Negative / Trade-offs:** A per-90 average clearing the bar is a *reliability* signal, not a
  guarantee of 2 points every match (per-match variance); exact DefCon points would need
  per-match data. Preseason values are last-season. GK are out of scope for this lens.
* **Risks & Mitigations:**
  - *Reliability read as certainty* → framed as a margin (bigger = safer), stated in output.
  - *Threshold rules* → verified the field is position-correct; thresholds are named constants.
  - *GK / small samples* → GK excluded (a test); the ≥ 900 minutes gate.

---

### 🛠 Implementation & Migration
* **Components Affected:** `Player` model (+5 fields), storage (migration + save +
  get_players), analytics (the margin function), CLI (`defcon` view), Docs. **No new dependency.**
* **Action Items:**
  - [x] Record the design + worked example + the position-correct verification (US-053)
  - [ ] Ingest & store the five DefCon fields + migration (US-054)
  - [ ] The metric + `defcon` view (US-055)
  - [ ] (Backlog) exact DefCon points via per-match data; a defensive squad objective

---

### 🔄 Review & Reconsideration
* **Review Date:** Once the season starts (thresholds/rules confirmed live; numbers reset).
* **Triggers for Reconsideration:**
  - [ ] FPL changes the DefCon thresholds or the counting rules.
  - [ ] Want exact DefCon points (pull per-gameweek data to count matches cleared).

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-053 (this), US-054/055
- **External Docs:** [ADR-017 (over/under-performance)](./ADR-017-over-under-performance.md) · [ADR-015 (expected goals)](./ADR-015-expected-goals.md) · [Sprint 017](../05_Sprints/Sprint17.md)
