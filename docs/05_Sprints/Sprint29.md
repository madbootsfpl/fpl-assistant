# Sprint 029: Team Analyser (Phase 3, decision-support capstone)

**Dates:** 2026-08-04
**Status:** ✅ Complete (3/3 stories, retro done)
**Capacity:** ~3 working sessions (aggregation + a rich summary view)
**Carried Over:** None (Sprint 028 closed clean)

> **Sequence (owner's "do in order"):** 028 — Transfers ✅ → **029 — Team Analyser** → 030 — Data
> Hardening. This closes the decision-support trio (captain · transfer · analyse).

---

### 🔎 Verified at planning (the standing lesson — probed a real squad)

Checked what a squad health-check needs against the saved squad **"TS"** before designing:

- **Everything is already there — it's aggregation, not new modelling.** From the saved squad +
  xP + availability we get: **XI projected 278.1 xP over 5 GW**, bench 29.8, **0 availability
  issues** (preseason), weakest XI links (Ampadu 19.4, Kelleher 19.6 → transfer candidates), and
  club concentration (MCI 3, LIV 2, TOT 2).
- **The XI/bench split is available** — saved squads store `bench_ids` (TS has 4), so the starting
  XI is the 11 non-bench; only the XI's xP is "projected points" (the bench doesn't score). For a
  squad saved *without* a declared bench, the best legal XI can be picked with the optimiser we
  already own (`select_squad`, ADR-008).
- **The forward-looking fixture view is already inside xP** — xP over the horizon is
  fixture-difficulty-adjusted (ADR-006/007), so "how do the next N GW look?" is the xP projection.

**What this means:** the analyser is the **capstone that composes the trio's pieces** — saved squads
(ADR-024) + xP-over-a-horizon (ADR-028) + availability (ADR-023) + the optimiser (ADR-008) + the
shared renderer (ADR-025) — into one *"here's your squad's health"* view. FPL-native; **no new
dependency, no schema change**. ClubElo re-checked — still down (timeout).

---

### 🧭 What's new — the app *summarises*, not just answers one question

`captain` and `transfer` each answer a single question. The analyser is the **overview**: given
your squad, what's its projected haul, where are the problems (injuries, weak links), how strong is
the bench, how concentrated are your clubs. It **links to the other tools** — a weak link is a
`transfer` candidate; the top XI player is your `captain` lead — turning three point-features into a
coherent workflow. Honest by design: it shows **indicators**, not a made-up letter grade.

---

### 🎯 Sprint Goal

**Objective:** An `analyse --squad <name>` command that grades a saved squad's health over the next
N gameweeks — projected XI xP, the XI and bench with per-player xP + availability, and highlights
(availability issues, weakest links → transfer hints, club concentration). Composes the existing
pieces; shows indicators, not a fake grade.

#### Success Criteria
- [ ] Approach agreed (**ADR-031**) before code — indicators-not-a-grade; saved squad; XI/bench; horizon
- [ ] A pure `analyse_squad` fn: XI/bench split, **projected XI xP over a horizon**, squad value,
      availability issues, weakest XI links, club concentration
- [ ] XI selection: use the declared bench if present, else the best legal XI (reuse `select_squad`)
- [ ] `analyse --squad <name>` command (+ `--next`, `--type`) + a summary view (XI + bench + highlights)
- [ ] Graceful: unknown squad (list saved), departed players, a squad with no declared bench
- [ ] Cross-links surfaced: weakest links point at `transfer`; the top XI player at `captain`
- [ ] Tests (split, projected xP, issues, weakest, clubs, bench-vs-inferred XI) + **live smoke**
- [ ] Docs: ADR-031 + index, Architecture changelog, Handbook, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-086 | **Gate.** Team-analyser design (**ADR-031**): a health check of a *saved squad* over a horizon; **indicators not a grade**; XI/bench (declared or best-XI); projected XI xP; highlights + cross-links to `captain`/`transfer`. Pressure-test on a real squad | Critical | ✅ Done | 0.5 session |
| US-087 | **`analyse_squad` analytics** (pure) — XI/bench split, projected XI xP over the horizon, value, availability issues, weakest XI links, club concentration. Unit-tested | High | ✅ Done | 1 session |
| US-088 | **`analyse` command + view** — `analyse --squad <name>` (+ `--next`/`--type`); XI selection (declared bench, else `select_squad`); a summary view (XI, bench, highlights). Tests + smoke | High | ✅ Done | 1.5 sessions |

