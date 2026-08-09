# Lessons Learned

**Sprint:** Sprint 129 — Build the DefCon opposition magnifier (wired-dormant) + persistence review

**Dates:** 2026-08-30

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Build the owner's DefCon opposition magnifier — a fixture-context re-weighting of DefCon points — in the one
`decision_xp` recipe, **double-counting-safe**, **off by default** (invariance-pinned), and **auditable**;
calibrate at GW1. Plus a review of cross-device persistence (done + dormant — owner-activated).

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Reframe to avoid double-counting** — re-weight what the baseline already prices; don't add a new component.
- **Wired-dormant modelling** — ship a change to the sacred metric at weight 0, pinned by an invariance test.

### New Skills Acquired

- **A delta beats a component when the baseline already prices the signal.** DefCon points are *in* the baseline
  (`total_points`), so adding a DefCon-xP component double-counts. Re-weighting the DefCon *share* by fixture — a
  delta `defcon_pts × (magnifier − 1)` that's **0 at neutral** — is correct *and* dormant-by-default. Same insight
  that shaped the set-piece term (ADR-096): find what's already counted before adding.
- **Fold a new term into `by_gameweek`, not just the total.** Adding the delta per-GW (not only to `xp`) keeps
  the ADR-032 invariant ("`by_gameweek` sums to `xp`") intact — a test pins it.
- **A user's data need may already be in the pipeline.** `player_xp` already carried the per-fixture difficulty
  the magnifier needs — no new plumbing; the review found it before the build assumed otherwise.
- **Auditable, but honest about direction.** A DefCon *lift* is a grounded ✓ reason ("🛡 edge (+X)"); a *drag*
  (easy fixture) isn't dressed up as a positive — the xp already reflects it. Only surface what's a genuine plus.

---

# What Went Well ✅

- **The review reframed the design** (the delta) before the build — correct + dormant-safe.
- **No new plumbing** — reused the per-fixture difficulty; folded the delta into `by_gameweek` (sums to xp).
- **Zero-risk ship** — weight 0 → the 816 byte-identical (invariance).
- **Persistence confirmed done** — owner-activated, no build.
- 811 → 822 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A DefCon component would double-count | the baseline already includes DefCon points | Re-weight the share — a delta, 0 at neutral |
| by_gameweek must still sum to xp | a separate additive term | Fold the delta into per-GW `unrounded`, then sum |
| The magnifier delta can be negative | easy fixtures reduce DefCon | Keep it in xp; only a *lift* is a ✓ reason |
| Can't calibrate the mapping preseason | DefCon is a new-season signal | Coarse defaults, dormant, calibrate at GW1 |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Delta vs component | Re-weight what's priced; don't add and double-count |
| Per-GW folding | Add a new term to `by_gameweek` to keep "sums to xp" |
| Reuse the pipeline | The per-fixture difficulty was already there |
| Honest reasons | Surface a lift as ✓; don't spin a drag |

---

# Development Lessons 💻

- Before adding to a shared metric, check what it already includes — often the fix is a re-weight, not an add.
- Keep derived invariants (`by_gameweek` sums to `xp`) true when you add a term — fold it in at the same level.
- Ship a metric change behind a default-0 weight + an invariance test; it lands with no blast radius.

---

# AI Collaboration Lessons 🤖

- The DefCon magnifier changes `decision_xp`, so — like form/xMins/set-pieces — it's a **modelling** term (an ADR
  + wired-dormant + auditable), not a lens; the grounded number (`defcon_xp`) makes turning it on transparent.

### Notes _(for Tony)_

---

# Decisions Made 📋

_**ADR-097 refined + built** — a fixture DefCon magnifier as a **delta on the DefCon share already in the
baseline** (`defcon_pts_per_match · (magnifier − 1)`, 0 at neutral → no double-count). `analytics/defcon_xp.py`
(`defcon_points_per_match` + `defcon_magnifier(FDR)`) wired into `player_xp` behind `config.DEFCON_MAGNIFIER_WEIGHT
= 0` (invariance-pinned); `defcon_xp` on the row + a "🛡 DefCon fixture edge" reason. A modelling change (not a
lens). Calibrate + backtest at GW1. Persistence (ADR-094): done + dormant — owner-activated, no build._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **GW1 (2026-08-21+): calibrate the DefCon magnifier** — set `DEFCON_MAGNIFIER_WEIGHT`, tune `DEFCON_P_SCALE` +
  the band, **backtest** on real DefCon returns (do magnified DEFs beat the flat ones vs strong opponents?).
  Alongside the set-piece + form calibrations (the Data Hardening flip).
- **Deferred:** a team-share adjustment for transferred players; a separate clean-sheet-xP magnifier (opposite
  direction); an Elo/xGC proxy refinement; the persistence handle-taken hint.
- **Owner:** activate cross-device squads (Supabase secrets, `docs/CLOUD_SQUADS.md`).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep reviewing what a shared metric already prices before extending it; keep modelling changes dormant + pinned.

---

# Key Commands Learned

```text
# set config.DEFCON_MAGNIFIER_WEIGHT > 0 to activate; a DEF vs a strong opponent shows "🛡 DefCon fixture edge (+X)"
python -m pytest tests/test_defcon_xp.py -q     # the magnifier: pts/match, band, the delta, invariance, the reason
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| DefCon delta | A re-weight of the DefCon share already in the baseline (0 at neutral) |
| P(clear) | Probability of clearing the position's defensive-actions threshold in a match |
| DefCon magnifier | A fixture multiplier (weak opp ~0.5 → strong ~1.5) from the FDR clean-sheet proxy |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/analytics/defcon_xp.py` | The pure `defcon_points_per_match` + `defcon_magnifier` |
| `src/analytics/xp.py` (`player_xp`) | The per-GW delta wiring (folded into by_gameweek) |
| `docs/06_Decisions/ADR-097-…` | The refined delta design + the traps |

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

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- ADR-097 refined + built — a fixture DefCon magnifier as a delta (no double-count), wired-dormant
- US-318 The pure DefCon-magnifier analytics (`defcon_points_per_match` + `defcon_magnifier`)
- US-319 The delta wired into `player_xp` — dormant + invariance + a grounded reason

**Stories Carried Forward:**

- The GW1 calibration + backtest (set the weight, tune the mapping/band on real returns).

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
