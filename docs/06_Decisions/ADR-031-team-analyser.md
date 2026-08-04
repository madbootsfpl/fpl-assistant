# Architectural Decision Record: Team Analyser (a saved squad's health check)

**Decision ID:** ADR-031
**Date:** 2026-08-04
**Status:** Accepted
**Superseded By / Replaces:** N/A (Phase 3 decision support, feature 3 — the capstone)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

`captain` and `transfer` each answer one question. The **Team Analyser** is the overview: given a
squad, *how healthy is it over the next N gameweeks?* — projected haul, problem players, bench
strength, club concentration. A planning probe on the saved squad **"TS"** confirmed it's an
**aggregation of pieces we already have**, not new modelling:

- From the squad + xP + availability: **XI projected 278.1 xP over 5 GW**, bench 29.8, 0 availability
  issues (preseason), weakest links (Ampadu 19.4, Kelleher 19.6, Truffert 20.7), clubs (MCI 3, LIV
  2, TOT 2).
- The **XI/bench split** is available — saved squads store `bench_ids` (ADR-024). For a squad saved
  *without* a declared bench, the best legal XI is pickable with `select_squad` (ADR-008) — proven on
  TS to return the **same** projection (278.1) and the **same** four bench players the manager
  declared.
- The **forward fixture view is already inside xP** (fixture-difficulty-adjusted over the horizon,
  ADR-006/007).

The original roadmap said "upload a manager ID"; we deferred `/my-team/` auth, so the subject is a
**saved squad** — same as `captain`/`transfer`.

#### Decision Drivers
- **Compose, don't reinvent** — reuse xP, availability, saved squads, the optimiser, the renderer.
- **Be honest** — show indicators the manager can judge, not a made-up grade.
- **Tie the trio together** — an overview that points at `captain` and `transfer`.

---

### 💡 Decisions

**1. Subject: a saved squad** (`SquadStore`, ADR-024) — not a manager-ID fetch (auth deferred).

**2. Indicators, not a grade.** Show concrete numbers — projected **XI** xP over the horizon, squad
value, # availability issues, the weakest XI links, club concentration — **not** an invented
letter/number "grade" (false precision). The manager judges; the tool informs.

**3. Projected points = the starting XI only.** The bench doesn't score, so "projected xP" sums the
**XI**; the bench is shown separately as its own strength figure (a high bench total = points sitting
idle). The **XI** is the declared bench's complement when a bench is saved, else the **best legal
XI** by xP via `select_squad` (formation `XI_FLEX`, size 11) — proven identical on TS.

**4. Compose + cross-link.** Reuse `player_xp` (ADR-028), `is_unavailable` (ADR-023), the optimiser
(ADR-008), and the shared renderer (ADR-025). Point the weakest links at **`transfer`** and the top
XI player at **`captain`** — a workflow, not three silos. Horizon default 5 (`--next`).

**5. Complements `squad --load`.** `--load` is the *current* state (re-priced, injuries, departed,
ADR-024); `analyse` is the *forward* view (xP over N GW + problems + links). Different questions.

**Not in scope:** manager-ID auto-fetch; a numeric/letter grade; xMins-weighted projections; running
`captain`/`transfer` for the user (it points, they choose).

---

### 🧪 Worked example (pressure-testing — real squad, before code)

On "TS", 5-GW horizon: projected **XI 278.1 xP**, bench 29.8, 0 issues, weakest = Ampadu · Kelleher ·
Truffert. The no-declared-bench fallback (`select_squad` over the owned 15) returned an **Optimal**
XI with the **same 278.1** and the **same four** bench players (Diop, Dubravka, Kusi-Asare, Slater) —
so the fallback is sensible and reuses machinery we own.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** the decision-support capstone — one health-check view that composes the trio's pieces
  and links them into a workflow. No new dependency, no schema change.
* **Negative / Trade-offs:** it summarises rather than decides (by design); projections assume the
  XI plays (xP is a mean — the shared caveat); no auto-fetch of the real team (a saved squad only).
* **Risks & Mitigations:**
  - *False-precision grade* → concrete indicators, no letter.
  - *No declared bench* → best-XI via `select_squad` (proven); assumption noted.
  - *Bench xP misread as projected* → projected = XI only; bench shown separately.

---

### 🛠 Implementation & Migration
* **Components Affected:** a pure `analyse_squad()` analytics fn (owned + xi_ids + xp → indicators);
  the `analyse` command (`--squad`, `--next`, `--type`) doing XI selection (declared bench or
  `select_squad`); a `render_squad_analysis` view (summary + XI + bench + highlights). Reuses
  `SquadStore`, `player_xp`, `is_unavailable`, `select_squad`, the shared renderer. No schema change.
* **Action Items:**
  - [x] Record the design + the two probe validations (US-086)
  - [ ] `analyse_squad` (pure) + unit tests (US-087)
  - [ ] `analyse` command + view + smoke (US-088)
  - [ ] (Backlog) manager-ID fetch once auth exists; a numeric health score if a benchmark appears

---

### 🔄 Review & Reconsideration
* **Review Date:** When `/my-team/` auth exists (analyse the real team) or xMins arrives (weight the
  projection by expected minutes).
* **Triggers for Reconsideration:**
  - [ ] Auth added → analyse a live manager ID, not just a saved squad.
  - [ ] A meaningful benchmark exists → an honest health score alongside the raw indicators.

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-086 (this), US-087, US-088
- **External Docs:** [ADR-024 (saved squads)](./ADR-024-saved-squad.md) · [ADR-028 (xP)](./ADR-028-xp-historical-baseline.md) · [ADR-008 (optimiser)](./ADR-008-squad-selector.md) · [ADR-029 (captain)](./ADR-029-captain-suggestions.md) · [ADR-030 (transfer)](./ADR-030-transfer-suggestions.md) · [Sprint 029](../05_Sprints/Sprint29.md)
