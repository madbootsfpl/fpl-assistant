# Lessons Learned

**Sprint:** Sprint 086 — The XI score in the formation preview

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Give the Build page's "🔎 Preview the best XI in a shape" a **projected XI score**, and — on request — a
**ranked comparison of all formations**, so a user can see how much each shape is worth (display-only; the
saved build stays a full 15).

---

# Knowledge Compounded 📈

## Skills Strengthened

- Turning an existing computation into a **user-facing number** (the preview already solved the XI; it just
  never summed it).
- Weighing a feature's value against its **render cost** and gating accordingly.

### New Skills Acquired

- A **Streamlit expander body executes even when collapsed** (like `st.tabs`, unlike `st.segmented_control`)
  — so anything expensive inside it runs on every render unless gated (a checkbox / a lazy control).
- `st.metric(label, value, help=…)` is a clean one-number readout; `AppTest` exposes it via `at.metric`.
- A one-off comparison table can honour the number-format convention (ADR-072) with an **inline
  `column_config`** (`NumberColumn(format=…)`) without adding the labels to the global `FORMATS` map.

---

# What Went Well ✅

- **Real data made the case** — an 8.1 xP spread across shapes (3-5-2 254.1 → 5-4-1 246.0) proved the score
  is decision-relevant, not decorative.
- **The perf trap was caught at planning** — the comparison is 7 ILP solves; because the expander runs
  collapsed, it was gated behind a default-off checkbox so the common Build render stays one solve.
- **No analytics drift** — reused `select_squad` + the build's `scores`/`display_xp`; the score is a sum,
  the comparison a loop; display-only.
- 617 → 619 tests; ruff + CI-parity green; seed.db clean.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A full comparison would slow every Build render | an expander body runs even when collapsed | Gate the 7 solves behind a default-off checkbox — cost only on request |
| What number to call "XI score" for non-xp objectives | the XI optimises the objective, not xP | Show the XI's projected **xP** (consistent with the per-row column + the reference-metric caption) |
| Formatting a one-off compare table | `XI xP`/`Δ` aren't in the global `FORMATS` | Inline `st.column_config.NumberColumn(format=…)` — honours ADR-072 without polluting `FORMATS` |
| An illegal shape within budget/options | not every formation is affordable | Show a blank in the compare table (as the single-shape preview already does) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Expander ≠ lazy | Its body runs collapsed; gate expensive work inside it (checkbox / lazy control) |
| Reuse the solve | The preview already solved the XI — the score was a free sum |
| Inline column_config | Format a one-off table's numbers without touching the shared `FORMATS` |
| Pick the interpretable metric | Show xP (the visible, comparable number) even when optimising another objective |

---

# Development Lessons 💻

- Check the render cost of a UI container before adding heavy work inside it.
- Prefer surfacing an existing computation over adding a new one.
- Ground a "is this worth building?" question in the real spread — 8 xP is a real formation decision.

---

# AI Collaboration Lessons 🤖

- The owner's "score + gated compare" choice was the right balance — it fully answers "see the effect of
  different formations" while keeping the default page fast; presenting the perf trade-off up front made
  that an informed call.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-075 | **The XI score in the formation preview** — show the selected shape's **Projected XI xP** (a sum of the previewed XI's xP; free) and, behind a **default-off "Compare all formations"** checkbox, a table ranking all 7 shapes by XI xP with Δ vs best (gated because the expander runs collapsed). Display-only; reuses `select_squad`/the build's scores; the saved build stays a full 15; no analytics change | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- If the comparison ever feels slow, cache it keyed on (objective, budget, include/exclude).
- Post-**GW1 (2026-08-21)**: the Data Hardening flip + xP calibration — the formation scores sharpen with
  real form.
- Possible: surface the *best* shape as a hint on the main build (e.g. "3-5-2 projects the most points").

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep pricing the render cost of Streamlit containers (expander/tabs run eagerly; segmented_control is lazy).

---

# Key Commands Learned

```text
python -m src.web_streamlit      # Squads → Build → "Preview the best XI" shows a Projected XI metric;
                                 #   tick "Compare all formations" for the ranked table
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Projected XI xP | The total projected points of a shape's best XI (display-only) |
| Gated compute | Expensive work put behind a control so it runs only when the user asks |
| Δ vs best | Each formation's XI xP minus the best formation's — the "cost" of a shape |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-075 | The XI-score decision + the expander-runs-collapsed perf rationale |
| `src/web_streamlit/views/squads.py` | `render_build` preview: the `st.metric` + `_formation_xi_scores` |

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

- US-230 The XI score — a "Projected XI — <shape>" metric in the Build formation preview (ADR-075)
- US-231 Compare all formations — a gated (default-off) table ranking all 7 shapes by XI xP with Δ vs best

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
