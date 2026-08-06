# Lessons Learned

**Sprint:** Sprint 075 — A filter on Trending (reuse the shared filter)

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Give the Trending page the **same Team · Position · Player filter** as Players and Player Stats — by reusing
the existing shared helper, not building anything new.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Reusing a page-agnostic helper (`filters.py`) to satisfy a whole feature request cheaply.
- Trusting the deterministic test over an eyeballed number when a smoke result looks odd.

### New Skills Acquired

- A concrete payoff of an earlier **shared-component** decision: the third consumer of the filter was a
  few lines, and its tooltips + coverage came for free from the prior sprints.

---

# What Went Well ✅

- **Reuse over rebuild** — `filter_controls`/`apply` (ADR-064) dropped straight into Trending: one import,
  one call, a per-board `apply`. No new analytics, no new ADR.
- **Free inheritance** — the filter's `help=` (ADR-065) came along, so the tooltip coverage test stayed
  green without a line of extra work.
- **The test caught the truth** — the AppTest (Team=ARS ⇒ ARS-only) confirmed the filter bites, even when a
  raw count looked suspicious.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Smoke showed "30 → 30" (looked like a no-op) | ARS + LIV really have 30 MIDs combined (big squads / fringe youth) | Verified the count directly; the deterministic AppTest already proved narrowing |
| The GW1-empty note vs a filter emptying a board | the all-zero check runs on filtered rows | Left as-is — momentum boards are all-zero preseason anyway; owned just shows "0 shown" |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Shared components compound | The Nth consumer of a page-agnostic helper is nearly free — and inherits its tests/tooltips |
| Trust the test | A deterministic AppTest assertion beats an eyeballed count when a smoke looks wrong |
| Know the data | FPL classifies many fringe/youth players as MID, so per-team MID counts are larger than intuition |

---

# Development Lessons 💻

- When a request is "same as X", check whether X's implementation is already reusable — often it's a few
  lines, not a feature.
- Don't over-trust a single smoke number; the crafted test is the ground truth.

---

# AI Collaboration Lessons 🤖

- The owner's one-liner ("Trending needs a filter, same as Players and Player Stats") mapped directly to the
  existing shared helper — the smallest possible sprint.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — this sprint **executes ADR-064** (the shared player filter) on a third page._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- If the ~570-name player multiselect ever feels unwieldy, a team-scoped variant (only players from the
  chosen teams) would help all three pages at once. Open items: pronoun-aware chat, a team-level
  squad-fixtures view, the tech-debt sweep (PuLP 4.0 + shared squad renderer), and — post-GW1 — the Data
  Hardening flip + calibration and the crowd/form-vs-xP backtest.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep investing in page-agnostic shared components; each later reuse is nearly free.

---

# Key Commands Learned

```text
python -m pytest tests/test_web_streamlit.py -k trending -q   # the Trending filter + pagination tests
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Executes an ADR | A sprint that applies an existing decision to a new place, needing no new ADR |
| Page-agnostic helper | A shared control (`filter_controls`) that works on any page's rows |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-064 | The shared filter this sprint reused |
| `src/web_streamlit/filters.py` | `filter_controls` + `apply` — now on Players, Player Stats **and** Trending |

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

- US-210 Trending filter — the shared Team · Position · Player filter on all four boards (reuses ADR-064)

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
