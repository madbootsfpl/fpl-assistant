# Sprint 034: Deeper Phase 4 — per-gameweek transfer plans + a table in `ask`

**Dates:** 2026-08-04
**Status:** ✅ Complete (3/3 stories, retro done)
**Capacity:** ~2–3 working sessions (compose two existing features + wiring)
**Carried Over:** None (Sprint 033 closed clean)

> **Direction (owner's Sprint-33 retro note):** *"a table with a list of transferred-in players and
> points per week would be informative"* (in the `ask "which 5 transfers"` output). So: show each
> incoming player's **per-gameweek xP** in a **table**, in both `transfer --count` and `ask` (which
> today shows only prose).

---

### 🔎 Verified at planning (the standing lesson — it's a composition, the data's there)

This is **ADR-035 (the plan) × ADR-032 (per-GW xP)** — no new modelling. Probed the TS 5-transfer
plan's incoming players with their per-GW breakdown:

```
In             GW1  GW2  GW3  GW4  GW5    xP
Benitez        7.0  6.3  7.0  7.7  7.0   35.0
Dasilva        5.3  5.3  5.8  5.3  4.8   26.6
Adli           4.5  5.6  5.6  5.6  5.1   26.4
De Cuyper      5.4  4.8  5.9  5.9  4.8   26.9
Calafiori      5.8  4.8  4.8  5.3  5.3   25.9
```

`player_xp` already returns `by_gameweek` per player (ADR-032); the plan already names the incoming
players (ADR-035). So the table is a join. It reads well and shows *when* each incoming player's
points land.

**Also:** the `ask` plan output today is **prose only** — the owner wants the structured **table**
too (the table is the exact truth; the LLM prose is the readable summary — consistent with
analytics-decide/LLM-narrate). And a small polish: the 3B model echoes the instruction (*"Here is a
summary…"*) — tighten the prompt. Still preseason; ClubElo intermittent (degrades). No new dependency.

---

### 🧭 What's new — the plan shows *when* the points land, and `ask` gains a table

Two composable improvements: the transfer **plan table** gains **per-gameweek columns** for each
incoming player (so a manager sees the weekly shape, not just a total), and **`ask` returns a
structured table** alongside the narration (its first structured detail — the exact data under the
prose). Both reuse `by_gameweek`; the plan engine and the grounding contract are unchanged.

---

### 🎯 Sprint Goal

**Objective:** Enrich the transfer-plan table with **per-gameweek xP for each incoming player**, in
`transfer --count`; and have **`ask "which N transfers"` show that table** (its first structured
detail) above the grounded narration. Tighten the plan narration prompt.

#### Success Criteria
- [ ] Approach agreed (**ADR-036**) before code — per-GW plan table; `ask` returns structured detail; both surfaces
- [ ] The plan table shows **GW1…GWN** (the incoming player's per-GW xP) + the gain, in `transfer --count`
- [ ] `ask "which N transfers"` shows the **table** (structured) + the narration (prose)
- [ ] The plan narration prompt tightened (no instruction echo)
- [ ] Reuses `by_gameweek` (ADR-032); the plan engine (ADR-035) and grounding contract (ADR-034) unchanged
- [ ] Sensible width (per-GW columns are narrow; the horizon default is 5)
- [ ] Tests (the per-GW plan columns; `ask` carries + shows the detail) + live smoke
- [ ] Docs: ADR-036 + index, Architecture, Handbook/README, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-101 | **Gate.** Design (**ADR-036**): the plan table gains per-GW xP columns for the incoming players (join ADR-035 + ADR-032); `ask` returns a **structured detail** table (evolving the ADR-034 result shape) above the narration; tighten the prompt. Pressure-tested (the probe) | Critical | ✅ Done | 0.5 session |
| US-102 | **Per-GW plan table** — thread `by_gameweek` into `render_transfer_plan`; show GW1…GWN (incoming) + gain in `transfer --count`. Tests | High | ✅ Done | 1 session |
| US-103 | **`ask` shows the table** — the plan decision carries a rendered `detail` table; `AskResult`/`render_ask` display it above the prose; tighten the plan prompt. Tests + smoke | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [x] ADR-036 recorded + added to the ADR index — _US-101_
- [ ] Update Architecture changelog (compose plan × per-GW; `ask` structured detail) — _US-102_
- [x] Update Handbook/README (the per-GW plan table; `ask` structured detail) — _US-103_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — the per-GW plan columns; `ask` carries + renders the detail; existing
   301 stay green; no new dependency.
2. **Manual smoke test done** — `transfer --squad TS --count 3` and `ask "which 3 transfers for TS?"`
   on live data; the per-GW table reads correctly and the `ask` output shows table + prose.
3. **Documentation updated & checked** — ADR-036 + index, Architecture, Handbook, README, sprint
   board + PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Per-GW xP columns in the plan table (both surfaces) | New plan logic — the engine (ADR-035) is unchanged |
| `ask` returns a structured detail table | A general structured-output framework for every intent |
| A tighter plan-narration prompt | A bigger/cloud model |
| Reuse `by_gameweek` (ADR-032) | Per-GW *actuals* (needs GW1 — Data Hardening) |

**External Dependencies:** None beyond stored FPL data + a saved squad.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Wide table at large horizons | Med | Narrow GW columns; default horizon 5; a soft cap is a noted refinement |
| `ask` output too busy (table + prose) | Low | Table = the exact data, prose = the summary; both are useful and clearly separated |
| Coupling `ask` to a rendered detail | Low | The plan decision carries a pre-rendered string; `render_ask` just displays it — minimal coupling |
| Per-GW rounding vs total (ADR-032) | Low | Same known artifact; total is authoritative; footnoted |

---

### 🗝️ Gating decision (US-101 → ADR-036)

Settle before code — the probe pressure-tested it. Proposed (confirm/redirect at "start US-101"):

1. **Per-GW plan table.** The plan table shows, per move, the **incoming player's** GW1…GWN xP
   (from `by_gameweek`, ADR-032) + the gain — so a manager sees the weekly shape. Applied to
   `transfer --count` and `ask`.
2. **`ask` returns structured detail.** The plan decision carries a **pre-rendered table** (`detail`);
   `render_ask` shows it above the LLM narration. The LLM still narrates from the self-describing
   facts (ADR-034 unchanged) — the table is the exact data, the prose is the summary.
3. **Tighten the prompt** so the small model doesn't echo the instruction (*"Here is a summary…"*).

**Worked example (already run):** the TS 5-plan's incoming players with GW1–GW5 xP (Benitez 7.0/6.3/
7.0/7.7/7.0 = 35.0, etc.) — reads well and joins two existing features.

---

### 📝 Session Progress Log

- **US-101 (gate) ✅** — Recorded **ADR-036**: a **composition** (ADR-035 plan × ADR-032 per-GW xP),
  not new modelling. Confirmed: the plan table gains **GW1…GWN columns for the incoming player** (bank
  → footer, OUT kept for context); **`ask` returns a structured `detail`** (a pre-rendered table shown
  above the narration — a small evolution of the ADR-034 result shape; the LLM still narrates only the
  self-describing facts). Tighten the plan prompt (no instruction echo). Engine + grounding contract
  unchanged; reuses the shared renderer + `by_gameweek`. Pressure-tested on the TS 5-plan.
- **US-102 (per-GW plan table) ✅** — `render_transfer_plan` gained dynamic **GW1…GWN columns of the
  incoming player's** per-GW xP (via `_plan_columns` + a threaded `by_gameweek_by_id`; bank → footer,
  OUT kept for context); `transfer --count` passes the per-GW data. **+1 test** → suite **301 → 302**;
  ruff clean. Live smoke: `transfer --squad TS --count 3` shows Benitez 7.0/6.3/7.0/7.7/7.0 etc.,
  total +49.0.
