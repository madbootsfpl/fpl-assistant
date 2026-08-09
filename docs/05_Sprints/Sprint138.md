# Sprint 138: GW1 Data Hardening — the calibration harness + the runbook (prep)

**Dates:** 2026-08-09
**Status:** 🚧 In progress (ADR-101 accepted · 2 stories to build) — **prep now; weight *values* are a GW1+ follow-up**
**Capacity:** ~1 session (a backtest harness + a runbook + a features smoke)
**Carried Over:** the long-deferred Data-Hardening body (Sprint 069 wired it dormant)

> **Direction (owner):** GW1 = **2026-08-21** (~12 days out). The season-start modelling is wired **dormant**
> (form / set-piece / DefCon weights = 0). "Data Hardening" is flipping those on **calibrated on real returns** —
> plus verifying the GW1-gated features (live manager-import, momentum, price). This sprint builds the **tooling +
> runbook** so GW1 is a confident switch-flip, not a scramble.

---

### 🔎 Verified at planning (on real data + the code)

- **The machinery is built + dormant; the *calibration* is the gap.** `analytics/form.py` (`form_rate`/`blend_form`),
  `ingest.backfill_history` (the throttled per-GW `element-summary` walk), the `player_history` table
  (`element_code, round, minutes, total_points, …` — **`total_points` per round = the backtest "actuals"**), and
  the three dormant weights all exist. **There is no backtest/accuracy tooling anywhere** — that's what's missing.
- **You can't set the weights now — there's no data.** `player_history` is **empty preseason**; `player_history_past`
  is per-*season* summaries (not per-GW). So there are **no per-GW returns to calibrate against until the season
  runs** — and one GW is noise; form needs a window (~3–5 GWs) to mean anything. **Real calibration is ~GW4–6**, not
  GW1. So this sprint builds + tests the harness on **synthetic data**, and it produces real numbers as GW data
  accrues.
- **Calibration is a genuine methodology decision → ADR-101.** *How* we judge a weight is "good" — the metric
  (this is a **ranking** tool, so rank-correlation matters more than absolute error), **walk-forward** (predict GW N
  from data ≤ N-1, never in-sample), and **overfitting guards** on thin early data — needs recording before we
  build, so the eventual weight-setting is principled, not a guess.
- **The GW1-gated features already degrade gracefully; they just need a *verify*.** Live manager-import (picks
  unlock post-deadline, ADR-058), momentum/trending (0 preseason → live GW1), the price predictor (ADR-092), and
  community signals (may degrade on the cloud IP) are wired — a code-path smoke + a checklist means no GW1 surprises.
- **The weights stay 0 in the repo after this sprint.** Calibration *recommends* a value; the owner sets it (a
  small config change + the invariance test updated) as a **GW1+ follow-up** when the harness says so — off by
  default until then (the one-xP invariant, ADR-041, holds).

---

### 🎯 Sprint Goal

**Objective:** GW1 becomes a **documented switch-flip**: a **calibration/backtest harness** that measures how well
`decision_xp` predicts real returns and recommends a weight, a **GW1 runbook** (what to run when), and a **verified**
set of GW1-gated features. No weight is changed this sprint (no data yet); the tooling is ready + tested.

