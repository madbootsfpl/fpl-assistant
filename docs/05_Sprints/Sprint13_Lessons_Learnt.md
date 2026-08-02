# Lessons Learned

**Sprint:** Sprint 013 — Flexible Formations

**Dates:** 2026-08-02

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Let `squad` pick the best legal formation (GK 1; DEF 3–5; MID 2–5; FWD 1–3; 11 total)
instead of a fixed 1-4-4-2, with an optional `--formation D-M-F` pin — and make the shape
visible, including the one the declared bench implies in `--full`.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Turning a fixed constraint into a range the solver optimises over.
- Keeping a change backward-compatible with a normalising default (`int → (n,n)`).
- Pushing policy (the flexible default) to the edge, leaving the core generic.

### New Skills Acquired

- Modelling variability as *data* (a range), not new code paths.
- Recognising two features are one idea in two views (bench ↔ formation).

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- A load-bearing constraint changed for almost nothing — ranges + one `size` line.
- Tony's "does the bench set the formation?" connected two features into one.
- The +19-pt value was measured before code (5-4-1 vs 4-4-2).
- Backward-compat was explicit; the 3-part DoD held (13th sprint).

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Ranges break the "exact count" assumption | The old loop used `== count` | Normalise: exact `int → (n,n)`; `lo==hi` stays `==` |
| A range formation's total is ambiguous | `3–5 + 2–5 + 1–3` isn't a single number | Require `size`; derive it only for all-exact shapes |
| The bench and the XI formation looked separate | Two commands, one concept | One `formation_str()` shows both; `--formation` is XI-only |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Ranges over equalities | Model a choice as `min ≤ Σ ≤ max`, let the solver decide |
| Normalising defaults | `int → (n,n)` keeps every exact caller unchanged |
| Policy at the edge | "Flexible is the default" is a CLI choice, not a solver change |
| Shared helpers | `formation_str` serves the XI display and the bench-implied display |

---

# Development Lessons 💻

- Make a risky change safe with a default that reproduces old behaviour (a regression anchor).
- A range without a total is ambiguous — fail loud (`ValueError`), don't guess.
- Answering "how do these interact?" can collapse two features into one.

---

# AI Collaboration Lessons 🤖

- Tony's interaction question reshaped the plan mid-flight — the bench-implied shape.
- The gate measured the +19 and the implied 4-4-2 on real data before any code.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-014 | Flexible formations: ranges + `size` in `select_squad` (exact ints unchanged); `XI_FLEX` default at the CLI; `--formation D-M-F` (XI-only); the bench implies the shape, shown via `formation_str` | Accepted |

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

- Validate a declared bench yields a *legal* XI (Sprint 013 shows the shape but doesn't
  police it); bench order; a saved/persistent squad; FBref xG/xA once feasible.
- Consider grouping the growing `squad` options.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep measuring value at planning; keep the gate + 3-part DoD.

---

# Key Commands Learned

```text
python app.py squad                 # best legal formation (was a fixed 1-4-4-2)
python app.py squad --formation 3-5-2   # pin the XI shape
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Formation | The DEF-MID-FWD shape of the starting XI (GK implied) |
| Range constraint | `min ≤ Σ ≤ max` — a choice the solver optimises over |
| Normalising default | Converting input to one form (`int → (n,n)`) so old callers still work |
| Policy at the edge | The CLI decides behaviour; the core stays generic |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-014 | Records ranges + `size`, the XI-only rule, and the bench↔formation link |
| Handbook Ch 22 | Optimisation, now with the flexible-formation section |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Constraints as ranges | | |
| Backward-compatible changes | | |
| Connecting features into one idea | | |
| Architecture | | |
| AI-assisted Development | | |

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?
This is a huge value add to creating the squad.

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?
maybe tackling the big backlog item - could add significant value

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-042 Flexible-formation design + ADR-014
- US-043 `squad --formation` + the flexible default

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
