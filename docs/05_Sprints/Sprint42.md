# Sprint 042: Squad archetypes — build a squad with low-cost + premium constraints

**Dates:** 2026-08-05
**Status:** ✅ Complete (3/3 stories, retro done)
**Capacity:** ~2–3 working sessions (a gate + an optimiser extension + NL/CLI wiring)
**Carried Over:** None (Sprint 041 closed clean)

> **Direction (owner's Sprint-41 note):** *"I'd like to ask a multi-faceted question like `build me a
> squad for £100M with 3 low cost players and 1 premium player`."* Reason: a couple of players are
> always benched (chip fodder), so cheap enablers make sense; you also want 1–3 premiums. *"The other
> type is a differential — we probably need to define that first."*

---

### 🔎 Verified at planning (the standing lesson)

- **Archetype thresholds pin on data.** Prices: min £4.0, p25 £4.5, p90 £6.0, max £15.5. So **low-cost
  ≤ £4.5m** (190 players — the bench-fodder tier) and **premium ≥ £9.0m** (5 elite) are defensible
  defaults (tunable).
- **The optimiser can take it.** `select_squad` is a PuLP ILP (budget + formation + club cap +
  include/exclude/bench); a "**≥N players in a price band**" is a natural extra constraint.
- **The NL parse works** — every phrasing parsed: "3 low cost … 1 premium" → cheap 3/premium 1;
  "2 premium … 4 budget" → premium 2/cheap 4; "build me a squad for £100m" → none; "1 premium and 3
  cheap and 2 differentials" → cheap 3/premium 1/diff 2.
- **Differentials need data we don't have.** `selected_by_percent` (ownership) is **not stored** → the
  differential is **defined here and deferred** (a follow-up ingests ownership).
- Still preseason (0 GWs); ClubElo up (intermittent).

---

### 🧭 What's new — a squad you can shape

`build_squad` and `squad --full` optimise the best 15 on xP; this sprint lets you **shape** it —
"give me ≥3 cheap enablers and ≥1 premium" — by adding **min-count price-band constraints** to the
ILP, exposed as CLI flags (`--cheap`/`--premium`) and parsed from a natural-language build request.
The optimiser still maximises xP; it just satisfies your structure too, and says so clearly when a
structure can't fit the budget.

---

### 🎯 Sprint Goal

**Objective:** `select_squad` accepts **min-count price-band constraints**; `squad --full --cheap N
--premium M` and `ask "build me a squad for £X with N low-cost and M premium players"` build the best
xP squad that satisfies them (a clear message when infeasible). The **differential** archetype is
**defined** (ownership-based) and deferred with a "coming soon" note.

#### Success Criteria
- [ ] Approach agreed (**ADR-043**) — the archetype definitions (low-cost ≤£4.5m, premium ≥£9.0m,
      tunable; differential defined + deferred); the ILP band-constraint design; the CLI + NL surface
- [ ] `select_squad(..., band_minimums=…)` — ≥N players within a price band; the objective (xP) still
      maximised; **byte-identical when no bands are given** (existing 374 stay green)
- [ ] `squad --full --cheap 3 --premium 1` builds the best xP squad with ≥3 ≤£4.5m and ≥1 ≥£9.0m
- [ ] `ask "build me a squad for £100m with 3 low-cost players and 1 premium player"` does the same,
      grounded + verified
- [ ] **Infeasible** structures (e.g. 5 premiums in £80m) → a clear message, not a crash
- [ ] A requested **differential** → a "defined but needs ownership data (coming soon)" note
- [ ] Tests (band constraints; the parser; infeasibility; CLI flags) + live smoke
- [ ] Docs: ADR-043 + index, Architecture, Handbook/README, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-124 | **Gate.** Archetype design (**ADR-043**): definitions (low-cost ≤£4.5m, premium ≥£9.0m, tunable); the `select_squad` band-constraint interface; NL parsing (proven); **differential defined + deferred** (ownership). Pressure-test feasibility + infeasibility | Critical | ✅ Done | 0.5–1 session |
| US-125 | **Optimiser + CLI** — `select_squad` takes `band_minimums` (≥N in a price band); `squad --full --cheap N --premium M`; infeasible → a clear status/message. Byte-identical without bands. Tests | High | ✅ Done | 1 session |
| US-126 | **NL build** — parse "N low-cost / M premium" (+ a differential "coming soon" note) in `build_squad`; wire to the optimiser; grounded + ✓. Tests + smoke + docs | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-043 recorded + added to the ADR index — _US-124_
- [ ] Update Architecture changelog (squad archetypes) — _US-125/126_
- [ ] Update Handbook/README (`--cheap`/`--premium`; the multi-faceted `ask`) — _US-126_
- [ ] Update PROJECT_STATUS — _US-126_
- [ ] Backlog: the **differential** archetype (needs an ownership ingest) — _US-124_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — band constraints (≥N in a band, objective still maximised); the parser;
   infeasibility; byte-identical without bands; existing **374** stay green; no new dependency.
2. **Manual smoke test done** — `squad --full --cheap 3 --premium 1` and `ask "build me a squad for
   £100m with 3 low-cost players and 1 premium player"` both satisfy the structure; an over-constraint
   gives a clear message; a differential request gives the "coming soon" note.
3. **Documentation updated & checked** — ADR-043 + index, Architecture, Handbook/README, sprint board +
   PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Low-cost + premium band constraints (ILP + CLI + NL) | **Differential** build (needs an ownership ingest — deferred) |
| Infeasibility handling (a clear message) | Per-position archetypes ("a premium forward") — later |
| Reuse `select_squad`, `decision_xp`, `render_squad`, the verifier | Chip-specific squads (Bench Boost etc.) — later |

**External Dependencies:** None now. The differential follow-up needs `selected_by_percent` ingested.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Over-constrained → infeasible ILP | Med | Detect non-Optimal status → a clear "couldn't fit N premiums + M cheap in £X — relax it" message |
| Band constraints change squad output subtly | Low | `band_minimums` optional; byte-identical without it; a test locks the no-band path |
| "budget"/"cheap"/"premium" parse ambiguity | Low | A tested parser (proven); default to no constraint when unclear |
| Premiums are few (5 ≥£9m) | Low | "≥1–3 premium" is satisfiable; a larger ask → the infeasible message |
| Differential expectations | Low | Clearly "defined, coming soon (needs ownership data)" — no half-baked version |

---

### 🗝️ Gating decision (US-124 → ADR-043)

Settle before code — the thresholds + parse are pinned. Proposed (confirm/redirect at "start US-124"):

1. **Archetypes.** **low-cost** = price ≤ **£4.5m**; **premium** = price ≥ **£9.0m** (both tunable
   constants). **differential** (defined, deferred) = low ownership (`selected_by_percent` ≤ ~10%) with
   a decent xP — needs an ownership ingest, so a follow-up.
2. **Optimiser.** `select_squad(..., band_minimums=[(count, lo, hi), …])` — each band adds an ILP
   constraint `Σ x_i (lo ≤ price_i ≤ hi) ≥ count`; xP is still the objective. Absent → today's behaviour.
3. **Surface.** CLI `--cheap N` / `--premium M` (→ bands); NL "N low-cost / M premium" parsed in
   `build_squad`. Infeasible → a clear message; a differential request → a "coming soon" note.
4. **Grounded + optional**, like every intent — reuse `render_squad` + the verifier.

**Worked example (to run at the gate):** `--cheap 3 --premium 1` → an Optimal 15 with ≥3 ≤£4.5m and ≥1
≥£9.0m; `--premium 6` → infeasible → a clear message.

---

### 📝 Session Progress Log

- **US-124 (gate) ✅** — Recorded **ADR-043**, design pinned on the live DB + the actual `select_squad`
  PuLP code:
  - **Thresholds:** low-cost **≤£4.5m** (190 players), premium **≥£9.0m** (5: Haaland, B.Fernandes,
    Saka, Palmer, Isak) — tunable constants.
  - **ILP addition proven trivial:** one line before `solve()` — `Σ pick[p] (lo ≤ price ≤ hi) ≥ count`
    — via a `band_minimums=[(count, lo, hi), …]` param (byte-identical when absent).
  - **Feasibility:** "≥3 cheap + ≥1 premium" satisfiable; **"≥6 premium" impossible** (only 5 exist) →
    the non-Optimal message path. NL parse handled every phrasing.
  - **Differential defined + deferred:** low ownership (`selected_by_percent` ≤ ~10%) + decent xP —
    `selected_by_percent` isn't stored, so a follow-up (ownership ingest); added to the Backlog. A
    requested differential → a "coming soon" note.
  Settled: `select_squad(band_minimums=…)`; CLI `--cheap N`/`--premium M`; NL parse in `build_squad`;
  infeasible → a clear message. ADR-043 indexed.
- **US-125 (optimiser + CLI) ✅** — `select_squad` gained `band_minimums=[(count, lo, hi), …]` → one ILP
  line (`Σ pick[p] (lo ≤ price ≤ hi) ≥ count`); **byte-identical when absent**. `archetype_bands(cheap,
  premium)` translates counts → bands using tunable `LOW_COST_MAX=4.5` / `PREMIUM_MIN=9.0`. `squad
  --full --cheap N --premium M` wires them; an infeasible result (bands + non-Optimal) prints a clear
  *"relax --cheap/--premium or raise the budget"* message. **+4 tests** (`archetype_bands`; a band forces
  a low-scoring premium in while staying optimal; an infeasible band → non-Optimal; the CLI flags) →
  suite **374 → 378**; ruff clean; no new dependency. **Live smoke:** `--cheap 3 --premium 1` → a 15
  with 3 ≤£4.5m + B.Fernandes (£12); `--premium 6` → the clear message (only 5 premiums exist); no bands
  → unchanged (305.8 xP).
- **US-126 (NL build) ✅** — `_archetype_counts` parses "(low_cost, premium, differential)" counts from a
  build request; `_decide_build_squad` builds the bands, passes `band_minimums` to `select_squad`, and
  on a non-Optimal result returns a clear message naming the requested structure. A parsed
  **differential** → a "coming soon" note (defined, needs ownership data); the requested structure is
  added to the grounded facts. **+2 tests** (the parser on the owner's exact phrasing + others; routing
  the multi-faceted question to `build_squad`) → suite **378 → 380**; ruff clean; no new dependency.
  **Live smoke:** the owner's `ask "build me a squad for £100M with 3 low cost players and 1 premium
  player"` → a 15 with 3 ≤£4.5m + B.Fernandes (£12); a differential request → the coming-soon note; "5
  premiums in £70m" → the clear message. *(Note: the ✓/⚠ line correctly ⚠-flagged an LLM fabrication —
  invented per-group cost figures not in the facts — the grounding verifier working as designed.)*
  Docs: Architecture, README.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — the owner's multi-faceted build. **US-124** — ADR-043 (archetypes
  pinned on data; the ILP interface; differential defined + deferred). **US-125** —
  `select_squad(band_minimums=…)` + `archetype_bands` + `squad --full --cheap N --premium M`. **US-126**
  — the NL parse in `build_squad` + the differential "coming soon" note. Tests 374 → **380**; one ADR;
  **no new dependency**.
