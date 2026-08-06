# Lessons Learned

**Sprint:** Sprint 082 — Make the stat numbers interpretable · per-tab header graphics

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Let a casual user read the stat boards at a glance — each metric says what it *is* (absolute vs per-90) and
carries a **self-calibrating colour rating** (best/worst vs the players shown) with the percentile inline;
and give every tab a consistent, friendly **emoji header** like Home.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Verifying a proposed design against real data before building it** — the single most valuable move this
  sprint (see below). A number that "looks reasonable" (ChatGPT's band table) was quietly wrong for FPL.
- Keeping display policy at the **web edge** so the analytics core stays pure.

### New Skills Acquired

- A **relative (quantile) rating** is often more honest than a fixed absolute scale: it self-calibrates to
  the real field, needs no threshold maintenance, and is correct at GW1 with no code change.
- `st.column_config.Column(head, help=...)` adds a **per-column tooltip** to `st.dataframe` — but there's
  **no per-cell hover**, so an inline anchor (the percentile in the cell) is the workaround.
- `AppTest` exposes `at.title` (`.value`), so an emoji-led header is testable.

---

# What Went Well ✅

- **Real-data check flipped the approach.** The tester's ChatGPT bands would have bucketed **91/117**
  defenders as "poor" and 1 as "excellent". Measuring the actual xGC/90 distribution (median 1.36) turned
  "copy the table" into a *relative quintile* rating that actually helps — and answers the tester's real
  question ("is 0.52 good, or just relative?") truthfully.
- **Tight, well-layered change** — a small web-side helper + two boards; the analytics and the sort order
  were untouched; the signed boards (over/under, DefCon) were deliberately left alone.
- **A cosmetic story stayed cosmetic** — the header pass was a title + caption per page, no logic, one test.
- 598 → 607 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| ChatGPT's fixed band table mislabels almost everyone "poor" | its scale is team goals-per-match (~1.1 avg); FPL player xGC/90 sits higher (median 1.36) | Rate **relative to the pool shown** (quintiles) instead of fixed thresholds |
| Rating shouldn't change as you page | pagination slices the board | Compute the rating over the **filtered** board (all pages), not the visible page |
| No per-cell hover in `st.dataframe` | Streamlit limitation | Put the percentile **inline** in the Rating cell (colour + number both visible); tooltips at the column header |
| A missing xGI would rate as worst | `None` coerced to 0.0 | Acceptable + honest (no attacking threat); the pool uses `xgi or 0.0` |
| Changing tab titles could break assertions | tests might pin exact titles | Verified none do (the Help test checks the body, not the title); safe |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Relative vs absolute rating | Relative bands self-calibrate and stay honest; fixed bands need constant re-checking and can mislead |
| Verify on real data | A plausible external scale (ChatGPT's) can be quietly wrong for your data — always measure the distribution first |
| Display policy at the edge | Pool-relative presentation lives web-side; the analytics core stays pure and one-way |
| `st.dataframe` limits | Column tooltips yes; per-cell hover no → anchor inline |
| Stable ratings across pages | Compute over the full filtered set, not the current page |

---

# Development Lessons 💻

- When a tester hands you a rule of thumb, treat it as a hypothesis — check it against the real numbers
  before wiring it in.
- Prefer the honest, self-calibrating option (relative) over the intuitive-but-brittle one (fixed) when the
  data says the fixed thresholds don't fit.
- Keep cosmetic and substantive work in separate stories — the header pass was fast precisely because it
  carried no logic.

---

# AI Collaboration Lessons 🤖

- The owner's "hybrid: band + percentile" call was the right synthesis — a scannable colour for the casual
  user, plus a precise anchor for anyone who wants the number. Surfacing the real-data finding up front made
  that an informed decision rather than a guess.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-071 | **Interpretable stat boards** — a display-only quality **rating** (`web_streamlit/ratings.py::quality_band`) rating a value **relative to the players shown** (quintile 🟢…🔴) + the percentile inline; a **Rating** column on Clean sheets (xGC/90) + xG (xGI) + a legend; clearer captions + per-column tooltips on all four boards. Relative (not fixed) because real FPL xGC/90 makes ChatGPT's fixed table mislabel 91/117 "poor"; analytics untouched, no server writes | Accepted |

(US-222 — per-tab header graphics — was cosmetic, no ADR.)

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Post-**GW1 (2026-08-21)**: the Data Hardening flip (`history --backfill` + raise `FORM_WEIGHT`) + xP
  calibration — and the stat ratings sharpen as the season's real numbers come in.
- Possible: extend the quality rating to the **CLI** stat commands, or add a rating to the Players **Pool**.
- Still open: pronoun-aware chat; the crowd/form-vs-xP backtest.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the "check the tester's assumption against real data first" step in planning — it changed the design
  here and is cheap to run.

---

# Key Commands Learned

```text
python -m src.web_streamlit           # Players → Clean sheets / xG now show a 🟢…🔴 Rating column + legend
python -m pytest tests/test_ratings.py -q     # the quality-band unit tests (both directions, ties, extremes)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Quality band | A quintile colour (🟢 excellent … 🔴 very poor) rating a value against the pool shown |
| Relative / quantile rating | Rated by rank within the field, not a fixed threshold — self-calibrating |
| Percentile anchor | The "top N%" shown inline so the colour band is tied to a concrete number |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-071 | The rating decision + the real-data evidence against fixed bands |
| `src/web_streamlit/ratings.py` | The reusable `quality_band`/`rating_cell` helper |
| `src/web_streamlit/views/players.py` | Where the boards apply the rating + tooltips |

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

- US-221 Interpretable stat boards — a relative quality rating (`quality_band`) + a Rating column on Clean
  sheets (xGC/90) & xG (xGI) + a legend; clearer captions + per-column tooltips on all four boards (ADR-071)
- US-222 Per-tab header graphics — an emoji-led title + tagline on all 7 tabs (👟📅🧩💬📰📈🧭)

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
