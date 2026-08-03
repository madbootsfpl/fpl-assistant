# Lessons Learned

**Sprint:** Sprint 018 — Clean-Sheet / Defensive-Solidity Lens (xGC)

**Dates:** 2026-08-03

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Add a `cleansheet` view — rank DEF/GK by expected goals conceded per 90 (lowest = best
clean-sheet prospects), minutes-gated — completing the defensive picture alongside `defcon`.
Computed from data already stored; no ingest, no new dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Computing a metric from already-stored fields (no ingest) and verifying it vs the source.
- Choosing None-handling by the metric's direction (0 isn't always neutral).
- Reusing the pure-function + view pattern for a fast, testable feature.

### New Skills Acquired

- Recognising when a field banked earlier makes a later feature almost free.
- Pairing lenses (actions + solidity) to tell a fuller story.

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- `xgc` (banked Sprint 014) was spent now → the lightest feature sprint in a while.
- The defensive picture is complete: `defcon` (actions) + `cleansheet` (solidity).
- Compute-vs-ingest was decided by evidence (computed == FPL's per-90 field).
- The 0-means-best edge (skip missing xGC) was caught in the walkthrough, not in a bug.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Should we ingest xGC/90? | FPL provides it, but we store xGC + minutes | Verified `xgc × 90 / min` == FPL's field → compute, don't ingest |
| Missing xGC would rank as "best" | Here 0 = best (ascending) | Skip None `xgc`, don't coerce to 0 |
| Could be read as individual defending | xGC is team-level | State the team-signal caveat in the output |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Bank data early | A field stored before it's used makes a later feature almost free |
| Direction-aware defaults | The safe "missing" value depends on sort direction (0 ≠ neutral here) |
| Compute vs ingest | If a computed value matches the source exactly, compute (fewer fields) |
| Paired lenses | Attack/defence + actions/solidity tells a fuller story than one metric |

---

# Development Lessons 💻

- Verify a computed value against the source before deciding not to ingest it.
- Skip un-rankable rows rather than coercing them into a misleading rank.
- Reuse the pure-function + view shape; a sibling metric needs almost no new code.

---

# AI Collaboration Lessons 🤖

- Tony's DefCon thread led naturally to the clean-sheet companion.
- The walkthrough surfaced the 0-means-best edge before any code was written.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-019 | Clean-sheet lens: `xGC/90 = xgc × 90 / minutes` (computed, verified == FPL); DEF+GK, ascending, minutes-gated; a `cleansheet` view; team-signal caveat | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

| Mistake | What I'll Do Differently Next Time |
|----------|------------------------------------|
| | |

---

# Things That Surprised Me 💡 _(for Tony)_

-

---

# Improvements for Next Sprint 🚀

## Project Improvements

- A combined "defensive value" (DefCon + clean sheet) lens/objective; a clean-sheet
  *probability* model; a shared table renderer for the four ranking views.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep verifying computed values against the source before adding fields.

---

# Key Commands Learned

```text
python app.py cleansheet             # best clean-sheet prospects (DEF/GK by xGC/90)
python app.py cleansheet --pos GK
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| xGC | Expected goals conceded — a team defensive-solidity measure |
| Clean-sheet prospect | A DEF/GK whose team concedes few expected goals |
| Team signal | A stat that reflects the team, shown on each of its players |
| Direction-aware default | Picking the "missing value" to suit ascending vs descending |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-019 | Records the metric, the compute-vs-ingest call, and the team caveat |
| Handbook Ch 25 | Defensive Contribution — now with the clean-sheet section |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Computing metrics from stored data | | |
| Direction-aware None handling | | |
| Pairing complementary metrics | | |
| Architecture | | |
| AI-assisted Development | | |

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

- US-056 Clean-sheet lens design + ADR-019
- US-057 The metric + the `cleansheet` view

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