#### Success criteria
- [x] **ADR-101 (the gate)** — record the **calibration methodology**: the primary metric = **rank correlation**
      (Spearman) between predicted xP and actual points (it's a ranking tool), with **MAE** + a **top-N hit-rate**
      as secondary; **walk-forward** (predict GW N using only data ≤ N-1); **overfitting guards** (a minimum # of
      GWs before trusting a value, sweep **one weight at a time**, prefer a *conservative* weight when the metric is
      near-flat); that calibration **recommends**, the owner **sets** (weights stay dormant/0 in the repo until
      then, invariance-pinned); and that this measures a *ranking*, not a probability (honest, ADR-041 intact).
- [x] **US-340 (the backtest harness)** — a pure `analytics/backtest.py`: `pairs(...)` (walk-forward
      predicted-xP vs actual `total_points` per player/round), `spearman(pairs)` / `mae(pairs)` / `hit_rate(pairs, n)`,
      and `sweep(weight_name, values, ...) → [(value, metrics)]` + the best. Weight-agnostic (demo on `FORM_WEIGHT`;
      extends to set-piece/DefCon). Fully unit-tested on **synthetic** data (a known-rank set → Spearman ≈ 1; a
      sweep picks the best); empty/thin data → a clear "not enough GWs yet".
- [ ] **US-341 (the CLI + the runbook + the features verify)** — a `python app.py calibrate --weight form
      [--range …]` command that runs the sweep on the stored `player_history` and prints the metric per value + the
      recommendation (or "need ≥N GWs"). A **`docs/GW1_RUNBOOK.md`** — the exact ordered checklist (GW1: backfill +
      verify features; GW3–6: `calibrate` → set the weight → re-run the invariance test → commit; per-weight). A
      **features smoke** (manager-import / momentum / price code paths degrade cleanly now → light up at GW1).
- [ ] **No unintended drift** — the weights stay **0** (xP byte-identical; the invariance test holds); the harness
      is read-only (no writes, no engine change); existing **898** stay green; ruff clean.
- [ ] **Docs** — ADR-101 + index; `docs/GW1_RUNBOOK.md`; Roadmap (Data Hardening → in progress, the runbook);
      PROJECT_STATUS; Architecture; a `config.py` pointer to `calibrate`.

---

### 🧭 Design sketch

**ADR-101 — calibration methodology.** We're tuning a **ranking** (who to pick), so the target is **rank
correlation** (Spearman ρ between predicted xP and actual points across players, per GW, averaged), with MAE + a
top-N hit-rate as sanity checks. **Walk-forward** avoids the in-sample trap: to score GW N, predict with only
data ≤ N-1 (a truncated `gw_history`). **Guards:** need ≥ K GWs (e.g. 4) before trusting a value; sweep **one**
weight at a time; when the curve is near-flat, pick the **smaller** weight (less overfit to noise). Calibration
**recommends**; the owner **commits** the value — the repo default stays dormant (0), the one-xP invariant intact.

**US-340 — `analytics/backtest.py` (pure).**
```
def pairs(players, upcoming, history, gw_history_by_round, weights) -> list[(pred, actual)]:
    # for each round N with actuals, decision_xp using data ≤ N-1 (walk-forward) → (predicted xP, total_points)
def spearman(pairs) / mae(pairs) / hit_rate(pairs, n)          # the metrics (stdlib; no new dep)
def sweep(weight_name, values, ...) -> {"best": v, "rows": [(v, metrics)]}
```
Weight-agnostic (`weight_name ∈ {form, set_piece, defcon}`). Unit-tested on synthetic pairs (a monotonic set →
ρ≈1; a U-shaped error curve → the sweep finds the min); thin data → a `None`/"insufficient" signal.

**US-341 — CLI + runbook + verify.** `cmd_calibrate` runs `sweep` on `Storage.get_gw_history_by_code()` and prints
a small table (value · ρ · MAE · hit-rate) + the recommendation, or "need ≥K GWs (have N)". `docs/GW1_RUNBOOK.md`
turns the scattered "at GW1" notes into **one ordered checklist**. The features smoke asserts the GW1-gated paths
(`manager.fetch_manager_team`, momentum/trending, `price` intent) degrade cleanly preseason (they already do — a
regression guard).

**Deferred (the GW1+ follow-up, needs data):** actually **running** `calibrate` on live returns and **setting**
`FORM_WEIGHT` (then set-piece, then DefCon) + updating the invariance test; rolling 3-/6-GW windows; the
momentum/DGW-BGW season features. This sprint makes those a documented flip.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| ADR-101 | **Calibration methodology** — rank-correlation + walk-forward + overfitting guards (the gate). | High | ✅ Done | gate |
| US-340 | **The backtest harness** — `analytics/backtest.py` (pairs/metrics/sweep), synthetic-tested. | High | ✅ Done | ~½ session |
| US-341 | **CLI `calibrate` + `GW1_RUNBOOK.md` + the features smoke.** | High | ⬜ To do | ~⅓ session |

---

### 🧑‍💻 Owner runbook actions (the GW1+ flip — documented, not this sprint)

1. **At GW1 (2026-08-21):** `python app.py history --backfill` (starts per-GW collection) + verify the GW1-gated
   features (manager-import, momentum, price) on live data.
2. **~GW4–6 (data accrued):** `python app.py calibrate --weight form` → if it recommends a value, set
   `config.FORM_WEIGHT`, update the invariance test, commit. Repeat for set-piece, then DefCon. (All in
   `GW1_RUNBOOK.md`.)

---

### ✅ Definition of Done

1. **Tests** — the metrics are correct on synthetic data (a monotonic set → ρ≈1; MAE exact; the sweep finds the
   min of a U-curve); walk-forward uses only ≤ N-1 data (a test pins it); thin/empty data → "insufficient"; the
   `calibrate` CLI prints a table / the "need ≥K GWs" note; the features smoke passes. **The weights stay 0 → xP
   byte-identical (the invariance test holds).** Existing **898** green; ruff clean.
2. **Manual smoke** — `python app.py calibrate --weight form` on the seed DB → "need ≥K GWs" (no data yet), no
   crash; the runbook reads as a clean checklist.
3. **Docs** — ADR-101 + index; `docs/GW1_RUNBOOK.md`; Roadmap; PROJECT_STATUS; Architecture.

---

### 📝 Session Progress Log

- **ADR-101 (the gate)** — wrote `docs/06_Decisions/ADR-101-calibration-methodology.md` (Accepted). Records the
  **calibration methodology** for flipping on the dormant weights (ADR-060/096/097): a **walk-forward** backtest
  (predict GW N from data ≤ N-1, never in-sample) that maximises **Spearman rank correlation** between predicted xP
  and actual `total_points` (it's a **ranking** tool; MAE + a top-N hit-rate are secondary sanity checks); **one
  weight at a time** (interpretable, `FORM_WEIGHT` first); **overfitting guards** (need ≥K=4 GWs, prefer the smaller
  weight on a flat curve, report the whole curve); calibration **recommends**, the owner **commits** (the repo
  stays dormant/0 until then, the one-xP invariant intact); a **decision aid, not a probability/significance**
  claim (ADR-041/037). Alternatives recorded (MAE-primary ✗, in-sample ✗, auto-set ✗, joint/ML fit ✗, cross-val
  deferred, hand-tune ✗). Added to the ADR index. **101 ADRs.** No code — suite unchanged at **898**. (US-340 builds
  the harness next.)
- **US-340 (the backtest harness)** — added `src/analytics/backtest.py`: **pure + read-only** (imports no
  analytics/config; the predictor is **injected** — decision_xp-backed in the CLI, synthetic in tests). `pairs()`
  builds walk-forward `(predicted, actual, round)` triples — for each round N it calls `predict(history_before_N,
  N)` using **only rounds < N** (no leakage); metrics `spearman` (rank-based via average-rank + Pearson-on-ranks),
  `mean_gw_spearman` (the primary — per-GW ρ averaged), `mae`, `hit_rate(n)` (top-N overlap per GW); `sweep()`
  scores each weight value and returns `{gws, rows, best}` — **best = the smallest value within `_FLAT_EPS` of the
  top ρ** (the overfitting guard) or `{insufficient}` below `MIN_GWS=4`. **+12 tests** (all synthetic, since real
  returns are GW4–6 away): ties/perfect/reversed/non-linear Spearman · None-without-spread · exact MAE · hit-rate
  overlap · per-GW averaging · **no-leakage walk-forward** · triple-building · sweep insufficient/best/flat-curve.
  **No engine change — the weights stay 0, xP byte-identical.** ruff clean. **898 → 910.** (US-341 wires the
  `calibrate` CLI + the runbook + the features smoke.)

---

### 🏁 Sprint Review & Retrospective

_(filled at retro)_

---

### 📌 For Tony — decisions before I gate ADR-101

1. **Scope** — build the **calibration harness now** (my recommendation — it's the missing piece + makes GW1 a
   flip; testable on synthetic data), or keep this sprint to a **runbook + features-verify only** and build the
   harness at GW1 when there's data to shape it?
2. **The metric** — optimise **rank correlation** (Spearman; my rec — it's a ranking tool) as primary, with MAE +
   hit-rate as checks; or lead with **point error (MAE)**?
3. **First weight** — build weight-agnostic but **demo/validate on `FORM_WEIGHT`** (the main season signal), set-piece
   + DefCon to follow the same path? (My rec: yes.)
