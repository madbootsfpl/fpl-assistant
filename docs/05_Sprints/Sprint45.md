# Sprint 045: Bench-aware squad optimisation — weekly XI vs Bench Boost

**Dates:** 2026-08-05
**Status:** ✅ Complete (3/3 stories, retro done)
**Capacity:** ~2–3 working sessions (a gate + a bench-aware ILP + CLI/ask modes)
**Carried Over:** None (Sprint 044 closed clean)

> **Direction (owner):** a bench-aware optimiser — *"valuable for both rotation and Bench Boost."* Today
> `squad --full` maximises the 15-total (Bench-Boost-optimal), which over-invests in a bench that won't
> score on a normal week. A **weekly** mode should maximise the **starting XI** with a cheap-but-playing
> bench (rotation cover); a **Bench Boost** mode keeps the max-15.

---

### 🔎 Verified at planning (the standing lesson — the value is big, the default settled)

- **Bench-aware lifts the XI meaningfully.** A prototype bench-aware ILP (a `start` variable per player,
  an XI formation, and a weighted objective `Σ xp·start + w·xp·(pick−start)`) on the £100m pool:
  - `w = 1.0` (max-15 = today / Bench Boost): best XI **233.6**, bench 72.2 (£27.5m bench);
  - `w = 0.0` (pure XI): XI **243.1**, bench 0.6 (a dead £17m bench);
  - **`w = 0.1` (the sweet spot):** XI **241.2** (only −1.9 vs pure), bench **39.7** — a *playing* bench
    for +£1.5. **+7.6 XI xP** over today's best XI, with real rotation cover.
- **The ILP designates the XI natively** (the `start` vars) — better than Sprint-44's post-hoc split, and
  it marks the recommended bench.
- **Owner's call — modes, not a new default.** The default `squad --full` stays max-15 (Bench-Boost-
  optimal *and* transfer-consistent — no "free transfers", ADR-041). **`--weekly`** = bench-aware
  (`w = 0.1`); **`--bench-boost`** = the explicit max-15. Avoids a surprise + a consistency regression.
- Still preseason (0 GWs); ClubElo up (intermittent).

---

### 🧭 What's new — build the team you'll actually field

The optimiser can now maximise the *right* thing for the week: **`--weekly`** pours budget into the
starting XI and fills the bench with cheap-but-playing cover (a stronger XI + rotation insurance);
**`--bench-boost`** keeps the max-15 for the chip week (all 15 score). The build *designates* its XI, so
the XI/bench xP breakout (Sprint 044) is exact, and the recommended bench is saveable.

---

### 🎯 Sprint Goal

**Objective:** `select_squad` gains a **bench-aware** mode (a `bench_weight`: `start` vars + XI
formation + the weighted objective), surfaced as `squad --full --weekly` (w = 0.1) and `--bench-boost`
(w = 1.0 = max-15); the default is unchanged; `ask "build me a squad for a bench boost / for rotation"`
picks the mode. The build designates + can save its bench.

#### Success Criteria
- [ ] Approach agreed (**ADR-045**) — the bench-aware ILP; `w = 0.1` weekly default (pinned); the
      `--weekly`/`--bench-boost` modes; default max-15 unchanged (transfer-consistent); the save/display
      behaviour; the `ask` keywords
- [ ] `select_squad(..., bench_weight=W)` maximises `Σ xp·start + W·xp·(pick−start)` with a legal XI +
      full 15; **byte-identical when `bench_weight` is None** (existing 386 stay green)
- [ ] `squad --full --weekly` → a stronger XI (~241 vs 233.6) + a playing bench; `--bench-boost` → max-15
- [ ] The build **designates** the XI (bench flags), so the XI/bench breakout is exact; `--weekly --save`
      records the designated bench
- [ ] `ask "build me a squad … for a bench boost"` / `"… for rotation"` selects the mode
- [ ] Combinable with `--cheap`/`--premium`/`--differential`; infeasible → a clear message
- [ ] Tests (bench-aware XI > default XI; playing bench; default byte-identical; the modes) + live smoke
- [ ] Docs: ADR-045 + index, Architecture, Handbook/README, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-133 | **Gate.** The bench-aware design (**ADR-045**): the `start`-variable ILP + the weighted objective; `w = 0.1` weekly default (pinned); the `--weekly`/`--bench-boost` modes (default max-15 unchanged, transfer-consistent); designate + save the bench; the `ask` keywords. Pressure-test (done) | Critical | ✅ Done | 0.5–1 session |
| US-134 | **Bench-aware optimiser + CLI** — `select_squad(bench_weight=W)`: `start` vars, XI formation (`XI_FLEX`), the weighted objective, bench flags on non-starters; byte-identical when absent. `squad --full --weekly` / `--bench-boost`. Tests | High | ✅ Done | 1–1.5 sessions |
| US-135 | **`ask` modes + display** — parse "bench boost" / "rotation/weekly" in `build_squad` → the mode; the designated bench drives the XI/bench breakout; combinable with archetypes. Tests + smoke + docs | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-045 recorded + added to the ADR index — _US-133_
- [ ] Update Architecture changelog (bench-aware optimisation) — _US-134_
- [ ] Update Handbook/README (`--weekly`/`--bench-boost`; the `ask` modes) — _US-135_
- [ ] Update PROJECT_STATUS — _US-135_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — bench-aware XI beats the default XI; the bench is playing (not dead);
   default `bench_weight=None` byte-identical; the modes parse; existing **386** stay green; no new
   dependency.
