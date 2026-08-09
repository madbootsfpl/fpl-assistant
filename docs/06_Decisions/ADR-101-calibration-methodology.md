# Architectural Decision Record: Calibration methodology — how we tune the dormant weights on real returns

**Decision ID:** ADR-101
**Date:** 2026-08-09
**Status:** Accepted
**Superseded By / Replaces:** the *methodology* for flipping on the dormant modelling weights wired by ADR-060
(form), ADR-096 (set-piece), ADR-097 (DefCon). It does **not** change `decision_xp` or the one-xP invariant
(ADR-041) — it defines how a weight *value* is chosen (a backtest harness) so the eventual flip is principled, not
a guess. The weights stay `0` until calibration (post-GW1) recommends otherwise.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The season-start modelling is **wired dormant**: `FORM_WEIGHT` / `SET_PIECE_WEIGHT` / `DEFCON_MAGNIFIER_WEIGHT` are
all `0`, so xP is unchanged preseason (an invariance test pins it). "Data Hardening" is turning them **on**, but a
weight is only worth setting if we can show it **improves the model on real returns** — and there is **no tooling to
measure that** today. Before building a backtest harness, we need to agree *how we judge a weight is good*, or we'd
just be fitting noise.

**Verified at planning:**
- **The inputs exist.** `player_history(element_code, round, minutes, total_points, …)` gives per-GW **actuals**
  (`total_points`); `analytics/form.py` + the dormant weights give the **predictions** (`decision_xp`). What's
  missing is the comparison.
- **There is no data yet.** `player_history` is empty preseason; per-*season* summaries aren't per-GW. So real
  calibration is **GW4–6+** (a few GWs of returns; one GW is noise). The harness is built + tested on **synthetic**
  data now and produces real numbers as GW data accrues.
- **This is a *ranking* tool.** The app's job is *who to pick / captain / transfer* — an ordering. So how well the
  predicted xP **ranks** players against their actual points matters more than the absolute point error.

#### Decision Drivers
- **Principled, not a guess** — a weight is set only if a backtest shows it helps; the method is recorded.
- **Honest about a ranking** — optimise the ordering (rank correlation), not a false-precision point estimate.
- **No overfitting on thin data** — early-season returns are noisy; guard against chasing them.
- **Recommend, don't auto-flip** — the harness advises; the owner commits the value (reversible, reviewed).
- **Zero blast radius until then** — the weights stay `0`; the harness is read-only tooling; xP is byte-identical.

---

### ✅ Decision

**Choose weights with a walk-forward backtest that maximises the *rank correlation* between predicted xP and actual
points — recommending a value the owner commits, with the weights staying dormant until then.**

**1. The metric — rank first.** The primary score is **Spearman rank correlation (ρ)** between each gameweek's
predicted xP and the players' actual `total_points`, averaged across gameweeks. Because the product ranks players,
a weight that improves the *ordering* is what we want. **Secondary / sanity checks:** **MAE** (mean absolute error,
predicted vs actual points) and a **top-N hit-rate** (of the N highest-xP players, how many landed in the actual
top-N). A value must not *worsen* the sanity checks to be recommended.

**2. Walk-forward, never in-sample.** To score gameweek **N**, the prediction uses **only data up to N-1** (a
`gw_history` truncated to rounds `< N`, the fixtures/opponent for N). Scoring a GW with data that includes it would
flatter any weight (it "predicts" what it has seen). Walk-forward mirrors the real use — you set your team *before*
the gameweek.

**3. Sweep one weight at a time.** Calibrate `FORM_WEIGHT` first (the main season signal), then `SET_PIECE_WEIGHT`,
then `DEFCON_MAGNIFIER_WEIGHT` — each swept over a small range with the others held, so the effect is
**interpretable** (a learning-project value) and not confounded. Joint optimisation is rejected as over-fit-prone
and opaque on thin data.

**4. Overfitting guards.** (a) Require a **minimum number of gameweeks** (default **K = 4**) before trusting any
recommendation — below that the harness says *"need ≥K GWs (have N)"*. (b) When the metric curve is **near-flat**,
prefer the **smaller** weight (less reliance on a noisy signal). (c) Report the **whole curve** (value · ρ · MAE ·
hit-rate), not just a winner, so a spurious peak is visible.

