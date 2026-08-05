# Lessons Learned

**Sprint:** Sprint 016 — Over/Under-performance (expected vs actual attacking points)

**Dates:** 2026-08-03

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Add an over/under-performance view — expected attacking points (from xG/xA) vs actual (from
goals/assists), minutes-gated — to spot finishing-hot regression risks and unlucky
bounce-back candidates. FPL-native, no new dependency (the lighter model chosen over
soccerdata in ADR-016).

---

# Knowledge Compounded 📈

## Skills Strengthened

- Adding a data dimension through the existing seams (model, migration, view) — again.
- Writing a pure analytics function that's testable without a database.
- Letting a verification habit *reshape* a design, not just check it.

### New Skills Acquired

- Building a metric that **compares** two stored quantities (expected vs actual).
- Designing a statistical guard (minutes gate) into a metric.

### Areas Needing More Practice _(for Tony)_

---

# What Went Well ✅

- The lighter FPL-native model (chosen over soccerdata) delivered — no dependency, real signal.
- First metric that *compares* rather than describes (regression / bounce-back).
- The "double-check" lesson caught the Meslier glitch → the minutes gate became core design.
- The migration seam upgraded the live DB a fourth time; the 3-part DoD held (16th sprint).

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A GK showed +66 over-performance | Preseason glitch (11 goals, 0 minutes) | Minutes gate (≥ 900) — part of the metric, not a patch |
| Number could be over-read | It's attacking-only | Caveat printed in the view (no clean sheets/bonus) |
| Un-refreshed rows (NULL fields) | Feature added after they were stored | Coerce None → 0; `minutes NULL` fails the gate → excluded |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Compare, don't just describe | Contrasting two stored metrics is a cheap new insight |
| Guard in the metric | A minutes gate makes a comparison statistically honest |
| Pure functions | `over_under()` is testable with no DB — like value/xp |
| Honesty in output | State the scope (attacking-only) so the number isn't over-read |

---

# Development Lessons 💻

- A verification step can improve a *design*, not just catch a bug (the minutes gate).
- Coerce missing values at the read site; let the gate exclude un-refreshed rows.
- Reuse the ingest → migrate → view seam; a new metric rarely needs new machinery.

---

# AI Collaboration Lessons 🤖

- The planning probe (run before code) shaped the metric — the Meslier find became the gate.
- Sprint 15's lesson ("double-check assumptions") directly improved Sprint 16.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-017 | Over/under = actual − expected attacking points (xG/xA vs goals/assists); minutes-gated (≥ 900); attacking-only; a two-ended `overperf` view | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- A total-points (not attacking-only) over/under; a clean-sheet / defensive lens (xGC);
  recent-form weighting (needs per-gameweek data).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep probing at planning — it catches glitches *and* improves designs.

---

# Key Commands Learned

```text
python app.py overperf                 # over- and under-performers (both ends)
python app.py overperf --pos FWD --min-minutes 1500
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Over/under-performance | Actual returns vs what the underlying numbers expected |
| Regression to the mean | A hot (or cold) run tending back toward the expected level |
| Minutes gate | A minimum-minutes filter so the sample is big enough to read |
| Attacking returns | Points from goals + assists (not clean sheets / appearance / bonus) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-017 | Records the formula, the minutes gate, and the attacking-only caveat |
| Handbook Ch 24 | Expected goals — now with the over/under-performance section |

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

- US-050 Over/under-performance design + ADR-017
- US-051 Ingest goals_scored / assists / minutes + migration
- US-052 The metric + the `overperf` view

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