2. **Manual smoke test done** — `squad --full --weekly` shows a stronger XI (~241) + a playing bench;
   `--bench-boost` = max-15; `ask "build me a squad for a bench boost"` boosts; `--weekly --save`
   records the bench; default `squad --full` unchanged; `transfer` on the default squad still finds 0.
3. **Documentation updated & checked** — ADR-045 + index, Architecture, Handbook/README, sprint board +
   PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| A bench-aware `select_squad` (`start` vars + weighted objective) | Making `transfer` XI-aware (a later sprint; keeps the default consistent) |
| `--weekly` / `--bench-boost` modes + `ask` keywords | Changing the default `squad --full` (owner: keep max-15) |
| Designate + save the recommended bench | Chip *timing* advice (when to Bench Boost) — later |
| Reuse `decision_xp`, the archetype constraints, `render_squad` | A `--bench-weight X` power-user knob (optional; gate to decide) |

**External Dependencies:** None.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| The `start`-variable ILP is a bigger change | Med | Guard behind `bench_weight` (None → today's model, byte-identical); a test locks the no-weight path |
| `--weekly` bench is cheap fodder → `transfer` "upgrades" it | Med | Default (max-15) is unchanged, so the consistency property holds; `--weekly` is opt-in; transfer flags bench swaps `(b)` |
| Solve time (2× the binaries) | Low | Still a small ILP (≤ ~1k vars); CBC handles it fast; measure in the smoke |
| Interaction with declared `--bench`/include/exclude | Low | A declared bench pins the split (skip bench-aware); include/exclude still force `pick`; a test |

---

### 🗝️ Gating decision (US-133 → ADR-045)

Settle before code — the ILP + weight are probed. Proposed (confirm/redirect at "start US-133"):

1. **The model.** `select_squad(..., bench_weight=W)` adds a `start[i]` binary (`start ≤ pick`,
   `Σ start = 11`, XI within `XI_FLEX` ranges) and maximises `Σ xp·start + W·xp·(pick − start)`; the 15
   still meet the full shape / budget / club cap / archetypes. Non-starters get `bench = True`.
   **`bench_weight = None` → today's model** (no `start` vars), byte-identical.
2. **Modes.** `--weekly` → `W = 0.1` (pinned: strong XI + a playing bench); `--bench-boost` → `W = 1.0`
   (max-15). The **default is unchanged** (max-15, transfer-consistent — owner's call). *(Optional
   `--bench-weight X` for tuning — confirm at the gate.)*
3. **Save/display.** The designated bench drives the XI/bench breakout (exact, not post-hoc) and is saved
   by `--weekly --save`. The default build keeps Sprint-44's post-hoc auto-XI display + empty saved bench.
4. **`ask`.** `build_squad` parses "bench boost" → boost and "rotation"/"weekly" → weekly; else the
   default. Grounded + optional.

**Worked example (already run):** `w = 1.0` → XI 233.6 / bench 72.2; `w = 0.1` → XI 241.2 / bench 39.7
(£18.5m, a playing bench); `w = 0.0` → XI 243.1 / bench 0.6 (dead bench).

---

### 📝 Session Progress Log

- **US-133 (gate) ✅** — Recorded **ADR-045**, the model + weight + composition all proven on the live
  pool: a `start[i]` binary per player, an XI formation (`XI_FLEX`), objective `Σ xp·start + W·xp·(pick −
  start)`. **`W = 0.1` weekly** → XI **241.2** / bench **39.7** (£18.5m playing bench) — **+7.6 XI xP**
  over the max-15's best XI, *with* rotation cover; `W = 1.0` = Bench Boost (max-15); `W = 0` = a dead
  bench. **Composes with archetypes** — `--weekly --premium 1 --differential 2` stays Optimal (~0.07s);
  over-asks go Infeasible. Settled: `select_squad(bench_weight=W)` (None → today's model, byte-identical);
  `--weekly` (0.1) / `--bench-boost` (1.0), **default max-15 unchanged** (owner's call — transfer stays
  consistent); the build designates + saves the bench; `ask` parses "bench boost" / "rotation". Both
  flags imply `--full` + use xP scores. ADR-045 indexed.
- **US-134 (bench-aware optimiser + CLI) ✅** — `select_squad(bench_weight=W)`: when set, adds a
  `start[i]` binary per player (`start ≤ pick`, `Σstart=11`, XI within `XI_FLEX`) and maximises
  `Σ score·start + W·score·(pick−start)`, flagging non-starters `bench`; **None → today's model,
  byte-identical** (a test locks it). **`--weekly`** → `WEEKLY_BENCH_WEIGHT` (0.1). **Refinement during
  build:** `--bench-boost` at `W=1.0` designated an *arbitrary* XI (223.2, understating the fielded XI),
  so it's now just the **default max-15 build** (best-XI display via `best_legal_xi`) **+ an "all 15
  score" note** — correct for the chip; the `BENCH_BOOST_WEIGHT` constant was dropped. Modes imply
  `--full`, are mutually exclusive, and can't combine with `--bench`; `--weekly --save` records the
  designated bench. **+4 tests** → suite **386 → 390**; ruff clean; no new dependency. **Smoke:**
  `--weekly` → *Starting XI 4-5-1: 241.2 / Bench: 39.7*; `--bench-boost` → *best XI 233.6 / Bench 72.2 ·
  total 305.8 · "all 15 score"*; default unchanged.
- **US-135 (`ask` modes + display) ✅** — `_bench_mode(question)` parses "bench boost" → the max-15 and
  "rotation"/"weekly" → the bench-aware XI (`W = 0.1`); `_decide_build_squad` passes `bench_weight` and,
  for a bench-aware build, uses the **designated** bench for the XI/bench breakout (else `best_legal_xi`).
  **Routing fix (found in smoke):** "build me a squad for a bench boost" was caught by `start_bench`'s
  "bench" keyword → moved **`build_squad` before `start_bench`** (start/bench questions never contain
  "build"/"best squad"). **+2 tests** (the mode parser; the bench-boost build routes to build_squad) →
  suite **390 → 392**; ruff clean; no new dependency. **Smoke:** `ask "… for rotation"` → XI 241.2 /
  bench 39.7 (grounded ✓); `ask "… for a bench boost"` → XI 233.6, total 305.8, the "all 15 score" note;
  `who should I start from TS` still routes to start/bench. Docs: Architecture, README.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — bench-aware optimisation for the owner's two use cases. **US-133** —
  ADR-045 (the `start`-variable ILP, `w = 0.1` pinned, default kept). **US-134** — bench-aware
  `select_squad` + `--weekly`/`--bench-boost`. **US-135** — the `ask` modes + a routing fix. Tests 386 →
  **392**; one ADR; **no new dependency**.
* **Carried Forward:** None. (Making `transfer` XI-aware — so a weekly squad's cheap bench isn't
  "upgraded" — is the natural next item; chip *timing* advice too.)
* **Key Artifacts / Decisions:** `select_squad(bench_weight=W)` (the `start`-variable ILP);
  `WEEKLY_BENCH_WEIGHT`; `_bench_mode`; the `--bench-boost` = default-max-15 refinement; the
  build_squad-before-start_bench routing order.

#### Retrospective
* **What Went Well?**
  - **The probe carried the whole design** — the weight sweep pinned `0.1` (the XI/rotation knee), and
    the composition test proved it stacks on the archetypes before a line of production code.
  - **Opt-in kept the guardrail.** Keeping max-15 the default means `transfer` stays consistent (no free
    transfers) — the owner's call, and it avoided reopening a solved problem.
  - **Two smoke catches saved the feature.** The `--bench-boost` arbitrary-XI (223.2 vs 233.6) and the
    "bench boost" → start_bench mis-route both showed only when run for real — and both had clean fixes.
  - **The ILP *designs* the XI** — a stronger team than a post-hoc split, and the breakout is exact.
* **What Could Be Improved?**
  - **`transfer` isn't bench-aware** — on a `--weekly` squad it'd suggest upgrading the cheap bench.
    Deferred (the default is consistent); a future XI-aware transfer closes it.
  - **Routing is keyword-precedence** — the "bench boost" collision was a reminder that order matters as
    intents grow; an intent classifier is the eventual tidy.
* **Lessons Learned?**
  - Sweep a parameter to find the knee (0.1), don't guess it.
  - Opt-in changes preserve invariants; make the more-correct-but-riskier thing a mode, not the default.
  - Run it for real — the arbitrary-XI and the mis-route were invisible to the unit tests.
* **Action Items for Next:**
  - [ ] (Backlog) an XI-aware `transfer` (don't "upgrade" a weekly bench); chip-timing advice.
  - [ ] (Backlog) an intent classifier as keyword routing grows.
  - [ ] Keep sweeping parameters; keep the 3-part DoD.

---

**Proposed follow-on:** owner to steer — an XI-aware `transfer`, more Phase 4 (an intent classifier /
chat), the web UI (Phase 2), or wait for GW1 for Data Hardening + the full Phase-5 xMins.

**Completion Date:** 2026-08-05
**Final Notes:** The optimiser now builds the team you'll actually field — `--weekly` for a stronger XI +
rotation cover (+7.6 XI xP), `--bench-boost` for the chip — from the CLI and in plain English, with the
transfer-consistent default preserved. A parameter sweep pinned the weight; two real-run catches sharpened
it. Sprint outcome: **Successful** — 3/3 stories, zero roll-over, DoD held (45th).
