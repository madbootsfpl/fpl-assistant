# Sprint 033: Deepen Phase 4 — multi-transfer plans ("recommend N transfers")

**Dates:** 2026-08-04
**Status:** ✅ Complete (3/3 stories, retro done)
**Capacity:** ~3 working sessions (an analytics extension + wiring `transfer` and `ask`)
**Carried Over:** None (Sprint 032 closed clean)

> **Direction (owner's Sprint-32 retro note):** *"I may have 1–5 transfers available depending on
> what I've used/banked… would be good to have as an option, e.g. 'which 3 transfers would you
> recommend for team TS'."* So: a **coordinated N-transfer plan**, surfaced in both `transfer` and
> `ask`.

---

### 🔎 Verified at planning (the standing lesson — coordination beats a shortlist)

The current `transfer --limit N` shows the top N **independent** single upgrades — each assumes it
has the whole bank to itself, so executing them as a *set* can overspend or double-buy. A greedy
**coordinated** plan (threads the shared bank, updates club counts, no re-buy) was probed on "TS"
(3 transfers, start bank £0):

| # | Move | Gain | Note |
|---|---|--:|---|
| 1 | Kelleher (£5.0) → Benitez (£4.5) | +15.4 | frees **£0.5** into the bank |
| 2 | Slater (£4.5) → **Dasilva** (£5.0) | **+26.6** | affordable *only* because of that £0.5 |
| 3 | Ampadu (£5.5) → Adli (£5.0) | +7.0 | Dasilva already owned → picks Adli (no double-buy) |

**Total +49.0 xP.** The naive independent top-3 couldn't reach Slater→Dasilva (unaffordable at bank
£0 → settled for Slater→Reed +9.9). So **threading the bank unlocks materially better moves**, and
the plan stays legal (shared budget, ≤3/club across the set, each player used once). Greedy is
simple, explainable, and — as shown — strong.

**Also:** still preseason; ClubElo intermittent (degrades fine). **No new dependency.**

---

### 🧭 What's new — a *plan*, not a shortlist

