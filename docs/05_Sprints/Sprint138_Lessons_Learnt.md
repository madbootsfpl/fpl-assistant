# Lessons Learned

**Sprint:** Sprint 138 — GW1 Data Hardening: the calibration harness + the runbook (prep)

**Dates:** 2026-08-09

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Make GW1 (2026-08-21) a **confident switch-flip** for the dormant season-start weights (form / set-piece / DefCon):
build the **calibration/backtest harness** + the **runbook** + verify the GW1-gated features — so the weights can be
set on *evidence* when data arrives. No weight is changed this sprint (there's no data yet).

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Name the data constraint before scoping** — "no returns until GW4+" turned "flip the weights" into "build the tooling".
- **Decouple the untestable from the testable** — an injected predictor made the harness pure + synthetic-testable.

### New Skills Acquired

- **A "prep" sprint is the honest shape when the payoff is data-gated.** The weights *can't* be calibrated with no
  season data, so the deliverable is **readiness** — a tested harness + a runbook — not the values. Framing that up
  front (rather than pretending to "do Data Hardening") kept the scope truthful and useful.
- **Inject the dependency to make the untestable testable.** `backtest.py` takes the *predictor* as an argument, so
  it imports no analytics/config and is **fully unit-tested on synthetic data now** — while the CLI wires the real
  decision_xp predictor (validated at GW4+). The seam is the whole reason the harness is verifiable preseason.
- **No-leakage is a property you test, not assume.** Walk-forward "predict GW N from only rounds < N" is easy to
  get subtly wrong; a test that records the newest round the predictor is ever shown pins it.
- **A calibration tool must recommend, not act.** The CLI never writes a weight — it prints a recommendation; the
  owner commits it (with the invariance test updated). Keeps the one-xP invariant owner-controlled and reversible,
  and stops a noisy early sample from silently moving the model.
- **Optimise the metric that matches the job.** The app *ranks* players, so the target is rank correlation
  (Spearman), not point error — a model can be "more wrong" in points yet rank better.

---

# What Went Well ✅

- **Right, honest scope** — tooling + runbook now; weight values as a data-gated follow-up.
- **Pure, injected harness** — synthetic-tested end to end, independent of decision_xp.
- **No-leakage pinned** — the walk-forward guarantee is a test.
- **Recommend-not-flip** — the CLI can't silently change the model; the owner commits.
- 898 → 916 tests (+18); ruff + CI green; the weights stay 0 (xP byte-identical).

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Nothing to calibrate against | no per-GW returns until the season runs | Build + test the harness on synthetic data; values are GW4+ |
| The harness would couple to decision_xp | it needs predictions | **Inject** the predictor — pure harness, real predictor in the CLI |
| Walk-forward can leak the future | using data ≥ N to score N flatters any weight | Truncate to rounds < N; a test records the newest round shown |
| `get_upcoming_fixtures` excludes finished GWs | it filters `finished = 0` | New `Storage.get_fixtures_by_event` (finished or not) |
| The full predictor is unprovable now | no real returns | Test the insufficient path + pure helpers; validate at GW4+ (runbook) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Data-gated work | When the payoff needs data you don't have, ship the tooling + runbook (readiness) |
| Dependency injection | Inject the predictor → a pure, synthetic-testable harness |
| Walk-forward | Predict N from < N only; pin no-leakage with a test |
| Metric choice | A ranking tool optimises rank correlation, not point error |
| Recommend, don't act | Calibration prints a value; the owner commits it (invariant stays owner-controlled) |

---

# Development Lessons 💻

- Scope to what the data allows: build + test the machinery now, defer the values to when returns exist.
- Make the hard-to-test thing injectable so the surrounding logic is testable without it.
- Encode a correctness property (no leakage) as a test, not a comment.

---

# AI Collaboration Lessons 🤖

- The harness sits **outside** the engine: `backtest.py` imports no analytics/config, and the CLI only *reads* +
  *recommends* — it never mutates a weight. So the one-xP invariant (ADR-041) and the grounded posture (ADR-037)
  are untouched; calibration is a decision aid the owner acts on, not an autonomous model change.

### Notes _(for Tony)_

---

# Decisions Made 📋

_**ADR-101** — calibration methodology: a **walk-forward** backtest maximising **Spearman rank correlation**
(predicted xP vs actual points; MAE + hit-rate as checks), **one weight at a time**, **overfitting guards** (≥K
GWs, smaller weight on a flat curve), **recommend not auto-flip** (weights dormant/0 until the owner commits). Built
prep: US-340 (`analytics/backtest.py`, synthetic-tested), US-341 (`calibrate` CLI + `docs/GW1_RUNBOOK.md` + a
GW1-readiness smoke). The weight values are the data-gated GW1+ follow-up._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner (GW1, 2026-08-21):** `python app.py history --backfill` + verify the gated features (manager-import,
  momentum, price, community signals) on live data.
- **Owner (~GW4–6):** `python app.py calibrate --weight form` → if it clearly helps, set `config.FORM_WEIGHT` +
  update the invariance test + commit; then set-piece, then DefCon. All in `docs/GW1_RUNBOOK.md`.
- **Deferred:** rolling 3-/6-GW windows; DGW/BGW + momentum season features; elite-manager comparison.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep data-gated work honest: build the tooling + runbook first; set the values when the data justifies it.

---

# Key Commands Learned

```text
python app.py calibrate --weight form            # backtest + recommend a weight (says "insufficient" until ~GW4+)
python app.py history --backfill                 # accrue the per-GW returns the backtest needs (run each GW)
python -m pytest tests/test_backtest.py -q       # the metrics + no-leakage walk-forward + the sweep
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Walk-forward | Predict gameweek N using only data before N (no in-sample leakage) |
| Rank correlation (Spearman) | How well predicted xP *orders* players vs their actual points |
| Overfitting guard | Min-GW threshold + prefer the smaller weight on a flat curve |
| Recommend-not-flip | The harness prints a value; the owner commits it |
| Prep sprint | Build the tooling + runbook now; set the data-gated values later |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/analytics/backtest.py` | The pure walk-forward harness (pairs / metrics / sweep) |
| `src/cli.py` (`cmd_calibrate`) | The decision_xp-backed sweep + the recommendation |
| `docs/GW1_RUNBOOK.md` | The ordered GW1 → calibrate checklist |
| `docs/06_Decisions/ADR-101-…` | The methodology (rank-correlation, walk-forward, guards) |

---

# Questions for Future Me ❓ _(for Tony)_

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?

---

# Summary

**Sprint Outcome:** ☑ Successful (prep — the GW1+ flip is a documented follow-up) ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- ADR-101 Calibration methodology (walk-forward, rank correlation, recommend-not-flip)
- US-340 The backtest harness — `analytics/backtest.py` (pairs / metrics / sweep), synthetic-tested
- US-341 The `calibrate` CLI + `docs/GW1_RUNBOOK.md` + the GW1-readiness smoke

**Stories Carried Forward:**

- The GW1+ flip (set the weight values on real returns) — data-gated, in `GW1_RUNBOOK.md`.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