- **US-103 (`ask` shows the table) ✅** — `AskResult` gained a `detail` field; the plan decision
  carries a pre-rendered `render_transfer_plan` table (no headline); `render_ask` shows **detail
  (table) → narration**; `_squad_xp` now also returns per-GW. **Tightened the prompt** ("write only
  the explanation — no preamble") — the *"Here is a summary…"* echo is gone. **+2 tests** (detail
  carried; table-before-prose) → suite **302 → 304**; ruff clean. Live smoke: `ask "which 3
  transfers for TS?"` shows the per-GW table + a clean grounded summary. **The owner's retro ask is
  delivered.**

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-101 (ADR-036), US-102 (per-GW plan table), US-103 (`ask`
  structured detail + prompt tighten). The owner's Sprint-33 retro ask is live: the transfer plan now
  shows each **incoming player's points per gameweek**, in `transfer --count` *and* `ask`. Tests 301
  → **304**; one ADR; **no new logic, no new dependency**.
* **Carried Forward:** None. A soft cap for very wide horizons is a noted refinement.
* **Key Artifacts / Decisions:** ADR-036 (compose ADR-035 × ADR-032; `ask` returns a structured
  `detail`); `_plan_columns`, `AskResult.detail`, the tighter prompt.

#### Retrospective
* **What Went Well?**
  - **Pure composition** — the per-GW plan table is a *join* of the plan (ADR-035) and the per-GW
    breakdown (ADR-032). No new modelling; the engine and grounding contract were untouched.
  - **`ask` gained hard data** — a structured table *above* the prose, keeping the philosophy intact
    (the table is the truth; the LLM narrates the summary). A minimal result-shape evolution (`detail`).
  - **The prompt tighten worked** — the *"Here is a summary…"* echo is gone with one instruction.
  - **Reused the shared renderer** — dynamic GW columns, exactly as `analyse`/`xp` do. DoD held (34th).
* **What Could Be Improved?**
  - **Table width** grows with the horizon (per-GW columns) — fine at the default 5; a compact form
    for large N is deferred.
  - **`ask` layering** — `ask.py` now imports a UI renderer (`render_transfer_plan`) to build the
    `detail`. Pragmatic and ADR-sanctioned, but a mild inversion; a data-only `detail` rendered by the
    view would be purer if it grows.
* **Lessons Learned?**
  - Mature features *compose* — reach for a join before a rebuild.
  - A natural-language layer can still surface hard data (a table), not just words.
  - A one-line prompt instruction can fix a persistent output artifact.
* **Action Items for Next:**
  - [ ] (Backlog) a compact/soft-capped per-GW table for large horizons; a data-only `ask` detail.
  - [ ] **Data Hardening** at ~GW1 (2026-08-21); or more Phase 4 / the web UI — owner to steer.
  - [ ] Keep gate + 3-part DoD.

---

**Proposed follow-on:** owner to steer — more Phase 4, the web UI (Phase 2), or wait for GW1 to do
Data Hardening. All live.

**Completion Date:** 2026-08-04
**Final Notes:** A clean composition sprint — the plan shows *when* the points land, and `ask` shows
the exact table under its prose, both from features we already had. Sprint outcome: **Successful** —
3/3 stories, zero roll-over, DoD held.
