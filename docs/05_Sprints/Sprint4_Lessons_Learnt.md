# Lessons Learned

**Sprint:** Sprint 004 — Custom Fixture Difficulty (Overall)

**Dates:** 2026-08-02

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Compute the app's *own* fixture difficulty from team overall strengths (home/away
aware), alongside FPL's version — so we control and can explain the rating, and have
the groundwork to extend to Attack/Defence later.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Extending an entity through every layer (model → table → analytics → CLI).
- Reusing a seam (`source`) rather than rewriting logic.
- Grounding a plan in real data before committing to it.

### New Skills Acquired

- **Schema migration**: adding columns to a table that already has data
  (`PRAGMA table_info` + `ALTER TABLE ADD COLUMN`).
- Giving one metric multiple **sources** behind a single parameter.
- Descoping a sprint honestly when the data doesn't support the plan.

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- A planning-time data check caught a blocker (zero strengths) before any code.
- The 3-part DoD (tests → smoke test → docs) held for every story.
- The `source` seam from US-015 made US-016 nearly free.
- The migration worked first time on the real database, no data lost.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Attack/Defence strengths all zero | Preseason — FPL hasn't published them yet | Descoped to overall FDR; deferred the split (ADR-005 + memory note) |
| Adding columns to an existing table | `CREATE TABLE IF NOT EXISTS` won't alter it | Light migration: `PRAGMA table_info` + `ALTER TABLE ADD COLUMN` |
| Custom difficulty easy to get backwards | Perspective (opponent's strength at their venue) | Pinned by a test (ARS↔BUR) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Schema migration | `CREATE` makes a new schema; a migration brings an existing DB up to it |
| Seams | A parameter in the right place (`source`) serves several consumers |
| Grounding | Verify a feature's data exists *before* planning around it |
| Descoping | Shipping the honest, smaller thing beats forcing the planned one |

---

# Development Lessons 💻

- Check the data a feature depends on at plan time, not just at execution.
- A forcing-function DoD (tests + smoke + docs) closes gaps a single check misses.
- Reuse over rebuild: extend a signature before writing new logic.

---

# AI Collaboration Lessons 🤖

- The most valuable moment was the *planning* data check — catching the blocker
  early saved building something broken.
- Framing each story around its place in the architecture kept the focus on
  *how it fits*, matching the learning goal.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-005 | Custom overall FDR (opponent strength, home/away); `fdr --type`; light migration; Attack/Defence deferred | Accepted |

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

- Revisit Attack/Defence FDR once strengths populate, or begin the xP engine.
- Add a data-availability check to sprint planning.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep the 3-part DoD (tests + smoke test + docs check).

---

# Key Commands Learned

```text
python app.py fdr --type custom --next 5          # our own difficulty vs FPL's
python app.py fixtures --team ARS --type custom   # per-match custom difficulty

# schema migration pattern
PRAGMA table_info(teams);                         # inspect current columns
ALTER TABLE teams ADD COLUMN strength_overall_home INTEGER;
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Migration | Bringing an existing database up to a new schema (e.g. ALTER TABLE) |
| Seam | A well-placed extension point (here, the `source` parameter) |
| Descope | Deliberately narrowing a plan to what's feasible/valuable now |
| Home/away strength | A team's overall rating split by where they play |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-005 | Records the custom-FDR decisions and the deferral |
| memory: fpl-preseason-strength-data | The preseason data constraint, for future reference |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| SQL / schema changes | 1|2 |
| Migrations | 1|2 |
| Analytics (metrics/sources) | 2|4 |
| Reading/using real data |1 |3 |
| Architecture |2 |3 |
| AI-assisted Development |2 |4 |

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with? 
Seeing feature grwoth & understanding same

### What was the biggest lesson?
check assumptions before we build

### What challenged me the most?

### What am I looking forward to building next?
next sprint

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-013 Custom FDR design + ADR-005 (descoped to overall)
- US-014 Store team strengths (with a migration)
- US-015 Custom FDR + `fdr --type`
- US-016 Per-match custom difficulty in `fixtures --type`

**Stories Carried Forward:**

- None (Attack/Defence split deferred to a future sprint — data-dependent)

**Overall Satisfaction (1–10):** __8_ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is to record what *you learned* while building it.
