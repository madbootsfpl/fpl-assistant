# Lessons Learned

**Sprint:** Sprint 121 — Finish the fixtures planner: a budget cap + value on the targets

**Dates:** 2026-08-22

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Make **🎯 Target by fixtures** (Sprint 120) **budget-aware**: cap the price so you only see affordable targets, and
show/sort by **Val/£m** so a tight-budget planner finds the best pick per £. Display only — extend
`target_by_fixtures` + the Fixtures page; the FDR / xP / value analytics untouched.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Grow a function with keyword params, keep it pure** — four filters/sorts, still one unit-testable assembler.
- **Reuse the one metric** — Val/£m is `points_per_million` (ADR-042), not a new "value" invented for this view.

### New Skills Acquired

- **Filter before you truncate.** The cap drops pricier players *in the grouping loop, before* the per-team top-K
  pick — so £6.0m reveals each team's best *affordable* name, not "the top 3 with the dear ones blanked". A blunt
  post-filter would have shown fewer, worse rows; a pre-filter shows the right ones. A unit test pins the swap.
- **A sort toggle is just a swappable key.** `sort_by` picks `value_by_id` or `xp_by_id` as the sort key —
  the grouping, per-team pick and row shape are identical. One `lambda`, no branching in the loop body.
- **One value definition beats a "better" second one.** xP/£m would arguably fit an xP-ranked list better, but it
  would mean two "values" in the app to reconcile. Reusing the points-based Val/£m (ADR-042) keeps the Pool, the
  stat boards and the targets consistent — the known Isak-style under-rating is the honest, shared trade-off.

---

# What Went Well ✅

- **The function absorbed both stories** — `max_price` + `sort_by`/`value_by_id` — and stayed pure.
- **No new metric, no drift** — reused `points_per_million`; `team_fdr`/`decision_xp` unchanged.
- **Verified on real data first** — price range for the slider, and Val/£m sanity, before building.
- 771 → 775 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Cap = truncate or reveal? | filter placement matters | Filter *before* the per-team pick → best affordable surfaces |
| Which "value"? | xP/£m vs points/£m | Reuse the app's one Val/£m (`points_per_million`, ADR-042) |
| Value can be undefined | price ≤ 0 → `None` | `points_per_million` returns None; the column shows a dash, sorts last |
| Sort must keep the grouping | teams stay easiest-first | Swap only the *within-team* sort key, not the structure |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Pre-filter vs post-truncate | Filter candidates before the top-K pick to reveal the best survivors |
| Swappable sort key | A toggle = choose the key function; keep the loop identical |
| One metric, many views | Reuse the existing value metric; don't fork a second definition |
| Undefined-safe values | None-value sorts last + renders as a dash; don't invent a number |

---

# Development Lessons 💻

- When a control "filters a top-N list", filter the candidates first, then take N — order matters.
- Add a display option by threading a keyword param through one pure function, not by branching in the page.
- Prefer reusing an existing metric over a locally "better" one; consistency across views beats local optimality.

---

# AI Collaboration Lessons 🤖

- The targets still rank by the same `decision_xp` (and the same `points_per_million`) the rest of the app uses —
  the cap and the sort only choose *which* of those to show and in what order. No metric is invented at the edge.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — US-303/304 extend the display lens. `target_by_fixtures` gains `max_price`, `sort_by` ("xp"/"value")
and `value_by_id`; the value shown is the app's one **Val/£m** (`points_per_million`, ADR-042); xP stays the
default sort (ADR-041). Deliberately **not** adding an xP/£m future-value metric (a second value definition)._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Squad-aware affordability** on the targets — cap = your **bank + a sell**, not a flat price (needs the Fixtures
  page to know your active squad).
- **A "widen" control** (top-N teams / per-team count) if the fixed 6×3 feels tight.
- Post-**GW1 (2026-08-21)**: the target xP gains the in-season form blend automatically; Val/£m sharpens as real
  points accrue (new signings stop being under-rated).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep threading new list options through the one pure assembler; keep the page a thin renderer.

---

# Key Commands Learned

```text
python -m src.web_streamlit    # Fixtures → 🎯 Target: Max price slider + Sort (xP / Val/£m)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Pre-filter cap | Drop over-budget players before the per-team pick (reveal, not truncate) |
| Val/£m | Points per £m — the app's one value metric (ADR-042), points-based |
| Swappable sort key | A toggle that changes the ranking key, not the list's structure |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/analytics/targets.py` (`target_by_fixtures`) | The one assembler; now cap + sort aware |
| `src/analytics/value.py` (`points_per_million`) | The single Val/£m definition (ADR-042) |
| `src/web_streamlit/pages/2_Fixtures.py` | The Target section: position / max-price / sort controls |

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

- US-303 A max-price cap on 🎯 Target by fixtures (filter before the per-team pick — reveals the best affordable)
- US-304 A Val/£m column + an xP↔Val/£m sort toggle (reuses `points_per_million`, ADR-042)

**Stories Carried Forward:**

- None. (Squad-aware affordability + a "widen" control are follow-ups.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
