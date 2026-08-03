# Architectural Decision Record: Transfer suggestions (best single legal upgrades)

**Decision ID:** ADR-030
**Date:** 2026-08-03
**Status:** Accepted
**Superseded By / Replaces:** N/A (Phase 3 decision support, feature 2)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

After captaincy, the next decision-support question is **"who should I transfer?"** — swap a weak
player out for a better one, within FPL's rules. A planning probe on the saved squad **"TS"**
confirmed the feature is feasible, useful, and grounded in data we already hold:

- Over a 5-GW horizon, the top single transfers are sensible and self-funding — e.g.
  **Kelleher → Benitez (+15.4)**, **Slater → Reed (+9.9)**, **Ampadu → Dasilva (+7.2)**.
- Every constraint is enforceable from stored data: same position, ≤3/club, availability,
  not-already-owned, affordability. Reuses xP (ADR-028), saved squads (ADR-024), the optimiser's
  `MAX_PER_CLUB`, and the shared renderer (ADR-025).

Two things the probe forced (Decisions 2 and 5). It also confirmed what we *can't* see: the user's
**bank** (we deferred `/my-team/` auth), and who they **start vs bench**.

#### Decision Drivers
- **Respect FPL's rules** — an illegal suggestion is worse than none.
- **Reuse xP; don't invent a "transfer score."**
- **Be honest about the unknowns** (bank, bench, rotation) rather than guessing.

---

### 💡 Decisions

**1. Scope: the best *single* transfers for a saved squad.** For each owned player, find the best
legal, affordable, available same-position replacement; rank all such moves by **xP gain over a
horizon**; suggest the top N (the #1 is the manager's one-free-transfer recommendation). *Deferred:*
multi-move plans and hit (−4) optimisation — a separate **transfer planner** (Backlog).

**2. Budget = sold player's price + `--bank` (default £0).** The bank isn't knowable without auth,
so default to £0 (a self-funding swap) and let the user supply their bank. The assumption is stated
in the output. A candidate is affordable iff `price ≤ out.price + bank`.

**3. Metric: xP gain over a horizon (default 5 GW).** Transfers are a multi-week commitment (unlike
captaincy's single GW), so compare replacement vs outgoing xP summed over the next N gameweeks
(ADR-007). Only **positive-gain** moves are suggested.

**4. Constraints (all enforced, unit-tested):** same position (FPL keeps 2/5/5/3); not already
owned; available (`is_unavailable`, ADR-023); **≤3 per club** — computed *after* accounting for the
outgoing player freeing a slot (so a same-club swap is always legal, and a candidate from a
3-already club is rejected unless you sell from that club). `MAX_PER_CLUB = 3` reused from the
optimiser.

**5. Goalkeepers are *included* (the mirror of captaincy).** The top probe move was a GK→GK upgrade
(Kelleher → Benitez). Captaincy *excludes* GKs (a ceiling bet — keepers have none, ADR-029), but a
**better keeper is a legitimate transfer**, so transfers keep all positions. A deliberate,
recorded contrast.

**6. Bench-blind, but bench players are *flagged*.** The engine ranks by xP gain across all 15 and
does **not** distinguish starters from bench (a bench upgrade helps the weekly score less — that's
rotation/xMins, a later phase). But the saved squad stores `bench_ids` (ADR-024), so a suggestion
whose *outgoing* player is on the bench is **marked**, letting the manager weigh it. Cheap and
honest, without building full XI-vs-bench modelling now.

**7. Explain the move.** Show OUT (price, xP) → IN (price, xP), the Δ, the bench flag, and the
caveats (unknown bank; single move; xP is a mean / assumes they play).

**Not in scope:** multi-move / hit optimisation; fetching the real bank; xMins-weighted ranking;
free-transfer accounting across weeks.

---

### 🧪 Worked example (pressure-testing — real squad, before code)

On squad "TS", 5-GW horizon:

| OUT | | IN | Δ |
|---|---|---|--:|
| Kelleher (BRE, £5.0, xP5 19.6) | → | Benitez (CRY, £4.5, xP5 35.0) | **+15.4** |
| Slater (HUL, £4.5, xP5 0.0) | → | Reed (FUL, £4.5, xP5 9.9) | +9.9 |
| Ampadu (LEE, £5.5, xP5 19.4) | → | Dasilva (BRE, £5.0, xP5 26.6) | +7.2 |

Constraints verified live: the squad has 3 from **MCI**, so an MCI candidate is rejected unless an
MCI player is the one sold; and `--bank £2.0m` changes the top gain (+15.4 → +27.8, Wilson) because
a pricier target becomes affordable. GK→GK upgrades are allowed (unlike captaincy).

---

### ⚖️ Consequences & Trade-offs

* **Positive:** the first feature that recommends a *rule-respecting change* — legal, affordable,
  explained. Composes xP + saved squads + the optimiser's club rule; no new dependency.
* **Negative / Trade-offs:** doesn't know the real bank (`--bank`), nor who starts (bench flag, not
  modelling). Single-move only. xP is a mean, so a high-ceiling differential won't stand out.
* **Risks & Mitigations:**
  - *Illegal suggestion* → constraints enforced per candidate, unit-tested (esp. ≤3/club).
  - *Wrong budget* → `--bank` default £0, assumption stated.
  - *Bench upgrade over-valued* → flagged; caveat noted; full xMins is a later phase.

---

### 🛠 Implementation & Migration
* **Components Affected:** a `suggest_transfers()` analytics fn (pure — squad + players + xP-by-id
  + bank/horizon → ranked moves); the `transfer` command (`--squad`, `--bank`, `--next`, `--limit`);
  a `render_transfers` view (OUT → IN, Δ, bench flag). Reuses `SquadStore`, `player_xp`,
  `is_unavailable`, `MAX_PER_CLUB`. The optimiser and existing views are untouched. No schema change.
* **Action Items:**
  - [x] Record the design + the two probe findings (GK-include, bench-flag) (US-083)
  - [ ] `suggest_transfers` + constraint tests (US-084)
  - [ ] `transfer` command + explain-why view + smoke (US-085)
  - [ ] (Backlog) a multi-move transfer *planner* (hits vs roll, −4 maths, free-transfer accounting)

---

### 🔄 Review & Reconsideration
* **Review Date:** When xMins/rotation exists (weight by expected minutes; retire bench-blindness) or
  a multi-week planner is wanted.
* **Triggers for Reconsideration:**
  - [ ] Bank becomes knowable (auth) → drop the `--bank` assumption.
  - [ ] Multi-move planning needed → a planner that optimises a sequence with hit costs.

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-083 (this), US-084, US-085
- **External Docs:** [ADR-029 (captain — GK exclusion contrast)](./ADR-029-captain-suggestions.md) · [ADR-028 (xP)](./ADR-028-xp-historical-baseline.md) · [ADR-024 (saved squads)](./ADR-024-saved-squad.md) · [ADR-008 (optimiser / MAX_PER_CLUB)](./ADR-008-squad-selector.md) · [Sprint 028](../05_Sprints/Sprint28.md)