#### Technical Tasks & Maintenance
- [ ] ADR-031 recorded + added to the ADR index — _US-086_
- [x] Update Architecture changelog (the decision-support capstone) — _US-087_
- [x] Update Handbook (Ch 21 — a summary that composes + cross-links; indicators over a grade) — _US-088_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — split, projected xP, issues, weakest, clubs, XI selection; existing 262 green.
2. **Manual smoke test done** — `analyse --squad TS` on live data; the numbers match the probe and
   the highlights read correctly.
3. **Documentation updated & checked** — ADR-031 + index, Architecture, Handbook, sprint board +
   PROJECT_STATUS (Charter Documentation Rules).

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Health check of a saved squad over a horizon | Manager-ID auto-fetch (`/my-team/`) — auth deferred |
| Projected XI xP, availability, weak links, clubs | A made-up letter/number "grade" — show indicators |
| XI/bench (declared or best-XI via the optimiser) | xMins-weighted projections (later phase) |
| Cross-links to `captain` / `transfer` | Running those tools for you (it points, you choose) |

**External Dependencies:** None beyond stored FPL data + a saved squad.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| A fake "grade" implies false precision | Med | Show concrete indicators (projected xP, # issues, weak links), not a letter |
| No declared bench → which 11 start? | Med | Best legal XI via `select_squad` (reuse); note the assumption |
| Bench xP double-read as "projected" | Med | Projected points = **XI only**; bench shown separately as bench strength |
| "It's just `squad --load`" | Med | `--load` is current state; `analyse` is the *forward* view (xP over N GW + problems + links) |
| xP is a mean / assumes minutes | Low | Honest caveat (as captaincy/transfers); xMins is a later phase |

---

### 🗝️ Gating decision (US-086 → ADR-031)

Settle before code — pressure-test on a real squad. Proposed (confirm/redirect at "start US-086"):

1. **Subject: a saved squad** (not a manager-ID fetch — auth deferred). Reuses `SquadStore`.
2. **Indicators, not a grade.** Projected XI xP over the horizon, squad value, # availability issues,
   the weakest XI links, club concentration. No invented letter/number grade (false precision).
3. **XI = the starting eleven.** Use the declared bench if present (XI = the other 11); else the best
   legal XI by xP via `select_squad`. Only the XI's xP is "projected points"; the bench is shown as
   its own strength figure.
4. **Compose + cross-link.** Reuse xP / availability / the optimiser; point weak links at `transfer`
   and the top XI player at `captain` — a workflow, not a silo. Horizon default 5 (`--next`).

**Worked example to verify at the gate:** on "TS", reproduce projected XI 278.1 xP / bench 29.8 /
0 issues / weakest = Ampadu·Kelleher·Truffert, and confirm a squad with no declared bench falls back
to a sensible best-XI.

---

### 📝 Session Progress Log

- **US-086 (gate) ✅** — Pressure-tested on "TS": reproduced XI 278.1 xP / bench 29.8 / 0 issues /
  weakest Ampadu·Kelleher·Truffert, and proved the **no-declared-bench fallback** — `select_squad`
  over the owned 15 returned an Optimal XI with the **same** 278.1 and the **same** 4 bench players.
  Recorded **ADR-031**: health check of a saved squad; indicators-not-a-grade; projected = XI only;
  XI = declared bench else best-XI; cross-links to captain/transfer. ClubElo still down.
- **US-087 (`analyse_squad` analytics) ✅** — Pure fn (owned + xi_ids + xp → indicators): XI/bench
  split, projected XI xP, value, availability issues, weakest links, top pick, club concentration.
  **7 unit tests** (projected-is-XI-only, value, split, weakest/top from XI, issues, clubs, XI order).
- **US-088 (`analyse` command + view) ✅** — `analyse --squad <name>` (+ `--next`/`--type`); XI
  selection (declared bench, else `select_squad`); `render_squad_analysis` (summary + XI + bench +
  cross-linked highlights) — the shared renderer's **3rd new consumer**. **2 parser tests** → suite
  **262 → 271**; ruff clean. Live smoke on "TS" matched the probe exactly (278.1 / bench 29.8;
  Captain lead Haaland; Weakest Ampadu/Kelleher/Truffert with `transfer`/`captain` pointers).

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-086 (ADR-031), US-087 (`analyse_squad`), US-088 (`analyse`
  command + view). The **decision-support trio is complete**: `captain` · `transfer` · `analyse`. The
  analyser grades a saved squad's health over a horizon (projected XI xP, issues, weak links, clubs)
  and **cross-links** the other two. Tests 262 → **271**; one ADR; **no new dependency, no schema
  change**. Built in a single pass (owner approved the gate + build).
* **Carried Forward:** None. Manager-ID auto-fetch (needs auth) and a numeric health score (needs a
  benchmark) are noted for later.
* **Key Artifacts / Decisions:** ADR-031 (indicators-not-a-grade; saved squad; projected = XI only;
  XI = declared bench else `select_squad`; cross-links); `analyse_squad` (pure), `analyse` command,
  `render_squad_analysis`.

#### Retrospective
* **What Went Well?**
  - **Almost pure composition.** The analyser added ~no new computation — it aggregates xP,
    availability, the optimiser's XI pick, and the club rule into one view, and points at `captain`
    and `transfer`. Three Phase-3 features, each mostly *wiring*.
  - **Reused the optimiser for the XI pick.** The no-declared-bench fallback is `select_squad` over
    the owned 15 — proven on TS to return the *same* XI/bench the manager declared. No new
    XI-selection code.
  - **Indicators over a grade.** Projected XI xP, # issues, weak links — concrete, honest numbers the
    manager can read, not a false-precision "B+".
  - **The trio became a workflow** — a weak link points at `transfer`, the top XI at `captain`. The
    features stopped being silos.
  - DoD held (29th sprint): unit tests + live smoke (matched the probe) + docs.
* **What Could Be Improved?**
  - **It summarises, it doesn't decide** — by design, but a future numeric health score (vs a
    benchmark) would let a manager compare weeks/squads. Deferred honestly (no benchmark yet).
  - **Preseason hides the availability value** again — 0 issues on TS, so the "headaches" highlight
    couldn't be shown live (unit-tested; matters in-season).
* **Lessons Learned?**
  - The pay-off of clean one-way-flow layers is *composability* — the whole of Phase 3 leaned on it.
  - Reuse the tool you already own (the optimiser picked the XI) instead of writing a new one.
  - Show indicators and cross-link; let the manager drive.
* **Action Items for Next Sprint (030 — Data Hardening):**
  - [ ] The last in the sequence — a full 567-player history backfill, and (once GW1 plays) per-GW
        `history` + in-season xP blending. **Note the timing:** per-GW/form needs the season started;
        check what's live at planning.
  - [ ] Once in-season data exists: retire bench-blindness / add xMins to captaincy & transfers.
  - [ ] Keep gate + 3-part DoD; re-check ClubElo (still down).

---

**Proposed follow-on (Sprint 030 — Data Hardening):** the last of the owner's three. Partly gated on
GW1 being played (per-GW history + form) — worth checking timing at planning; the full backfill can
happen any time.

**Completion Date:** 2026-08-04
**Final Notes:** The decision-support capstone landed by composition, completing the captain ·
transfer · analyse trio and turning them into a workflow. The whole phase was a demonstration that
clean layers make new features mostly wiring. Sprint outcome: **Successful** — 3/3 stories, zero
roll-over, DoD held.
