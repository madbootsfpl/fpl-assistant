# Architectural Decision Record: One xP metric — unify the optimiser with the decision layer (+ a squad-build `ask` intent)

**Decision ID:** ADR-041
**Date:** 2026-08-04
**Status:** Accepted
**Superseded By / Replaces:** Unifies the squad optimiser's `xp` objective (ADR-011) with the decision
layer's xP (ADR-028/038/040); makes `xp` the default `squad` objective. Extends `ask` (ADR-034/039).
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner built a squad for "max points", it looked optimal, yet `transfer` then offered moves that gain
points — *"why weren't those in the squad?"* A planning probe found the cause: **two different metrics
were in play.**

- **`squad --full` optimised `--objective points`** = last season's **total points** (`total_points`,
  backward-looking). `transfer`/`analyse`/`captain`/start-bench rank by **xP** — next-N-GW,
  fixture-adjusted, historical-baseline + low-evidence fallback, **xMins-weighted** (forward-looking).
  Different quantities → a squad best on last-year's points is not best on next-5-GW xP.
- **Even `squad --objective xp` disagreed:** `objective_scores("xp", …)` called `player_xp(players,
  upcoming)` with **defaults** — horizon **1**, no baseline/fallback, no xMins. A *degraded* xP.
- **The unified fix is proven** (worked example): a 15-man squad built on the **full** xP scores
  **305.8** and leaves `transfer` (same xP) with **0** positive moves; built on the degraded xP it
  scores **239.0** and `transfer` finds **5** (top +14.7). One metric → a better squad *and* consistency.

#### Decision Drivers
- **One currency** — the optimiser and the recommendations must speak the same xP, or they contradict.
- **Consistency by construction** — a single shared xP recipe, so they can't drift (cf. `best_legal_xi`).
- **Answer the question honestly** — explain points vs xP; make the default coherent.
- **Extend Phase 4** — expose the (now consistent) optimiser through grounded NL.

---

### ✅ Decision

**1. One shared xP recipe.** Extract `decision_xp(players, upcoming, history_by_code, *, source,
horizon, minutes_weighted=True)` → the ranked `player_xp` list, assembling the **full** xP the decision
layer uses: the historical baseline + the low-evidence fallback (ADR-040) and, unless `--no-xmins`,
xMins (ADR-038). This is the *one* place the "decision xP" is defined; `squad` (xp objective),
`analyse`, `transfer`, and the `ask` decisions all call it, replacing the duplicated
baseline/weight/`player_xp` assembly. The optimiser and the recommendations can no longer disagree.

**2. `xp` is the default `squad` objective** (owner's call). `squad --full` now optimises forward-looking
**xP** (xMins-weighted; `--no-xmins` for the raw view) — so it's consistent with `transfer` out of the
box (a squad on xP → `transfer` finds nothing). **`--objective points`** is kept for the season-total
view; `value`/`xgi` unchanged. *(xP needs upcoming fixtures — `refresh` provides them; with none, xP is
0 and the user is told to refresh.)*

**3. Explain points vs xP.** The squad output / handbook states plainly: `points` = last season's total
(proven, backward-looking); **`xp`** = expected points over the next N GW (fixtures + minutes) — the
metric the recommendations use. So the two are never silently conflated again.

**4. Phase 4 — a squad-build intent.** `ask "build me a squad [for £X]"`: parse the budget (default
£100m; a small tested parser like `_transfer_count`), optimise the 15 on the unified xP, render it
(reuse `render_squad`) as the structured detail, narrate + verify (`subjects` = the squad players).
Grounded and optional like every intent — `ask` can now *build*, not only analyse/transfer/captain.

---

### 🔀 Alternatives Considered

- **Keep `points` as the default.** Rejected by the owner — `points` (last-season total) is exactly the
  backward-looking metric that caused the confusion; `xp` is what the tool now speaks everywhere.
- **Leave the degraded `objective_scores("xp")`.** Rejected — it's the whole inconsistency; a degraded
  metric that looks like xP but isn't is worse than none.
- **Remove the `points` objective.** Rejected — season-total value is still a legitimate lens; keep it
  behind `--objective points`.
- **Let each command keep its own xP assembly.** Rejected — that's how they drifted; one `decision_xp`
  recipe is the structural guarantee (the ADR-040 `best_legal_xi` pattern).
- **Part B: a smarter router instead of the squad intent.** Deferred — the squad-build intent is the
  natural completion of the unified optimiser; the router tweak stays on the backlog.

---

### 🧭 Consequences

**Positive**
- `squad` and the recommendations agree: an xP-optimal squad has no free transfers. The owner's question
  is resolved *structurally*, not just explained.
- The squad is genuinely better on the forward-looking metric (305.8 vs 239.0 in the probe).
- One `decision_xp` recipe removes duplicated assembly across four call sites and prevents future drift.
- `ask` gains a build capability, grounded and verified.

**Negative / risks (mitigations)**
- **`squad --full` default output changes** (xp, not points) → documented; `--objective points` kept; a
  clear note explains the two.
- **xP needs fixtures** → `refresh` provides them; empty → xP 0 with a hint (as today for other views).
- **Drift could recur** → the shared recipe + a consistency test (squad-on-xp → 0 transfers) lock it.

---

### 📊 Validation

Prototyped on the live DB before code: squad on the unified full xP → total 305.8, `transfer` finds 0
positive moves; squad on the degraded xP → 239.0, `transfer` finds 5 (top +14.7). Acceptance for the
sprint: `squad --full` (now xp) → `transfer --squad` shows no positive moves; `ask "build me a squad for
£100m"` returns a sane 15 with the ✓ trust line; the points-vs-xP note is present.