Every recommendation so far is a single call ("the best captain", "the best transfer", "your
squad's health"). This is the first that reasons over a **sequence**: N transfers that are jointly
legal and jointly better, sharing one bank. It deepens the transfer intent for `ask` (*"which 3
transfers for TS?"*) and adds `transfer --count N`. The count is an **input** — FPL free transfers
aren't knowable (no auth), so the manager says how many they have.

---

### 🎯 Sprint Goal

**Objective:** A **coordinated N-transfer plan** (greedy: best legal move given the running state,
repeated) — surfaced as `transfer --count N` and via `ask "which N transfers for <squad>?"` —
threading the shared bank, ≤3/club across the set, and no re-buy. Honest about greedy ≠ globally
optimal, and about hits.

#### Success Criteria
- [ ] Approach agreed (**ADR-035**) before code — greedy coordinated plan; count as input; hits deferred
- [ ] A pure `suggest_transfer_plan` — up to N moves, each best given the **updated** state (bank,
      club counts, players used); positive-gain only; stops early if none
- [ ] **The shared bank threads** (a later move can spend what an earlier sale freed) — proven on TS
- [ ] **No double-buy / no re-buy** (a bought player can't be bought again; a sold player can't return)
- [ ] `transfer --count N` shows the plan (running bank + total gain); `--count 1` = today's behaviour
- [ ] `ask "which N transfers for <squad>?"` — parse N, route to the plan, humanise + narrate
- [ ] Honest caveats: greedy (not guaranteed optimal); the count = free transfers you have (hits not modelled)
- [ ] Tests (bank threading, no double-buy, club limit across the set, count, parse N) + live smoke
- [ ] Docs: ADR-035 + index, Architecture, Handbook/README, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-098 | **Gate.** Multi-transfer plan design (**ADR-035**): greedy coordinated N-transfers (thread bank, update clubs, no re-buy); count as input; positive-gain; greedy-not-optimal + hits-deferred caveats. Pressure-tested (the TS Slater→Dasilva unlock) | Critical | ✅ Done | 0.5 session |
| US-099 | **`suggest_transfer_plan` + `transfer --count`** — pure greedy planner reusing `suggest_transfers`' constraints; the `transfer` command's plan mode + view (running bank, total gain). Unit-tested | High | ✅ Done | 1.5 sessions |
| US-100 | **`ask` N-transfer intent** — parse "N transfers" from the question; humanise the plan (the move list + total gain); narrate. Tests + smoke | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [x] ADR-035 recorded + added to the ADR index — _US-098_
- [x] Update Architecture changelog (a sequence plan, not a single call) — _US-099_
- [x] Update Handbook/README (`transfer --count`, `ask "N transfers"`) — _US-100_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — bank threading, no double-buy, club-limit-across-the-set, count, the
   `ask` N-parse; existing 294 stay green; no new dependency.
2. **Manual smoke test done** — `transfer --squad TS --count 3` and `ask "which 3 transfers for TS?"`
   on live data; the plan is legal (bank never negative, ≤3/club, no repeats) and reads correctly.
3. **Documentation updated & checked** — ADR-035 + index, Architecture, Handbook, README, sprint
   board + PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| A greedy **coordinated** N-transfer plan | A globally-optimal (ILP) plan — greedy is enough, and explainable |
| Shared bank threading, ≤3/club across the set, no re-buy | Hit (−4) optimisation — the count = free transfers you *have* |
| `transfer --count N` + `ask "N transfers"` | Knowing your real free-transfer count / bank (no auth) |
| Positive-gain moves only | Multi-week transfer *sequencing* (which week to move) |

**External Dependencies:** None beyond stored FPL data + a saved squad.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Greedy isn't globally optimal | Med | Honest caveat; the probe shows it's strong; ILP would be marginal + opaque |
| Bank goes negative across moves | High | Affordability checked against the **running** bank each step; a test asserts it |
| Double-buy / sell-then-rebuy | High | Bought → owned (excluded); sold → excluded from future buys; unit-tested |
| ≤3/club breaks as a set | High | Club counts updated after each move; the per-candidate check runs on the updated state |
| User over-reads "N transfers" | Low | State: count = the free transfers you have; hits aren't modelled |

---

### 🗝️ Gating decision (US-098 → ADR-035)

Settle before code — the probe pressure-tested it. Proposed (confirm/redirect at "start US-098"):

1. **Greedy coordinated plan.** Repeatedly take the best legal single transfer given the **current**
   state (owned, running bank, club counts, players already used), apply it, repeat up to N. Reuses
   `suggest_transfers`' constraint logic on the evolving state. Positive-gain only; stop early.
2. **Count is an input** (`--count N`, or "N transfers" in `ask`), default 1. The tool can't know your
   free transfers (no auth), so you say how many.
3. **Hits deferred.** The count assumes N *free* transfers; −4 hit optimisation stays on the Backlog
   (the full multi-move *planner*). Stated in the output.
4. **Greedy ≠ optimal** — honest caveat; each move is best given the last, not a joint optimum.

**Worked example (already run):** on "TS", the coordinated 3-plan threads a £0.5 sale into an
otherwise-unaffordable Slater→Dasilva (+26.6) — total +49.0, no double-buy — vs the naive shortlist.

---

### 📝 Session Progress Log

- **US-098 (gate) ✅** — Recorded **ADR-035**: a **greedy coordinated** N-transfer plan
  (`suggest_transfer_plan` wraps `suggest_transfers` over the evolving state — threads the shared
  bank, recomputes club counts, excludes sold/bought players). **Correct by construction:** bank
  can't go negative (the affordability invariant), no double-buy (bought→owned), no re-buy
  (sold→out of market), ≤3/club across the set. `count` is an input (`--count`, opt-in; default =
  today's shortlist). Caveats recorded: greedy ≠ optimal; hits not modelled (count = free transfers
  you have). Pressure-tested on TS (Slater→Dasilva +26.6 unlocked by a £0.5 sale; total +49.0).
- **US-099 (`suggest_transfer_plan` + `transfer --count`) ✅** — Built the pure greedy planner (wraps
  `suggest_transfers` over the evolving state; annotates `bank_after`) + a plan view
  (`render_transfer_plan`, ordered moves + running bank + total) + `transfer --count N` (opt-in;
  shortlist unchanged without it). **5 tests** — bank-threads, no-double-buy, club-limit-across-set,
  bank-never-negative, stops-early → suite **294 → 299**; ruff clean. Live smoke: `transfer --squad
  TS --count 3` reproduced the probe (Kelleher→Benitez, Slater(b)→Dasilva, Ampadu→Adli, +49.0).
- **US-100 (`ask` N-transfer intent) ✅** — `_transfer_count` parses the N (a digit before
  "transfer(s)"; else 1); `_plan_facts` humanises the plan (self-describing move list + total);
  `_decide_transfer` branches to `suggest_transfer_plan` when count > 1; `answer` threads the parsed
  count. **+2 tests** (count parse, plan facts) → suite **299 → 301**; ruff clean. Live smoke:
  `ask "which 3 transfers for TS?"` → grounded narration of the +49.0 plan. Handbook Ch 21 + README
  updated. **The owner's retro ask is delivered.**

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-098 (ADR-035), US-099 (`suggest_transfer_plan` +
  `transfer --count`), US-100 (`ask "which N transfers"`). The owner's Sprint-32 retro ask is live:
  a **coordinated multi-transfer plan**, surfaced as a table *and* in plain English. Tests 294 →
  **301**; one ADR; **no new dependency, no schema change**.
* **Carried Forward:** None. The hit-optimising / multi-week / ILP planner stays on the Backlog.
* **Key Artifacts / Decisions:** ADR-035 (greedy coordinated plan; correct by construction; count as
  input; hits deferred); `suggest_transfer_plan`, `render_transfer_plan`, `_transfer_count` /
  `_plan_facts`.

#### Retrospective
* **What Went Well?**
  - **Coordination unlocked real value** — threading the shared bank found Slater→Dasilva (+26.6) that
    the independent shortlist couldn't afford; the TS 3-plan totals +49.0.
  - **Correct by construction, by reuse** — the planner wraps `suggest_transfers` over the evolving
    state, so bank-can't-go-negative, no-double-buy, no-re-buy, and ≤3/club-across-the-set fall out of
    rules already proven for single transfers. Each is a small explicit test.
  - **Two surfaces, one engine** — `transfer --count` and `ask "which N transfers"` share the same
    planner; the LLM narrates the plan grounded (self-describing facts).
  - **Greedy over ILP** — explainable ("each move best given the last"), and the probe showed it's
    strong. DoD held (33rd sprint).
* **What Could Be Improved?**
  - **Greedy isn't globally optimal** — it won't take a worse move 1 to fund a better move 2. Honest
    caveat; an ILP variant is a later option if it ever matters.
  - **Count parsing is digits-only** ("3 transfers", not "three"), and hits aren't modelled — both
    stated. A richer NL parse / a hit-aware planner are future work.
* **Lessons Learned?**
  - Reuse the single-step engine over an evolving state — don't write a new optimiser for a sequence.
  - Make correctness structural (invariants that hold by construction) and pin each with a test.
  - Share one engine behind two surfaces (a command + `ask`) rather than duplicating logic.
* **Action Items for Next:**
  - [ ] (Backlog) a hit-aware / multi-week / ILP transfer planner; a richer count parse ("three").
  - [ ] **Data Hardening** at ~GW1 (2026-08-21); or more Phase 4 / the web UI — owner to steer.
  - [ ] Keep gate + 3-part DoD.

---

**Proposed follow-on:** owner to steer — more Phase 4 depth, the web UI (Phase 2), or wait for GW1
to do Data Hardening. All live.

**Completion Date:** 2026-08-04
**Final Notes:** The first recommendation over a *sequence* — coordinated, correct by construction,
and delivered on both surfaces (a table and plain English). Reusing the single-transfer engine over
an evolving state kept it small and safe. Sprint outcome: **Successful** — 3/3 stories, zero
roll-over, DoD held.