**5. Recommend, the owner commits.** The harness **prints a recommendation**; it never writes a weight. The repo
default stays **`0` (dormant)** until the owner edits `config.py` and updates the invariance test — a reviewed,
reversible, per-weight code change (the GW1 runbook). So calibration can't silently change the model.

**6. It measures a ranking, not a probability.** Consistent with ADR-041 (one xP metric) and ADR-037/089 (grounded,
"a heuristic, not a probability"): the harness reports *how well the ranking holds up*, not a calibrated
probability. No claim of statistical significance on a hobby-sized sample — it's a decision aid, stated honestly.

---

### 🔀 Alternatives Considered

- **Optimise MAE (point error) as primary.** Rejected as the lead metric — the tool ranks players, and a model can
  have a larger absolute error yet a better ordering. MAE is kept as a **secondary** guard (a weight shouldn't blow
  up the point error).
- **In-sample fit** (score a GW using data that includes it). Rejected — it overfits by construction; walk-forward
  is the honest mirror of real use.
- **Auto-set the weight** from the sweep. Rejected — calibration **recommends**; a model change should be a
  reviewed, reversible commit, not a silent write. Keeps the one-xP invariant owner-controlled.
- **Joint / multivariate optimisation** of all weights at once (or a regression/ML fit). Rejected for now —
  opaque, overfit-prone on thin early data, and against the project's "understanding first" value. One weight at a
  time is interpretable; revisit only if the season yields ample data.
- **Cross-validation / significance testing.** Deferred — a hobby-sized, time-ordered sample doesn't support heavy
  statistics; walk-forward + a min-GW guard + reporting the whole curve is the proportionate honest method.
- **Wait and hand-tune at GW1 by eye.** Rejected — that's the guess this ADR exists to avoid; the harness makes the
  choice measurable and repeatable per weight.

---

### 🧭 Consequences

**Positive**
- **A principled flip** — each weight is set only if a walk-forward backtest shows it improves the ranking; the
  method (and the curve) is recorded, repeatable, and per-weight.
- **Honest to the tool** — optimising rank correlation matches "who to pick"; the caveats (a ranking, not a
  probability; a hobby sample) are stated, not glossed.
- **Zero risk until data + a decision** — the harness is read-only, the weights stay `0`, xP is byte-identical; the
  owner commits a value only when the numbers justify it.
- **Reusable** — one harness calibrates all three weights (and any future one) the same way.

**Negative / risks (mitigations)**
- **Thin early data is noisy.** *Mitigation:* the min-GW guard (K=4), one-weight-at-a-time, prefer the smaller
  weight on a flat curve, and report the whole curve — a spurious peak is visible, not auto-adopted.
- **Rank correlation ignores magnitude.** *Mitigation:* MAE + a top-N hit-rate as secondary checks; a recommended
  weight must not worsen them.
- **Walk-forward is fiddly** (truncating history per round). *Mitigation:* isolated in a pure `backtest.py`,
  unit-tested (a leakage test pins "only ≤ N-1 data used").
- **Over-trusting a hobby-sized backtest.** *Mitigation:* the ADR states it's a decision aid, not significance;
  recommendations are conservative and owner-committed.

---

### 🧾 Status & follow-ups

- **Accepted.** Built this sprint (prep): US-340 (`analytics/backtest.py` — walk-forward pairs + Spearman/MAE/
  hit-rate + a one-weight sweep, synthetic-tested), US-341 (a `python app.py calibrate` CLI + `docs/GW1_RUNBOOK.md`
  + a GW1-gated-features smoke). **The weights stay `0`** — xP byte-identical, the invariance test holds.
- **Owner actions (the GW1+ flip, data-gated):** at GW1 run `history --backfill` + verify the gated features; at
  ~GW4–6 run `calibrate --weight form` → if recommended, set `config.FORM_WEIGHT` + update the invariance test +
  commit; repeat for set-piece, then DefCon. All in `docs/GW1_RUNBOOK.md`.
- **Deferred:** rolling 3-/6-GW form windows; DGW/BGW + momentum season features; any heavier statistics if the
  season yields ample data.
