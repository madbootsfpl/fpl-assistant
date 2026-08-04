# Sprint 039: Trust the numbers — sane xP + consistent recommendations

**Dates:** 2026-08-04
**Status:** ✅ Complete (3/3 stories, retro done)
**Capacity:** ~2–3 working sessions (a gate + a model fix + a bug fix + clarity)
**Carried Over:** None (Sprint 038 closed clean)

> **Direction (owner's Sprint-38 notes):** *"I want to challenge some of the data output/results."*
> Three concrete examples on squad **RoboTS**: (1) `transfer` offers cheap players with far higher xP
> than the squad has (Benitez £4.5 → **35.0 xP**) — *"why wouldn't that be in the original result?"*;
> (2) `transfer` lists the **same incoming player twice** (Benitez); (3) start/bench differs from the
> "original" lineup — *"I thought the original would be optimised."*

---

### 🔎 Verified at planning (the standing lesson — root causes found before code)

- **Implausible xP = an un-gated ppg fallback on a tiny sample.** Benitez's 35.0 xP comes from a
  **single game** (90 mins, 7 pts → `points_per_game` 7.0). The ≥900-min gate (ADR-028) protects the
  *baseline* rate, but when there's **no qualifying baseline** the code falls back to raw `ppg` **with
  no sample gate** — so one cameo projects like a 7-pts/GW superstar. *(xMins already masks this in the
  **default** view — Benitez's weight is 0.026 → weighted xP 0.9, so default `transfer` is sane:
  Watkins/Roefs/Mukiele. But the **raw** rate is genuinely wrong, and `--no-xmins` exposes it — masking
  a bad number with a second model is fragile; fix the number.)*
- **Duplicate incoming = no cross-dedup.** `suggest_transfers` picks `best = max(candidates by xp)`
  **independently per out-player**, so two GKs (Kelleher, Raya) both resolve to the same target
  (Benitez). Nothing stops the same incoming player appearing in multiple rows.
- **start/bench "inconsistency" = a flag mismatch, not a bug.** Default `analyse --squad RoboTS` and
  `ask "start/bench"` produce the **same XI** (both xMins-weighted `select_squad` — confirmed). The
  owner's comparison was `analyse --no-xmins` (raw) vs start/bench (xMins) — apples to oranges. This is
  a **transparency** gap, not a logic error.
- Still preseason (0 GWs); ClubElo up (intermittent). All three are preseason-reproducible.

---

### 🧭 What's new — the recommendations become trustworthy

The system already *feels* good, but the owner rightly caught numbers that don't survive scrutiny. This
sprint makes the **raw xP** honest (no cameo can project like a star), removes a genuine **transfer
bug** (no repeated incoming), and makes the tools' **consistency** legible (why a raw and an
xMins-weighted view differ). It's a data-quality sprint — exactly the "verify on real data" ethos,
turned on our own output.

---

### 🎯 Sprint Goal

**Objective:** (1) Dampen the low-evidence xP rate so a tiny-sample player no longer projects like a
star (the raw number is sane, not just masked by xMins); (2) dedupe the incoming player in `transfer`
suggestions; (3) make the raw-vs-xMins consistency legible (confirm default `analyse`/start-bench agree;
explain the difference where a flag changes it).

#### Success Criteria
- [ ] Approach agreed (**ADR-040**) before code — how to damp a no-baseline rate by evidence; the
      dedup rule; the consistency/clarity approach. Pressure-tested on Benitez et al.
