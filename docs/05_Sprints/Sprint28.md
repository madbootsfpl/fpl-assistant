# Sprint 028: Transfer Suggestions (Phase 3, feature 2 of 3)

**Dates:** 2026-08-03
**Status:** ✅ Complete (3/3 stories, retro done)
**Capacity:** ~3 working sessions (the meatiest decision-support feature)
**Carried Over:** None (Sprint 027 closed clean)

> **Sequence (owner's "do in order"):** **028 — Transfers** → 029 — Team Analyser → 030 — Data
> Hardening. Each is its own sprint. Data hardening sits last: per-GW history + in-season form
> blending can't happen until GW1 is played.

---

### 🔎 Verified at planning (the standing lesson — probed a real squad)

Pressure-tested a transfer suggestion on the saved squad **"TS"** before designing:

- **It works and is useful.** Over a 5-GW horizon, the weakest owned outfield player is **Slater
  (MID, £4.5m, xP5 = 0.0)**; the best self-funding, same-position, available replacement is **Reed
  (£4.5m, xP5 = 9.9)** — a **+9.9 xP** upgrade for £0 net. Sensible, explainable.
- **The bank is unknown** (we deferred `/my-team/` auth). So budget for a replacement = **sold
  player's price + a `--bank` figure the user supplies** (default £0 = a self-funding swap). Honest
  and simple.
- **Transfers are a multi-week commitment**, so the xP comparison uses a **horizon** (default 5 GW)
  — unlike captaincy's single GW.
- **The constraints are all derivable** from stored data: same position (FPL keeps 2/5/5/3), not
  already owned, available (`is_unavailable`), ≤3 per club, affordable. Reuses saved squads
  (ADR-024), xP (ADR-028), and the shared renderer (ADR-025).

**What this means:** transfer suggestions are another **composition** — xP-over-a-horizon + the
squad + FPL's constraints — that *recommends and explains* a move. FPL-native; no new dependency.
ClubElo re-checked — still down (timeout).

---

### 🧭 What's new — the app suggests a *change*, with the rules baked in

Captaincy picked from what you own; transfers propose **swapping** a player out for a better one —
the first feature that respects FPL's **transfer rules** (same position, ≤3/club, budget). The core
is a single-transfer engine: for each owned player, find the best affordable, legal, available
same-position replacement, ranked by **xP gain over the horizon**. It states the move *and why*
(OUT → IN, prices, the xP delta), and is honest about what it can't see (your real bank; hits).

---

### 🎯 Sprint Goal

**Objective:** A `transfer --squad <name>` command that recommends the best **single** transfers for
a saved squad — each a legal, affordable, same-position upgrade ranked by xP gain over a horizon,
and **explained** (OUT → IN, prices, Δ). Honest about the unknown bank (`--bank`) and single-move
scope (hits noted, not optimised).

#### Success Criteria
- [ ] Approach agreed (**ADR-030**) before code — single-transfer, self-funding+`--bank`, horizon, constraints
- [ ] A `suggest_transfers` analytics fn: for a squad, the best legal replacement per owned player,
      respecting **position, ≤3/club, budget (sale + bank), availability, not-already-owned**
- [ ] Ranked by **xP gain over a horizon** (default 5 GW); only positive-gain moves suggested
- [ ] `transfer --squad <name>` command (+ `--bank`, `--next`, `--limit`) + an explain-why view (OUT → IN, Δ)
- [ ] Graceful: unknown squad name (list saved); departed players; a squad with no upgrade available
- [ ] Honest caveats shown: unknown bank (`--bank £0` default); single move (hits not optimised); xP is a mean
- [ ] Tests (gain ranking, each constraint, self-funding vs `--bank`, no-upgrade case) + **live smoke**
- [ ] Docs: ADR-030 + index, Architecture changelog, Handbook, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-083 | **Gate.** Transfer-suggestion design (**ADR-030**): single-transfer upgrades for a saved squad; budget = sale + `--bank` (default 0); xP gain over a horizon; constraints (position, ≤3/club, availability, owned); explain OUT → IN; hits/multi-move deferred. Pressure-test on a real squad | Critical | ✅ Done | 0.5 session |
| US-084 | **`suggest_transfers` analytics** — best legal replacement per owned player (position / ≤3-club / budget / availability / not-owned), ranked by xP-gain over the horizon; positive gains only. Pure + unit-tested | High | ✅ Done | 1.5 sessions |
| US-085 | **`transfer` command + view** — `transfer --squad <name>` (+ `--bank`/`--next`/`--limit`); an explain-why table (OUT → IN, prices, Δ); graceful edge cases. Tests + smoke | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [x] ADR-030 recorded + added to the ADR index — _US-083_
- [x] Update Architecture changelog (transfer engine; first rule-respecting change) — _US-084_
- [x] Update Handbook (Ch 21 — recommending a change means respecting the rules; honest unknowns) — _US-085_
- [x] Backlog: multi-move transfer *planner* (hits vs roll, −4 maths) noted as a future feature — _US-085_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — gain ranking + every constraint + budget modes + edge cases; existing 249 green.
2. **Manual smoke test done** — `transfer --squad TS` on live data; the suggested moves are legal,
   affordable, and the reasons read correctly.
3. **Documentation updated & checked** — ADR-030 + index, Architecture, Handbook, sprint board +
   PROJECT_STATUS (Charter Documentation Rules).

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Best **single** transfers for a saved squad | Multi-move plans / hit (−4) optimisation — a follow-on |
| Legal (position, ≤3/club), affordable (sale + `--bank`) | Knowing your real bank / auto-fetching `/my-team/` |
| Ranked by xP gain over a horizon, explained | A new score (reuses xP) |
| Availability + not-already-owned filters | xMins/rotation weighting (later) |

**External Dependencies:** None beyond stored FPL data + a saved squad (`squad --save`).

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Unknown bank → wrong budget | High | `--bank` (default £0 = self-funding); state the assumption in the output |
| Suggesting an illegal move (4th from a club) | High | Enforce ≤3/club per candidate (accounting for the outgoing player); unit-tested |
| Single-move ≠ optimal season plan | Med | Scope to the best single transfers (1 FT); note the multi-move planner as a follow-on |
| xP is a mean; a differential won't stand out | Low | Honest caveat (as captaincy); ceiling view is Backlog |
| "It's just two xP lookups" | Med | The value is the constraint-respecting, affordable, explained *move* — not a ranking |

---

### 🗝️ Gating decision (US-083 → ADR-030)

Settle before code — pressure-test on a real squad. Proposed (confirm/redirect at "start US-083"):

1. **Scope: best single transfers.** For each owned player, the best legal affordable same-position
   replacement; rank all such moves by xP gain over the horizon; suggest the top N (the #1 is your
   1-free-transfer recommendation). *Deferred:* multi-move plans + hit (−4) optimisation → Backlog.
2. **Budget = sale price + `--bank`.** The bank isn't knowable (no auth), so default £0 (self-funding)
   and let the user supply their bank. State it in the output.
3. **Metric: xP gain over a horizon** (default 5 GW — transfers are multi-week). Only positive gains.
4. **Constraints:** same position; not already owned; available (`is_unavailable`); ≤3 per club
   (accounting for the outgoing player freeing a slot). Reuse the optimiser's club-limit notion.
5. **Explain the move:** OUT (price, xP) → IN (price, xP), the Δ, and the caveats.

**Worked example to verify at the gate:** on squad "TS", show the top transfer (Slater → Reed, +9.9
over 5 GW) and confirm a candidate that would break ≤3/club or the budget is correctly rejected.

---

### 📝 Session Progress Log

- **US-083 (gate) ✅** — Pressure-tested the full transfer engine on squad "TS" (5-GW horizon):
  top moves sensible + self-funding (Kelleher→Benitez +15.4, Slater→Reed +9.9). **Constraints proven
  live:** ≤3/club (MCI at 3 → candidates restricted), budget (`--bank £2` changes the top gain to
  Wilson +27.8). **Two probe findings → ADR-030:** (1) the top move was a GK→GK swap → **transfers
  include GKs** (the mirror of captaincy's GK *exclusion* — a better keeper is a real upgrade);
  (2) the engine is bench-blind, but saved squads store `bench_ids` → **flag** when the OUT player is
  benched (honest, cheap). Recorded ADR-030: single-transfer upgrades; budget = sale + `--bank`;
  xP gain over a horizon; constraints; explain OUT→IN; multi-move/hits → Backlog. ClubElo still down.
- **US-084 (`suggest_transfers` analytics) ✅** — Built the pure engine (`src/analytics/transfer.py`):
  per owned player, the best legal same-position replacement (not-owned / available / affordable /
  ≤3-club), ranked by xP gain, positive only, bench-out flagged. Reuses `MAX_PER_CLUB` +
  `is_unavailable`. **10 unit tests**, one per constraint incl. the ≤3/club **same-club-swap edge
  case** — which caught a *bad test* (my first version expected a block where a legal same-club
  upgrade actually existed; the code was right, the test was wrong → fixed by making the 3 same-club
  players non-MID). Suite **249 → 259**; ruff clean.
- **US-085 (`transfer` command + view) ✅** — `transfer --squad <name>` (+ `--bank`/`--next`/
  `--type`/`--limit`); `render_transfers` shows OUT → IN with prices, xP, Δ and a `(b)` bench flag
  (the shared renderer's 2nd new consumer). Graceful: unknown squad lists saved names; departed
  players drop out; no-upgrade prints a clear message. **3 parser tests** (defaults, required
  `--squad`, `--bank`/`--next`) → suite **259 → 262**; ruff clean. Live smoke on "TS" reproduced the
  gate probe (Kelleher→Benitez +15.4, Slater(b)→Reed +9.9…); `--bank 2.0` unlocked pricier targets
  (Wilson +27.8); unknown-name path lists saved squads.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-083 (ADR-030), US-084 (`suggest_transfers` engine), US-085
  (`transfer` command + view). The app now recommends **transfers** as well as captaincy — and the
  first feature that respects FPL's **transfer rules** (same position, ≤3/club, budget). Composes xP
  + saved squads + the optimiser's club rule. Tests 249 → **262**; one ADR; **no new dependency, no
  schema change**.
* **Carried Forward:** None. A multi-move transfer *planner* (hits vs roll) is on the Backlog.
* **Key Artifacts / Decisions:** ADR-030 (single-transfer upgrades; budget = sale + `--bank`; xP
  gain over a horizon; ≤3/club with the freed-slot case; **GKs included**; bench **flagged**);
  `suggest_transfers` (pure), `transfer` command, `render_transfers`.

#### Retrospective
* **What Went Well?**
  - **A rule-respecting recommendation.** Transfers must be *legal* to be useful — same position,
    ≤3/club, affordable — and the engine enforces all of it, reusing the optimiser's `MAX_PER_CLUB`.
  - **Composition again** — xP-over-a-horizon + saved squads + the club rule + the shared renderer
    (its 2nd new consumer). The whole feature added ~one analytics fn + one view + one command.
  - **A test caught a *test*.** The ≤3/club case has a subtlety (selling a same-club player frees a
    slot); my first test expected a block where a legal same-club swap actually existed. The code was
    right — the test was wrong. Testing each constraint in isolation is what surfaced it.
  - **Honest about the unknowns** — the bank is an input (`--bank`, default £0), and bench players
    are flagged, not silently modelled. Stated assumptions beat guesses.
  - Probe-driven again: GKs *included* (the mirror of captaincy) came from seeing a GK→GK upgrade top
    the real board. DoD held (28th sprint).
* **What Could Be Improved?**
  - **Bench-blindness** — ranking by xP across all 15 over-values a bench upgrade. The `(b)` flag is
    an honest stopgap; proper starter/bench (xMins) weighting is a later phase.
  - **Single-move only** — the genuinely hard FPL question (a −4 hit vs rolling, multi-week plans) is
    deferred to the planner. This sprint is the foundation it'll build on.
* **Lessons Learned?**
  - A recommendation that breaks the domain's rules is worse than none — encode + test each rule.
  - State what you can't see (bank, who starts) as inputs/flags rather than guessing.
  - Pure analytics (data in → moves out) makes every constraint trivially unit-testable.
* **Action Items for Next Sprint (029 — Team Analyser):**
  - [ ] Grade a saved squad's health over the next N GWs (xP + fixtures + availability) — composing
        the same pieces. Check first.
  - [ ] Once xMins exists: weight transfers/captaincy by expected minutes (retire bench-blindness).
  - [ ] Keep gate + 3-part DoD; re-check ClubElo (still down).

---

**Proposed follow-on (Sprint 029):** Team Analyser — the next in the sequence: grade a saved squad's
health / fixtures / weak spots over a horizon, composing xP + saved squads + availability.

**Completion Date:** 2026-08-03
**Final Notes:** Transfers landed cleanly by composition, with the FPL rules encoded and tested (a
bad test caught along the way sharpened the ≤3/club logic). The app now advises on captaincy *and*
transfers. Sprint outcome: **Successful** — 3/3 stories, zero roll-over, DoD held.
