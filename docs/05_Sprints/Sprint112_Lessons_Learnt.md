# Lessons Learned

**Sprint:** Sprint 112 — Price Change Predictor (a directional lens, wired dormant → GW1)

**Dates:** 2026-08-13

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Build the last buildable-now item of the 5-request intake: a **Price Change Predictor** — flag players about to
**rise/fall** in value, to time transfers. A *directional flag, not the truth*, built wired-but-dormant so GW1
is a switch-flip. A display/analytics **lens** — never `decision_xp`.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Modelling within data limits** — designing an honest signal from the fields we actually have.
- **The wired-dormant → GW1 pattern** (ADR-060) applied again — build now, calibrate at the season start.

### New Skills Acquired

- **Sometimes the maths removes the dependency.** FPL's price threshold scales with ownership, so
  `net_transfers ÷ selected_by%` measures pressure *per unit of the threshold* — and the (unavailable) constant
  total-manager count **cancels** for direction + relative magnitude. A principled signal with **no** new
  ingest, no `total_players`, no since-last-change counter.
- **Distinguish forward-looking from retrospective.** The crowd lens already had 💰/💸 (a change that already
  happened); the predictor is *about to* move — so a distinct 🔺/🔻 marker + a legend that names the
  difference avoids confusing the two.
- **A lens must prove it's a lens.** Reusing the transfer fields, the honest guarantee is a `decision_xp`
  invariance test: force strong pressure so the flag fires, and assert xP is byte-identical.
- **Dormant needn't mean invisible.** Preseason the signal reads all "—", but the Pool column + legend and a
  My Squad dormant note ("live from GW1") make the feature discoverable before it has data.

---

# What Went Well ✅

- **A principled v0 from fields we already store** — no ingest/schema change.
- **Honest framing** — a flag, not exact price/timing; a "live from GW1" caption; no false precision.
- **The lens invariant held** — the predictor never leaks into the recommendations.
- 730 → 737 tests; ruff + CI-parity green; ADR-092 records the design.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| No exact price/timing available | FPL's threshold + since-last-change counter aren't published | Ship a *directional* pressure, framed honestly |
| Comparing players fairly | net transfers scale with ownership | Divide by `selected_by%` → comparable; total-managers cancels |
| Not re-skinning 🔥/❄️ or 💰/💸 | crowd already has momentum + retrospective price | A forward-looking pressure + a distinct 🔺/🔻 marker |
| Proving it's a lens | it reads the same transfer fields as xP inputs | A `decision_xp` invariance test that forces the flag to fire |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Normalisation | Dividing by ownership both makes players comparable and cancels a missing constant |
| Forward vs retrospective | Name the difference in the marker + legend so signals don't blur |
| Lens invariants | Force the lens to fire, then assert the grounded output is unchanged |
| Dormant features | Keep them visible (column + "live from GW1") so they're discoverable pre-data |

---

# Development Lessons 💻

- Look for a normalisation that removes a data dependency before adding ingest/schema.
- When a new signal overlaps an old one, differentiate it visually and in copy.
- Prove a "display-only" claim with an invariance test, not just a comment.

---

# AI Collaboration Lessons 🤖

- The grounded-lens discipline (ADR-057) makes a new signal safe to add: it's computed from stored data,
  clearly labelled, and pinned out of xP — so it informs without ever distorting the recommendations.

### Notes _(for Tony)_

---

# Decisions Made 📋

_**ADR-092** (new) — a Price Change Predictor: an ownership-normalised transfer-**pressure** lens
(`net_transfers ÷ selected_by%`) → a rise/fall/stable flag; comparable across players (total-managers cancels),
no new ingest, dormant → live at GW1, and **never** `decision_xp` (an invariance test pins it). New:
`analytics/price.py` (`price_pressure`/`price_prediction`/`price_flag` + `PRICE_LEGEND`)._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Calibrate the price thresholds at GW1** on real net transfers (like `TRENDING_NET`/`FORM_WEIGHT`).
- **An absolute "% to the next change"** — a GW1/Tier-3 refinement (needs `total_players` + a since-last-change
  counter).
- **A CLI Price column** + an `ask` "who's about to rise?" intent.
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- Post-**GW1 (2026-08-21)**: Data Hardening + xP calibration; the crowd/price/form signals all light up.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep verifying a signal on real (flat, preseason) data first — it confirms the dormant-then-live shape.

---

# Key Commands Learned

```text
# The Price column + My Squad nudge are web-only for now:
python -m src.web_streamlit   # → Players → Pool (Price column) · Squads → My Squad (timing nudge)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Price pressure | Net transfers per 1% ownership — a cross-player-comparable buy/sell pressure |
| Directional flag | A rise/fall/stable call, not the exact price or timing |
| Lens invariant | The rule that a display signal never changes `decision_xp` |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/analytics/price.py` | The price-pressure engine (ADR-092) |
| `docs/06_Decisions/ADR-092-price-change-predictor.md` | Why net÷ownership + dormant → GW1 |
| `tests/test_price.py` | The engine tests incl. the `decision_xp` invariant |

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

- US-285 Price-pressure engine — `price_pressure`/`price_prediction`/`price_flag`, dormant → GW1, never xP (ADR-092)
- US-286 Surface the prediction — a Pool Price column + a My Squad transfer-timing nudge (display-only)

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
