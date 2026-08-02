# Lessons Learned

**Sprint:** Sprint 007 — Optimal Squad Selector

**Dates:** 2026-08-02

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Pick the optimal starting XI — the 11 players that maximise last-season points within a
budget, a fixed formation, and the max-3-per-club rule — and display it.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Composing a command over a tested analytics function.
- Pressure-testing a design (worked example) before building.
- Keeping a dependency sealed inside one module.

### New Skills Acquired

- **Linear/integer programming** — describe an objective + constraints, let a solver find the best.
- Using PuLP (and the CBC solver) for an optimisation.
- Handling a "black box" solver honestly (status checks, tests on known answers).

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- The app crossed from *analysis* to a *decision* — `squad` recommends, not just ranks.
- The gate story earned its name: the formulation was pressure-tested before code.
- A new *kind* of code (declarative optimisation) landed cleanly in one module.
- The dependency (PuLP) stayed sealed; the rest of the codebase was untouched.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Greedy ≠ optimal | Budget couples the choices | Integer programming (evaluates combinations) |
| PuLP 4.0 deprecation warnings | Current PuLP 3.x API | Scope-suppressed + backlog item to migrate |
| Infeasible budgets | Too low to field a legal XI | Return the solver status; friendly message, no crash |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Optimisation mindset | Describe the *rules*, not the *search* |
| ILP | Binary pick per player; maximise points under linear constraints |
| Trusting a solver | Pin it with tests on small, known-answer cases |
| Dependencies | Seal an external library inside one module |

---

# Development Lessons 💻

- Pressure-test an ADR's mechanism with a worked example — it prevents flaws in code.
- A one-line constraint (`≤ 3 per club`) can change the whole answer.
- Handle third-party warnings deliberately (suppress with a reason + a backlog item).

---

# AI Collaboration Lessons 🤖

- The gate story's worked example (from a prior lesson) meant the design was verified
  before any code — the check-first discipline paying off.
- Framing the optimiser as "describe rules, solver searches" kept the focus on the idea.

### Notes _(for Tony)_

- Output is great, really like it and it gives different results for different budgets as expected.
- I think th enext logical extention of this feature is to have th echoice to include or exclude up to say 4 players, this will allow the user then to essentually choose 4 favorite players or exclue 4 that they dont like and have th etool then create a team around that.

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-008 | Optimal XI via ILP (PuLP); objective = last-season points; budget £80M / 1-4-4-2 / ≤3-per-club | Accepted |

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

- 15-man squad, flexible formations, or an xP-based objective (backlog).
- Revisit data-dependent work once the season starts.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep pressure-testing ADR mechanisms + the 3-part DoD.

---

# Key Commands Learned

```text
python app.py squad --budget 80     # optimal starting XI within a budget
python app.py squad --budget 40     # too low → clear "no legal XI" message
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Optimisation | Finding the best option out of many, subject to rules |
| Linear/Integer Programming | Maximise an objective under linear constraints (integers) |
| Objective | The thing being maximised (here, total points) |
| Constraint | A rule the answer must obey (budget, formation, club cap) |
| Infeasible | No answer satisfies the constraints |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-008 | Records the ILP formulation + worked example |
| Handbook Ch 22 | Explains optimisation / linear programming |
| PuLP | The integer-programming solver library |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Optimisation / linear programming | | |
| Using a third-party library | | |
| Reviewing decisions critically | | |
| Architecture | | |
| AI-assisted Development | | |

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?
Really like how this is shaping up

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-024 Squad selector design + ADR-008
- US-025 The optimiser (PuLP ILP)
- US-026 The `squad` command

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is to record what *you learned* while building it.
