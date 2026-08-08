# Lessons Learned

**Sprint:** Sprint 114 — Four-tier ownership badges (one ownership language)

**Dates:** 2026-08-15

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Adopt the tester's ownership-badge proposal — 💎 differential · ⭐ popular · 🟦 template · 👑 essential — as four
clear tiers shown consistently on every tab, and make the recommendation "why" speak the same language. A
crowd-lens + explanation refinement; the analytics/xP untouched.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Evaluating a proposal on data** before adopting — the distribution proved the tiers fill real gaps.
- **Refactoring at the shared point** so one edit changes every surface consistently.

### New Skills Acquired

- **Challenge, then verify on real data.** The tester invited a challenge; checking the ownership spread
  (500/57/15/1) showed the 5–20% band was genuinely unbadged and the >60% player mis-lumped with template — so
  the proposal was right, with one refinement (align the differential cut to the ≤5% filter).
- **A shared function is the leverage point.** `crowd_flags` *is* the Trends column everywhere, so refining its
  ownership block updated six surfaces at once — no per-tab work, no drift.
- **Unify vocabulary with a tiny helper.** `ownership_label` + `_ownership_signal` let three explanation
  functions speak the tier language identically, keeping the badges and the "why" in sync.
- **A relabel is low-churn if the boundaries hold.** Most explain fixtures sit in 20–60% → still "Template
  pick", so only the ≤5% and >60% cases changed — small, contained edits.

---

# What Went Well ✅

- **One edit, six surfaces** — the badge change propagated through `crowd_flags`.
- **Grounded challenge** — the data confirmed the tiers before any code.
- **The lens invariant held** — ownership feeds badges + wording only, never xP.
- 738 → 739 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| 5–20% band unbadged, >60% mis-lumped | the old 2-tier badge | Four tiers via `ownership_tier` |
| Keeping badges + "why" in sync | separate strings in each explain fn | A shared `ownership_label`/`_ownership_signal` |
| Boundary alignment | differential filter is ≤5, badge could be <5 | Align the tier cut to `DIFFERENTIAL_OWN` (≤5) |
| Unused import after the relabel | `TEMPLATE_OWN` no longer referenced in explain | `ruff --fix` dropped it |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Shared leverage point | Refine the one function every surface uses |
| Vocabulary sync | A label helper keeps badges + explanations consistent |
| Boundary alignment | Match a new classification to the existing filter |
| Low-churn relabels | Change only the boundary cases; keep the common path identical |

---

# Development Lessons 💻

- Verify a proposal against real data before adopting or refining it.
- Change behaviour at the shared function, not per consumer.
- When two surfaces name the same concept, drive both from one helper.

---

# AI Collaboration Lessons 🤖

- The grounded-lens discipline made the tiers safe: they classify ownership for display + wording, and a test
  pins them out of `decision_xp`, so richer badges never distort the recommendations.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — US-289 extends **ADR-057** (crowd lens); US-290 extends **ADR-089** (explainability). New:
`analytics/crowd.py::ownership_tier` (💎/⭐/🟦/👑) + `ownership_label` + `ESSENTIAL_OWN = 60`; `crowd_flags` and
`CROWD_LEGEND` updated; `explain.py::_ownership_signal` gives the explanations the tier vocabulary._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Calibrate the ownership thresholds at GW1** (esp. `ESSENTIAL_OWN`) as ownership concentrates.
- **A hosted LLM for the deploy** so the prose + free-form tail work on the cloud.
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- Post-**GW1 (2026-08-21)**: Data Hardening + xP calibration; the price/form/ownership tiers all sharpen as data
  arrives; calibrate the price-predictor thresholds too.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep verifying feedback on real data before adopting — it turns "maybe" into a grounded yes/no.

---

# Key Commands Learned

```text
python -m src.web_streamlit   # Players → Pool / Trending: 💎/⭐/🟦/👑 ownership tiers
python app.py ask "is Haaland worth the money?"   # the "why" now reads "Essential (74% owned)"
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Ownership tier | 💎 differential ≤5 · ⭐ popular 5–20 · 🟦 template 20–60 · 👑 essential >60 |
| Essential | A >60%-owned must-own — going without is a major rank risk |
| One language | Badges + explanations use the same ownership words |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/analytics/crowd.py` (`ownership_tier`, `ownership_label`, `CROWD_LEGEND`) | The tiers + the shared word |
| `src/analytics/explain.py` (`_ownership_signal`) | The tier vocabulary in the "why" |
| `tests/test_crowd.py` | The per-band tier tests |

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

- US-289 Four-tier ownership badges — `ownership_tier` (💎/⭐/🟦/👑) in `crowd_flags`, everywhere (extends ADR-057)
- US-290 One ownership language — the tier vocabulary in the explanations + the Trending/Help legend (extends ADR-089)

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
