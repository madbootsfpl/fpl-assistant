# Architectural Decision Record: Player Availability

**Decision ID:** ADR-023
**Date:** 2026-08-03
**Status:** Accepted
**Superseded By / Replaces:** N/A (extends ADR-008 squad selection; policy-at-edge like ADR-011/014)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The optimiser maximises a score over *every* player, so it can pick someone who **can't play**.
A probe confirmed the gap is live: default `squad` (XI and `--full`) selects **Garner (status
'i', injured)** on last-season points. Availability is **reference data** FPL already publishes —
`status` (a/d/i/s/u, stored since Sprint 005), `chance_of_playing_next_round`, and `news`.

#### Decision Drivers
- **Correctness** — don't put an injured player in an "optimal" team.
- **Respect the manager** — allow overrides (with a warning), don't dictate.
- **Keep the core generic** — availability is a policy at the edge, not solver logic.

---

### 💡 Decisions

**1. What counts as unavailable.** `status in {i, s, u, n}` — injured / suspended /
unavailable(departed) / not-in-squad (all `chance == 0`). **Available = `a`** (fit).
**Doubtful = `d`** — *kept* (they might play, chance 25–75%) but **flagged**.

**2. Default exclude, at the edge.** `squad` optimises over available players only — the CLI
filters the pool before calling `select_squad`, which stays a generic "maximise these scores".
**`--include-unavailable`** opts back in to the theoretical best. The output reports what was
left out (e.g. "Excluded 37 unavailable, incl. Garner (i)…").

**3. Forced-in override warns.** `--include <unavailable>` keeps the player (the manager's
call) but **warns** ("Garner is injured") — the warn-not-block spirit of ADR-022.

**4. Flag doubtful picks.** A doubtful (`d`) player in the squad is shown with their chance
("Kamara (d 75%)") — informative, not excluded.

**5. Ingest.** `chance_of_playing_next_round` and `news` via `Player.from_api` + the generic
migration (`status` is already stored).

**Not in scope:** availability flags across every view (table/xg/… — a follow-on);
deprioritising by `chance` % rather than a hard filter; a saved-squad availability reload;
predicting return dates.

---

### 🧪 Worked example (pressure-testing — run on real data)

Simulating the edge filter (`available = status not in {i,s,u,n}`) on the live squad:

| | Result |
|---|---|
| Pool | 564 → **527 available** (37 unavailable excluded) |
| Default `squad` @ £80m | Garner (injured) **out**, 2020 pts |
| `--include-unavailable` | Garner **in**, 2024 pts |
| Cost of excluding | **4 pts** — for a squad that can actually play |
| Doubtful | Wharton (`d`) kept in pool, to be flagged |

Confirms the default fixes the injured-Garner pick at a trivial cost, the opt-out restores the
theoretical best, and doubtful players stay — all before any code.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** The optimiser is honest about who can play (no injured picks by default); the
  manager keeps overrides (warned); the solver stays generic (policy at the edge); no new
  dependency. Costs almost nothing in points (4 here).
* **Negative / Trade-offs:** Preseason `status`/`news` can be stale (same as all FPL data;
  auto-updates on refresh). A doubtful player *could* still be auto-picked (by design — they
  might play) — mitigated by the flag. Excluding is a blunt tool vs weighting by `chance`
  (deferred).
* **Risks & Mitigations:**
  - *Over-excluding* → only i/s/u/n; doubtful stays, flagged.
  - *Silent forced-in* → keep the override but warn.
  - *Infeasibility* → 509 available players; never binds.

---

### 🛠 Implementation & Migration
* **Components Affected:** `Player` model (+`chance`, `news`), storage (migration), a pure
  `is_unavailable` helper, CLI (`cmd_squad` filter/report/warn; `--include-unavailable`),
  display (`render_squad` doubtful flag), Docs. `select_squad` stays generic.
* **Action Items:**
  - [x] Record the policy + worked example (US-064)
  - [ ] Ingest & store `chance` / `news` + migration (US-065)
  - [ ] `is_unavailable` + CLI filter/report/warn + doubtful flag (US-066)
  - [ ] (Backlog) availability flags in the other views; saved-squad reload; weight-by-chance

---

### 🔄 Review & Reconsideration
* **Review Date:** Once the season starts (status/news become live-form).
* **Triggers for Reconsideration:**
  - [ ] Want to *deprioritise* by `chance` (a soft penalty) rather than a hard exclude.
  - [ ] Want availability flags across every view, or on a saved-squad reload.

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-064 (this), US-065/066
- **External Docs:** [ADR-008 (squad selector)](./ADR-008-squad-selector.md) · [ADR-006 (status ingested)](./ADR-006-expected-points-v0.md) · [ADR-022 (warn, not block)](./ADR-022-validate-legal-bench.md) · [Sprint 022](../05_Sprints/Sprint22.md)
