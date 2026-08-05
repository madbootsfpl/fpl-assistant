# Sprint 046: XI-aware transfers — rank by the improvement to your fielded team

**Dates:** 2026-08-05
**Status:** ✅ Complete (3/3 stories; retro done)
**Capacity:** ~2–3 working sessions (a gate + a fast best-XI + XI-aware transfers across surfaces)
**Carried Over:** None (Sprint 045 closed clean)

> **Direction (owner):** the follow-on to bench-aware builds — an **XI-aware `transfer`**. Today
> `transfer` ranks single swaps by **raw player xP gain**, so it happily "upgrades" a cheap bench (a big
> paper gain that doesn't change the team you field). Rank instead by the improvement to your **starting
> XI**.

---

### 🔎 Verified at planning (the standing lesson — value clear, performance solved)

- **Raw-gain ranking is misleading.** On a `--weekly` squad (£3 bank), today's `transfer` tops with
  *Kusi-Asare → João Pedro **+19.3 xP*** — but Kusi-Asare is bench fodder, so the fielded XI barely
  moves. **XI-aware** ranks the *real* improvement: *Guéhi → Gabriel **+3.0 XI xP***. The right metric is
  **XI-gain** = `best-XI-xP(after) − best-XI-xP(before)`.
- **A fast best-XI makes it cheap.** Enumerating the ~7 legal formations and taking top-N per position
  **matches `best_legal_xi` exactly** (235.3 = 235.3) and ranks all ~750 candidate swaps in **0.02s** —
  no per-candidate ILP.
- **It pairs with `--weekly`** (ADR-045): XI-aware transfer maximises the XI, just as `--weekly` builds
  it — so a weekly squad has no XI-improving churn, and bench upgrades (XI-gain 0) drop out.
- Still preseason (0 GWs); ClubElo up (intermittent).

---

### 🧭 What's new — transfers that help the team you play

`transfer` becomes about the **fielded XI**: a swap's value is how much it lifts your best legal XI, not
a headline number dominated by bench fodder. Bench-only swaps (XI-gain 0) stop crowding the shortlist,
and the plan/`ask` speak the same weekly-relevant number — the natural completion of the bench-aware
work.

---

### 🎯 Sprint Goal

**Objective:** `suggest_transfers` (and the plan + `ask`) rank swaps by **XI-gain** — the change in the
best legal XI's xP — via a fast `best_xi_points` helper; bench-only swaps drop out. A gate settles
whether XI-aware is the transfer **default** or a mode.

#### Success Criteria
- [ ] Approach agreed (**ADR-046**) — the XI-gain metric; the fast `best_xi_points` (matches
      `best_legal_xi`); **default vs mode** (the key call); the displayed number; shortlist + plan + `ask`
- [ ] `best_xi_points(players, scores)` — the best legal XI's xP by formation enumeration; matches the ILP
- [ ] XI-aware `suggest_transfers` — rank by XI-gain; a bench-only swap (XI-gain 0) isn't suggested; fast
- [ ] The plan (`suggest_transfer_plan`) and `ask "what transfer…"` use the same metric
- [ ] The shown gain is the **XI gain** (weekly-relevant); combinable with `--bank`/`--count`
- [ ] Tests (XI-gain ranks XI upgrades over bench swaps; matches the ILP; a plan; the mode/default) + smoke
- [ ] Docs: ADR-046 + index, Architecture, Handbook/README, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-136 | **Gate.** XI-aware design (**ADR-046**): the XI-gain metric; the fast `best_xi_points` (proven to match `best_legal_xi`); **default vs mode**; the displayed number; how it flows to the plan + `ask`. Pressure-test (done: value + speed) | Critical | ✅ Done | 0.5–1 session |
| US-137 | **Fast best-XI + XI-aware `suggest_transfers`** — `best_xi_points(players, scores)`; rank swaps by XI-gain (best-XI after − before); bench-only swaps drop out; keep the legality/budget/club rules + dedup. Tests | High | ✅ Done | 1 session |
| US-138 | **Plan + `ask` + CLI/docs** — `suggest_transfer_plan` threads XI-gain; the `ask "transfer"` intent + the CLI use it; the shown number is XI gain; the default/mode from the gate. Tests + smoke + docs | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-046 recorded + added to the ADR index — _US-136_
- [x] Update Architecture changelog (XI-aware transfers) — _US-137_
- [x] Update Handbook/README (transfers rank by XI improvement) — _US-138_
- [x] Update PROJECT_STATUS — _US-138_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — `best_xi_points` matches the ILP; XI-gain ranks an XI upgrade above a
   bench-only swap; a bench-only swap (XI-gain 0) isn't suggested; the plan; existing **392** stay green;
   no new dependency.
2. **Manual smoke test done** — on a `--weekly` squad, `transfer` no longer tops with a bench-fodder
   swap; it surfaces real XI upgrades; the plan + `ask "what transfer for <squad>?"` agree; combinable
   with `--bank`/`--count`.
3. **Documentation updated & checked** — ADR-046 + index, Architecture, Handbook/README, sprint board +
   PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| XI-gain ranking in `suggest_transfers` + the plan + `ask` | A bench-aware *plan* over multiple weeks — later |
| A fast `best_xi_points` (formation enumeration) | Re-deriving the saved squad's declared bench (uses the XI directly) |
| The default-vs-mode decision (gate) | Chip-timing / hit (−4) modelling — later |

**External Dependencies:** None.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Changing `transfer`'s default surprises users | Med | Gate decides default vs mode; if default, a clear "ranked by XI improvement" note; the raw view stays available |
| `best_xi_points` disagrees with `best_legal_xi` | Med | Pinned to match on real data; a test asserts equality across squads |
| XI-gain hides a good bench-cover swap | Low | Bench cover has little weekly value (the point); a later bench-weighted transfer could nuance it |
| Performance (per-candidate XI) | Low | The fast best-XI is ~O(1) per candidate; measured 0.02s for ~750 swaps |

---

### 🗝️ Gating decision (US-136 → ADR-046)

Settle before code — the metric + speed are probed. Proposed (confirm/redirect at "start US-136"):

1. **The metric.** A swap's value = **XI-gain** = `best_xi_points(owned − out + in) −
   best_xi_points(owned)` (on the unified xP). `suggest_transfers` ranks positive-XI-gain swaps; the
   plan threads it; the shown "gain" is the XI gain.
2. **The helper.** `best_xi_points(players, scores)` — the best legal XI's xP via formation enumeration
   (matches `best_legal_xi`; fast, no ILP).
3. **Default vs mode** — *the key call.* XI-aware is more useful (raw gain is misleading), and it pairs
   with `--weekly`; but the raw ranking pairs with the max-15 default (ADR-041 consistency). *Propose:
   XI-aware as the default (with a note), keeping the raw ranking behind a flag — confirm/redirect at the
   gate (parallel to the squad default question).*
4. **Surfaces.** Shortlist + plan + `ask "what transfer…"`, all on XI-gain; keep dedup + `(b)` markers.

**Worked example (already run):** flat tops *Kusi-Asare → João Pedro +19.3* (bench fodder); XI-aware tops
*Guéhi → Gabriel +3.0 XI xP*; the fast best-XI matches the ILP (235.3) in 0.02s.

---

### 📝 Session Progress Log

- **US-136 (gate) ✅** — Recorded **ADR-046**, metric + speed + value all proven on the live DB, and the
  one decision settled by the owner: **XI-aware is the transfer default** (`--raw` for the old
  raw-player-gain ranking). Settled: a swap's value = **XI-gain** = `best_xi_points(owned − out + in) −
  best_xi_points(owned)`; a fast **`best_xi_points`** (formation enumeration — **matches `best_legal_xi`**,
  235.3 = 235.3, ~0.02s for ~750 swaps); rank positive-XI-gain swaps (bench-only swaps, XI-gain 0, drop
  out); the shown "gain" is the XI gain; the shortlist + plan + `ask` all use it; legality/dedup/`(b)`
  unchanged. Worked example: raw tops with the misleading *Kusi-Asare → João Pedro +19.3* (bench fodder);
  XI-aware tops with *Guéhi → Gabriel +3.0 XI xP*. ADR-046 indexed.
- **US-137 ✅** — **`best_xi_points(players, scores)`** added to `optimizer.py` (enumerate the ~7 legal
  formations `_XI_FORMATIONS`, sum top-N per position) + exported; **`suggest_transfers` gained
  `xi_aware=True`** ranking by XI-gain (`best_xi_points(owned − out + in) − base_xi`), raw path behind
  `xi_aware=False`; **`suggest_transfer_plan` threads `xi_aware`** through its greedy state.
  - **Tests (20 in `test_transfer.py`; 394 total, was 392):** `best_xi_points` matches `best_legal_xi`
    (62.0 on a constructed 15); XI-gain ranks an XI upgrade (FWD@10) above a bench-only swap (DEF@2, XI-gain
    0 → drops out) and `--raw` still surfaces the bench swap; the 9 rule-tests (legality/budget/club/dedup/
    bench-flag/limit/plan) pinned to the raw path (`xi_aware=False`) since they encode raw-gain values.
  - **Smoke (live DB):** on the **TS** squad, raw's #2 *Slater → Hughes +7.2* (bench-only) **drops out** of
    XI-aware, which surfaces *Senesi → Mukiele +4.1* instead; on a **`--weekly`** build (£3 bank) the ADR
    example reproduces exactly — raw tops *Kusi-Asare → João Pedro +19.3* (true XI gain +0.8), XI-aware tops
    *Guéhi → Gabriel +3.0*; `best_xi_points` matches `best_legal_xi` (208.9 TS, 235.3 RoboTS) in ~0.02s.
  - **Docs:** Architecture §12 changelog (Sprint 046). _CLI `--raw` + `ask` + README/PROJECT_STATUS are
    US-138._
- **US-138 ✅** — Wired XI-gain across every surface. **CLI:** `transfer` gained **`--raw`**
  (`xi_aware = not args.raw`), threaded to `suggest_transfers`/`suggest_transfer_plan` and both
  renderers. **Renderer (`ui/transfer.py`):** the gain column self-labels **ΔXI** (default) vs **ΔxP**
  (`--raw`), the header reads "by XI improvement" / "by raw xP gain", and a note explains the metric +
  points to `--raw`. **`ask`:** already XI-aware (inherits the default); reworded the facts/headline to
  **"starting_XI_improvement"** / "+N XI xP" so the narration speaks the right number.
  - **Tests (396 total, +2):** `--raw` parses (default off); the renderer labels ΔXI/"XI improvement"
    vs ΔxP/"raw xP gain"; updated the two `ask` fact-key assertions to the XI-improvement wording.
  - **Smoke (live DB):** `transfer --squad TS` tops *Ampadu → Zubimendi +9.3* then *Senesi → Mukiele
    +4.1* (the bench-only *Slater (b) → Hughes +7.2* only appears under `--raw`); `--count 2` plan and
    `ask "what transfer for TS?"` both agree (Ampadu → Zubimendi +9.3 XI xP); the grounding verifier
    flagged the LLM's invented figures (as designed).
  - **Docs:** README (feature + examples), Handbook §21 (a "rank by the right number" lesson),
    PROJECT_STATUS (commands + Tests 396 / ADRs 46 + the XI-aware line).

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — both stories delivered under the gate (US-136 / ADR-046). `transfer` now
ranks by **XI improvement** (best-XI gain via a fast, exact `best_xi_points`), so bench-fodder upgrades
drop out; `--raw` preserves the old ranking; the plan + `ask` speak the same number. **396 tests** (was
392, +4), **46 ADRs**, ruff clean, no new dependency.

**Delivered**
- **US-136 (gate)** — ADR-046: the XI-gain metric; the fast `best_xi_points` (proven to match
  `best_legal_xi`); owner's call — **XI-aware is the default**, `--raw` for the old ranking.
- **US-137** — `best_xi_points(players, scores)` (formation enumeration; matches the ILP, ~0.02s/750
  swaps); `suggest_transfers(xi_aware=True)` ranks by XI-gain; `suggest_transfer_plan` threads it.
- **US-138** — `--raw` CLI flag; renderers self-label ΔXI vs ΔxP + a metric note; `ask` reworded to
  "starting-XI improvement"; README + Handbook §21 + Architecture + PROJECT_STATUS.

**What went well**
- The gate probe pinned the metric, the speed *and* the value on real data before any code — the build
  was mechanical, and the worked example (*Kusi-Asare → João Pedro +19.3* vs *Guéhi → Gabriel +3.0*)
  was the acceptance test.
- A fast exact helper (formation enumeration) sidestepped the per-candidate ILP entirely — pinned to
  match `best_legal_xi` by a test.
- The default-vs-`--raw` split kept the change honest: the smoke showed the exact contrast (the
  bench-only *Slater → Hughes +7.2* only appears under `--raw`).

**Challenges / how they were handled**
- **The existing transfer tests broke** under the new default — they use tiny squads (no GK →
  best-XI 0). Recognised they test *metric-agnostic rules*, so pinned them to `xi_aware=False` and
  added dedicated XI-aware tests on a full 15. (The lesson: when the default metric changes, separate
  the rule-tests from the metric-tests.)
- **Grounding wording** — the fact keys said "expected points gain"; reworded to
  "starting_XI_improvement" so the narration can't imply a raw-xP delta.

**Carried forward:** None.
