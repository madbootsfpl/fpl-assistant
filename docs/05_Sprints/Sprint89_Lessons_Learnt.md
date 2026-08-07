# Lessons Learned

**Sprint:** Sprint 089 — A configurable prediction horizon on the Squads tab

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Let a manager choose how many gameweeks the tool predicts over — one dropdown on the Squads tab flowing
through Build · My Squad · Health · Transfer · AI Tips (Captain stays next-GW) — short for mid-season, long
for a wildcard/start.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Exposing an existing parameter as a control** — the analytics already took a horizon; the work was
  plumbing a user choice, not new maths.
- Threading a keyword through a layered call chain with a **safe default** so nothing else changes.

### New Skills Acquired

- A single UI control can drive multiple lazy sub-views by reading its value once and passing it into
  whichever view renders (segmented control = only the shown view runs).
- The `ask` layer can be made **per-call configurable** with a defaulted keyword (`horizon=_HORIZON`)
  threaded `answer → _fresh → _dispatch → _decide_* → _squad_xp` — reaching only the intent that needs it.
- A renderer label ("over 5 GW") should be **derived from the horizon**, not hard-coded, once the horizon
  is variable.

---

# What Went Well ✅

- **No analytics change, no surprise** — default 5 kept today's numbers; the feature is pure plumbing of a
  choice `decision_xp`/`analyse_squad` already accepted.
- **Honest per-view** — Captain (a one-week bet) is held at next-GW with a caption instead of a misleading
  multi-GW number.
- **Minimal ask-layer thread** — a defaulted `horizon` keyword reached only the gameweek decide; the CLI,
  the Ask tab, and transfer/analyse/start-bench are byte-identical (default `_HORIZON`).
- 625 → 627 tests; ruff + CI-parity green; seed.db clean.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A new page selectbox shifted widget indices | `at.selectbox[0/1]` positional refs | Re-point 5 tests to select **by label** (`s.label == …`) |
| AI Tips is behind `ask`, not a direct call | it routes through `ask.answer` (fixed 5-GW) | Add a backward-compatible `horizon` param threaded to the gameweek decide |
| A monkeypatched `_squad_xp` broke on the new kwarg | the test lambda had no `horizon` | Add `*, horizon=5` to the lambda signature |
| The "over 5 GW" plan label was hard-coded | it predated a variable horizon | Derive the window from `horizon` (or "next GW" for 1) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Expose, don't rebuild | A parameterised analytic becomes a feature by wiring a control to it |
| Default-safe threading | A defaulted keyword through a call chain adds a knob without changing callers |
| Label, not index | Any new page-level widget shifts positional test refs — assert by label |
| Derive labels | Once a value is variable, its display text must come from it, not a constant |

---

# Development Lessons 💻

- When adding a page-level control, expect positional widget tests to shift — prefer label-based assertions.
- Thread a new option with a safe default so existing behaviour (and every other caller) is unchanged.
- Keep a view honest about what a setting does (Captain = next-GW) rather than applying it everywhere.

---

# AI Collaboration Lessons 🤖

- The owner's "all sub-tabs incl. AI Tips" call was worth the small ask-layer thread — it delivered the
  "throughout the tab" the tester asked for, and the defaulted keyword kept it low-risk.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-077 | **A configurable prediction horizon on the Squads tab** — a shared "Gameweeks ahead" dropdown (1–8, default 5) driving Build · My Squad · Health · Transfer · AI Tips (Captain = next-GW); threaded via the existing horizon params + a backward-compatible `horizon` on `ask.answer` → `_decide_gameweek` → `_squad_xp`. Default 5 = unchanged; no analytics change; no server writes | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Post-**GW1 (2026-08-21)**: the Data Hardening flip + xP calibration — the horizon projections sharpen with
  real form.
- Possible: a horizon control on the **Ask tab / chat** too; a "best horizon" hint; the backlog's bench
  order / season-countdown / pronoun-aware chat.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Make every Squads-page widget assertion label-based so future page-level controls don't ripple into tests.

---

# Key Commands Learned

```text
python -m src.web_streamlit   # Squads → "Gameweeks ahead" drives Build/My Squad/Health/Transfer/AI Tips
python -m pytest tests/test_ask.py -q -k gameweek   # the ask-layer horizon threading
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Prediction horizon | How many upcoming gameweeks the projection sums over |
| Default-safe keyword | A new param with a default that leaves every existing caller unchanged |
| Next-GW decision | A choice (captaincy) that is inherently about the immediate gameweek only |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-077 | The horizon-selector decision + the "expose the existing param" rationale |
| `src/web_streamlit/pages/3_Squads.py` | The shared "Gameweeks ahead" control + dispatch |
| `src/ask.py` | `answer`/`_fresh`/`_dispatch`/`_decide_gameweek`/`_squad_xp` horizon thread |

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

- US-237 GW selector + analytic views — a shared "Gameweeks ahead" dropdown (1–8, default 5) through Build ·
  My Squad · Health · Transfer; Captain = next-GW (ADR-077)
- US-238 AI Tips respects the horizon — a backward-compatible `horizon` param through the ask layer; the
  gameweek plan labels "over N GW"

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
