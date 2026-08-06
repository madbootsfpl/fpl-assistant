# Lessons Learned

**Sprint:** Sprint 079 — A Help tab (build your team with the assistant)

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Add a **Help** tab: a step-by-step guide a new user follows to build and manage their team with the
assistant — static, clear, and complementary to Home.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Writing onboarding as a **recipe** (ordered steps + concrete examples) rather than a feature list.
- Adding a page with zero churn (placed last, so no renumber) and a light content test.

### New Skills Acquired

- A static Streamlit page (markdown + `st.expander`) with **no data dependency** renders before any
  `refresh` — ideal for a guide — and having **no input widgets** keeps it outside the tooltip-coverage test.

---

# What Went Well ✅

- **Static recipe** — robust (renders anytime), test-friendly (a key-content assertion), easy to keep
  accurate.
- **Zero churn** — placed last (`12_Help.py`); no other page files moved.
- **Complements, not duplicates** — Home keeps the one-screen overview and now points to Help.
- **Concrete** — copy-paste `ask` examples turn the guide into something a user can act on immediately.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A guide can drift from the app | it describes tabs / `ask` intents | Write it as a recipe (tabs + examples); a key-content test flags if core steps vanish; re-read on renames |
| Where to place it | sidebar order is filename-coupled | Last (`12_`) — zero renumber; Home points to it |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Static content pages | No data dependency → renders before refresh; no inputs → outside the tooltip test |
| Content tests | Assert the key steps + an example exist (presence), not exact prose (which reviews cover) |
| Placement vs churn | Appending at the end avoids the cascade a mid-list insert causes |

---

# Development Lessons 💻

- Onboarding is a recipe: ordered steps, each pointing at the tab that does it, with a runnable example.
- Keep guide pages static + dependency-free so they never break the app.

---

# AI Collaboration Lessons 🤖

- The owner's "step-by-step recommendations to build their unique team with AI help" mapped cleanly to a
  build → tweak → decide → ask → save recipe; the `ask` examples are the AI-help centrepiece.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-068 | **A Help guide tab** — a static, step-by-step Help page (`pages/12_Help.py`, placed last): expander steps (build → make it yours → check → improve → research → ask → save) + copy-paste `ask` examples + tab pointers; complements Home (which gains a pointer); no analytics/data dependency, no input controls; a render + key-content test | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- If the app changes a lot, re-read the Help steps for accuracy. Open items: pronoun-aware chat; small
  decision-support gaps (bench order, availability flags in the ranking views); and — post-GW1
  (2026-08-21) — the Data Hardening flip + calibration and the crowd/form-vs-xP backtest.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep guides static + example-driven; keep new pages at the end to avoid renumber churn.

---

# Key Commands Learned

```text
python -m src.web_streamlit          # the Help tab is at the bottom of the sidebar
python -m pytest tests/test_web_streamlit.py -k help -q   # the render + key-content test
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Recipe (vs spec) | Onboarding written as ordered, actionable steps rather than an exhaustive feature list |
| Static page | A content-only Streamlit page with no data/analytics dependency (renders anytime) |
| Key-content test | Asserts the essential steps/examples are present, without pinning exact wording |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-068 | The Help-page decision (static, placed last, complements Home) |
| `src/web_streamlit/pages/12_Help.py` | The step-by-step guide |

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

- US-215 A Help tab — a static, 7-step guide (build → make it yours → check → improve → research → ask →
  save) with copy-paste `ask` examples; a Home pointer

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
