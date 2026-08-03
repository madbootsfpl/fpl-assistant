# Architectural Decision Record: Clean-Sheet / Defensive-Solidity Lens (xGC)

**Decision ID:** ADR-019
**Date:** 2026-08-03
**Status:** Accepted
**Superseded By / Replaces:** N/A (companion to ADR-018; surfaces the xGC from ADR-015)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Defenders and goalkeepers score two ways: **DefCon** (actions — `defcon`, ADR-018) and
**clean sheets** (4 pts). We surfaced the first; this surfaces the second, using **expected
goals conceded (xGC)** — a field stored since Sprint 014 (ADR-015) but never shown. It also
gives GKs a lens (they're excluded from `defcon`).

A planning probe confirmed the data supports it with **no new ingest**.

#### Decision Drivers
- **Completeness** — the clean-sheet points source, to pair with `defcon`.
- **Reuse** — the metric is computable from data already stored.
- **Honesty** — xGC is a *team* signal; say so, don't mis-sell it as individual defending.

---

### 💡 Decisions

**1. The metric — computed, not ingested.**

```
xGC/90 = expected_goals_conceded × 90 ÷ minutes
```

Verified: this equals FPL's own `expected_goals_conceded_per_90` **to the decimal** (Raya
0.74, Calafiori 0.52). So we compute it from the stored `xgc` + `minutes` rather than ingest a
redundant field. **Lower xGC/90 = better solidity = higher clean-sheet probability.**

**2. Scope: DEF + GK.** They earn 4 pts for a clean sheet — the clean-sheet assets. `--pos`
can narrow; MID (1 pt for a clean sheet) are out of the default view; FWD get nothing.

**3. Minutes gate.** `minutes ≥ 900`, as `overperf`/`defcon` — a per-90 rate off a tiny sample
is noise, and it avoids divide-by-zero on 0-minute rows.

**4. Ordering.** Ranked **ascending** (lowest xGC/90 = best solidity first). The header states
"lowest = best" so the direction isn't misread.

**5. It's a team signal (the honest caveat).** xGC reflects the **team's** defensive record
while the player is on the pitch — so the ranking effectively ranks *team defences*, surfaced
via their DEF/GK (on real data, 5 of the top 6 are Arsenal). You act on it by picking that
team's cheapest nailed starter. Stated in the output + docs so it isn't mistaken for an
individual-defending metric.

**6. View.** `cleansheet` shows player / team / position / minutes / xGC-90, with `--pos` /
`--limit`.

**Not in scope:** a clean-sheet *probability* model; a team-level table (this is per player); a
squad `--objective`; merging DefCon + xGC into one "defensive value" score.

---

### 🧪 Worked example (pressure-testing — run on real data)

**Compute matches FPL** (so we can compute, not ingest): `xgc × 90 / minutes` equals FPL's
`expected_goals_conceded_per_90` to the decimal for every player checked.

**Best solidity** (lowest xGC/90, minutes ≥ 900, DEF + GK):

| Player | Pos | xGC/90 |
|---|---|--:|
| Calafiori | DEF | 0.52 |
| J.Timber | DEF | 0.64 |
| Saliba | DEF | 0.70 |
| Gabriel | DEF | 0.72 |
| Raya | GK | 0.74 |

**5 of the top 6 are Arsenal** — confirming both the metric and that it ranks *team* defences.
GKs appear (Raya), unlike `defcon`. Confirmed before any feature code.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** Completes the defensive picture (DefCon + clean sheets) and finally spends the
  `xgc` banked in Sprint 014 — a metric + view only, **no ingest, no migration, no dependency**.
  GKs get a lens.
* **Negative / Trade-offs:** It's a team signal shown per player (near-identical for teammates);
  it's *expected* solidity, not a clean-sheet guarantee; preseason values are last-season.
* **Risks & Mitigations:**
  - *Read as individual defending* → the team-level caveat in output + docs.
  - *Divide-by-zero / small samples* → the ≥ 900 minutes gate (a test covers 0 minutes).
  - *Computed value drifting from FPL's* → verified equal; a test pins the formula.

---

### 🛠 Implementation & Migration
* **Components Affected:** analytics (a new `clean_sheet` / solidity function), CLI (`cleansheet`
  view), Docs. **No model/storage change** — `xgc` + `minutes` are already stored.
* **Action Items:**
  - [x] Record the design + worked example + the compute-vs-ingest verification (US-056)
  - [ ] The metric + `cleansheet` view (US-057)
  - [ ] (Backlog) a clean-sheet *probability* model; a combined DefCon + clean-sheet score

---

### 🔄 Review & Reconsideration
* **Review Date:** Once the season starts (numbers reset; solidity becomes live-form).
* **Triggers for Reconsideration:**
  - [ ] Want a proper clean-sheet probability (from xGC via a Poisson model).
  - [ ] Want a combined "defensive value" (DefCon + clean sheet) ranking or objective.

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-056 (this), US-057
- **External Docs:** [ADR-018 (Defensive Contribution)](./ADR-018-defensive-contribution.md) · [ADR-015 (expected goals)](./ADR-015-expected-goals.md) · [Sprint 018](../05_Sprints/Sprint18.md)