* **Carried Forward:** None. The **differential** build is a Backlog follow-up (needs an ownership ingest).
* **Key Artifacts / Decisions:** ADR-043; `band_minimums` on `select_squad`; `archetype_bands` +
  `LOW_COST_MAX`/`PREMIUM_MIN`; `_archetype_counts`; the CLI `--cheap`/`--premium`.

#### Retrospective
* **What Went Well?**
  - **A real feature from one sentence.** "3 low cost + 1 premium" became a clean, general ILP addition
    (`band_minimums`) that powers both the CLI and the NL build — one seam, two surfaces.
  - **Infeasibility came for free.** The ILP status already distinguishes "no solution", so an
    over-constrained ask (≥6 premiums) gives a friendly message with zero special-casing.
  - **Byte-identical without bands.** The optional param means every existing squad/build path is
    untouched — a test locks it.
  - **Honest scoping of the differential.** Defined it properly (ownership, not price), refused a
    misleading price proxy, deferred the build with a clean note — matching the owner's "define it first".
  - **The grounding guardrail proved itself live.** The build narration invented per-group cost figures;
    the ✓/⚠ line ⚠-flagged them — a real demonstration that the verifier catches fabrication.
* **What Could Be Improved?**
  - **The build narration is prone to invention** (it flagged ⚠). The table is authoritative and the ⚠
    is honest, but a tighter task/prompt could reduce needless fabrication. A small future polish.
  - **Archetype thresholds are global** (£4.5 / £9.0). Per-position premiums ("a premium forward") is a
    natural later extension the band interface already supports.
* **Lessons Learned?**
  - Turn a request into the smallest general primitive (a price-band count), not a bespoke feature.
  - Let the solver's own status carry the error — don't reinvent feasibility checks.
  - Scope honestly: define the hard part, ship the easy part, defer the data-blocked part cleanly.
* **Action Items for Next:**
  - [ ] (Backlog) the **differential** — ingest `selected_by_percent`, then a band/predicate + a parsed count.
  - [ ] (Polish) tighten the build-squad narration task to reduce ⚠ fabrications.
  - [ ] Keep the gate probe broad; keep the 3-part DoD.

---

**Proposed follow-on:** owner to steer — the differential (ownership ingest), more Phase 4 (an intent
classifier / chat), the web UI (Phase 2), or wait for GW1 for Data Hardening + the full Phase-5 xMins.

**Completion Date:** 2026-08-05
**Final Notes:** The manager can now *shape* the squad — enablers + premiums — while it stays
xP-optimal, from the CLI and in plain English; over-asks fail gracefully, and the differential is
honestly "coming soon". Sprint outcome: **Successful** — 3/3 stories, zero roll-over, DoD held (42nd).