- [ ] **Sane xP** — a player with no ≥900-min baseline and tiny minutes projects a plausible rate
      (Benitez's raw xP drops from 35 to a believable figure); genuine players are ~unchanged
- [ ] **No duplicate incoming** — `suggest_transfers` never lists the same buy twice; each out-player
      gets its best *still-available* target
- [ ] **Consistency legible** — default `analyse` and start/bench give the same XI (confirmed + tested);
      a note explains that `--no-xmins` is the raw "assumes 90" view
- [ ] Tests (the damping on a cameo; genuine players unchanged; dedup; analyse≡start-bench) + live smoke
- [ ] Docs: ADR-040 + index, Architecture, Handbook/README, PROJECT_STATUS

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-115 | **Gate.** Diagnose (done) + decide the fixes (**ADR-040**): (a) **low-evidence xP damping** — when there's no qualifying baseline, shrink `ppg` toward a conservative prior by minutes-evidence (vs a hard gate or a positional cap); (b) the **transfer dedup** rule; (c) the **consistency/clarity** approach. Pressure-test the damping on Benitez/Okafor/genuine players | Critical | ✅ Done | 0.5–1 session |
| US-116 | **Sane low-evidence xP** — implement the agreed damping in `baseline_rate`/`player_xp` (the no-baseline path); a cameo no longer projects like a star; genuine players ~unchanged. Unit-tested | High | ✅ Done | 1 session |
| US-117 | **Transfer dedup + consistency clarity** — `suggest_transfers` never repeats an incoming player (best still-available per out); confirm + test that default `analyse` ≡ start/bench XI; a clarity note on raw vs xMins. Tests + smoke | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-040 recorded + added to the ADR index — _US-115_
- [ ] Update Architecture changelog (low-evidence damping; transfer dedup) — _US-116/117_
- [ ] Update Handbook/README if behaviour/notes change — _US-117_
- [ ] Update PROJECT_STATUS — _US-117_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — cameo damping + genuine-player-unchanged; transfer dedup; analyse ≡
   start-bench XI; existing **357** stay green; no new dependency.
2. **Manual smoke test done** — `transfer --squad RoboTS --no-xmins` shows a sane Benitez xP and **no
   repeated incoming**; default `analyse` and `ask "start/bench"` agree on the XI.
3. **Documentation updated & checked** — ADR-040 + index, Architecture, Handbook/README, sprint board +
   PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Damping the **no-baseline** (fallback) rate | Re-tuning the ≥900-min baseline itself (partial-season rates like Okafor — a GW1 concern) |
| Dedup of the transfer **incoming** player | A full multi-move planner rewrite |
| Confirming + explaining raw-vs-xMins consistency | Changing xMins itself (ADR-038 stands) |
| Unit + smoke coverage of the above | The full probabilistic xMins (Phase 5) |

**External Dependencies:** None beyond stored FPL data.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Over-damping genuine new signings | Med | Shrink toward a *replacement-level prior*, not to zero; pressure-test on real players; genuine ≥900-min players are untouched |
| The cap/damping is arbitrary | Med | Pin the prior/threshold on real data at the gate; keep it transparent + documented (ADR-040) |
| Dedup changes existing suggestions subtly | Low | Each out-player still gets its best *available* target; only repeats are removed; tests lock the shape |
| "Consistency" turns into a big refactor | Low | It's confirm + a note — the defaults already agree; no behaviour change |

---

### 🗝️ Gating decision (US-115 → ADR-040)

Settle before code — the diagnosis is done. Proposed (confirm/redirect at "start US-115"):

1. **Low-evidence xP damping.** When a player has **no qualifying baseline** (no season ≥900 min in the
   look-back), don't project raw `ppg`. Shrink by minutes-evidence toward a conservative prior:
   `rate = ppg × c + prior × (1 − c)`, where `c = min(1, best_season_minutes / 900)` and `prior` is a
   low replacement-level rate (pinned on real data — global or per-position). Benitez (90 min → c≈0.1)
   collapses from 7.0 toward the prior → a believable xP; a genuine ≥900-min player is **untouched**
   (they have a baseline). *Alternatives to weigh at the gate: a hard min-minutes gate (cliff) or a
   positional plausibility cap (crude).*
2. **Transfer dedup.** Build the shortlist so an incoming player appears **once** — greedily assign each
   out-player its best *not-yet-suggested* target (or dedupe by incoming id, keeping the higher gain).
3. **Consistency/clarity.** No behaviour change — the defaults already agree. Add a test that default
   `analyse` XI ≡ start/bench XI, and a one-line note that `--no-xmins` is the raw "assumes 90" view.

**Worked example (to run at the gate):** Benitez raw xP 35 → a sane figure after damping; Okafor/genuine
players ≈ unchanged; `transfer --squad RoboTS --no-xmins` yields no repeated incoming.

---

### 📝 Session Progress Log

- **US-115 (gate) ✅** — Recorded **ADR-040**, design **pressure-tested on the live DB**:
  - **Prior pinned on data:** 900-min regulars' pp90 runs p10=2.88 / median=3.92, so `PRIOR = 2.0`
    sits deliberately below the 10th percentile (sub-900-min players are weaker than regulars).
  - **Shrinkage validated:** `fallback_rate = career_pp90 × c + PRIOR × (1−c)`, `c = min(1,
    career_min/900)` → Benitez (90 min) 7.0 → **2.5** (xP 35 → ~12.5); Okafor/Wilson/Haaland
    **untouched** (they have baselines); 124 players use the fallback, the trusted 352 unchanged.
  - **Dedup root cause** confirmed (`suggest_transfers` picks best-incoming per out-player, no
    cross-dedup → Benitez twice); **consistency** confirmed a flag mismatch (default `analyse` ≡
    start/bench XI), not a bug.
  Settled: shrink the no-baseline fallback toward a replacement prior (global, tunable; wired via
  `fallback_by_code` used only when baseline is None → byte-identical when absent); transfer lists each
  incoming **once**; a test + note make raw-vs-xMins legible. ADR-040 added to the index.
- **US-116 (sane low-evidence xP) ✅** — Added `fallback_rate(history, prior=2.0)` in `xp.py`; `player_xp`
  gained an optional `history_by_code` and a three-tier rate: trusted **≥900 baseline** (`hist`) → the
  **shrunk fallback** (`fallback`) → current **ppg** (`current`). Wired `history_by_code` through the 3
  CLI commands, `captain_picks`, and the 3 `ask` decision paths; **byte-identical without it** (existing
  357 green). The honest new `rate_source="fallback"` gets **no `*` star** (the star still means a real
  baseline). **Mid-flight correction (broader smoke, the "probe broadly" lesson):** live `transfer`
  surfaced **Enes Ünal at 46.9 xP** — three cameo seasons (317/330/214 min at ~10 pp90) whose *career-sum*
  `c` compounded to false confidence. Fixed by taking **`c` from the biggest single season**, not the
  sum → Enes Ünal 46.9 → ~27 (rate 5.06), Benitez still 12.5; ADR-040 + the test updated. **+6 tests**
  (shrink a cameo; biggest-season-not-sum; ample minutes; no-history; the two `player_xp` tiers) →
  suite **357 → 363**; ruff clean; no new dependency. **Smoke:** `transfer --squad RoboTS --no-xmins`
  now shows plausible targets (Okafor/Wilson/De Cuyper), no cameo topping the list.
- **US-117 (transfer dedup + consistency) ✅** — Rewrote `suggest_transfers` to pick **disjoint** moves:
  build every positive-gain (out → in) pair, sort by gain, greedily take with each **buy and each sell
  used once** (a sell whose best target is taken gets its next-best). The duplicate-Benitez bug is gone;
  smoke shows 5 distinct incoming. For **consistency**, extracted `best_legal_xi(owned, scores)` — the
  one primitive `analyse` (no bench), its `ask` twin, and start/bench now all call, so they *can't*
  diverge (was triplicated); confirmed live `analyse` XI ≡ start/bench XI (True). **+3 tests** (no
  repeated incoming; `best_legal_xi` == `select_squad` on the same scores + shape; existing 16 transfer
  tests unchanged) → suite **363 → 365**; ruff clean; no new dependency. Broad smoke: captain / analyse /
  start-bench / compare / transfer all sane end-to-end.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories, from the owner's challenge of three RoboTS outputs. **US-115** —
  ADR-040 (diagnosis + the shrinkage/dedup/consistency decisions, pressure-tested). **US-116** —
  `fallback_rate` shrinks a no-baseline player's rate toward a replacement prior by their biggest
  season's confidence; `player_xp` gained a three-tier rate (`hist`/`fallback`/`current`).
  **US-117** — `suggest_transfers` picks disjoint moves (no repeated buy/sell); `best_legal_xi`
  extracted so `analyse` and start/bench can't diverge. Tests 357 → **365**; one ADR; **no new
  dependency**.
* **Carried Forward:** None. (Optimistic ≥900-min partial-season baselines — Okafor/Cherki — are a
  separate GW1 tuning question, deliberately scoped out.)
* **Key Artifacts / Decisions:** ADR-040; `fallback_rate` + the `history_by_code` tier on `player_xp`;
  the disjoint `suggest_transfers`; `best_legal_xi` (the shared XI primitive).

#### Retrospective
* **What Went Well?**
  - **The owner's challenge was exactly right.** All three "that looks wrong" outputs traced to real
    causes (an un-gated ppg fallback, a per-out dedup gap, a flag mismatch). Trusting a sharp-eyed
    "why is this number like that?" beat any amount of self-review.
  - **Diagnosis before code.** The gate found the root cause of each, so the fixes were targeted, not
    guessed — and the prior was *pinned on real data* (below the p10 of regulars), not invented.
  - **Consistency made structural.** Extracting `best_legal_xi` means `analyse` and start/bench can't
    drift — better than a test that merely checks they currently agree.
* **What Could Be Improved?**
  - **The gate probe was too narrow — again.** It validated the fix on Benitez (one 90-min season) but
    missed **Enes Ünal** (three cameo seasons compounding to false confidence), caught only by the
    live smoke. The recurring "probe broadly" lesson: a single example hides the multi-example bug.
    Fixed by taking confidence from the biggest single season, not the career sum.
  - **xMins was masking, not fixing.** The default view looked fine because xMins dampened Benitez;
    the raw number was still wrong. A second model hiding a bad number is a latent trap — fix the number.
* **Lessons Learned?**
  - Probe *broadly* at the gate (many players, many shapes), not one convincing example.
  - Don't let a downstream model excuse an upstream error — make the raw number honest.
  - Turn "they happen to agree" into "they call the same function" — consistency you can't break.
  - A good user challenge is a gift: implausible output is a lead, not noise.
* **Action Items for Next:**
  - [ ] (Backlog, GW1) revisit optimistic ≥900-min partial-season baselines; consider positional priors.
  - [ ] Keep the gate probe broad; keep the 3-part DoD (the smoke caught Enes Ünal).

---

**Proposed follow-on:** owner to steer — more Phase 4, the web UI (Phase 2), or wait for GW1 to do Data
Hardening + the full Phase-5 xMins (which also feeds the partial-season baseline tuning).

**Completion Date:** 2026-08-04
**Final Notes:** Three owner-flagged outputs, three root-cause fixes — the numbers are honest now in the
raw view too, not just masked by xMins; a real bug (duplicate incoming) is gone; and consistency is
structural. The process caught a fourth implausible player the gate missed. Sprint outcome:
**Successful** — 3/3 stories, zero roll-over, DoD held (39th).
