# Lessons Learned

**Sprint:** Sprint 011 — The Full 15-Man Squad

**Dates:** 2026-08-02

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Extend the optimiser from "best starting XI" to the real FPL **15-man squad**
(2 GK / 5 DEF / 5 MID / 3 FWD, ≤ £100m, ≤ 3 per club), with the bench chosen by the
manager via `--include`.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Reusing a generic core (parameterised `formation` + `budget`) instead of writing new code.
- Adding capability at the edge (a CLI flag + a caller) and leaving the core untouched.
- Pressure-testing a design on real data *before* building it.

### New Skills Acquired

- Recognising when the *simplest* model + an existing mechanism beats a cleverer one.
- Putting an honest caveat into program output, not just documentation.

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- The 15-man squad needed **no optimiser change** — the generic core (Sprint 007) paid off.
- The gate proved the `--include`-the-bench workflow *and* surfaced the caveat before code.
- Tony's call to keep the model simple (reject two-tier) — "prefer simple" in action.
- The 3-part DoD held (11th sprint); the smoke test matched the gate to the pound.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Budget default differs by mode (80 XI / 100 full) | argparse can't tell "typed 80" from "default 80" | `--budget` defaults to None; a pure `resolve_squad_budget()` decides |
| `--full` alone spends up, no cheap bench | The model scores all 15 equally | Intended — manager picks the bench via `--include`; caveat + docs say so |
| The 15-total isn't a weekly score | The bench doesn't score | Recorded in ADR-012 **and** printed with the result |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Generic core | A parameterised function turns a "new feature" into a new *caller* |
| Sentinel defaults | A `None` default lets the handler pick a mode-dependent value |
| Honesty in output | A caveat that travels with the number can't be missed like a doc can |
| Rejected options | Recording *why* two-tier was rejected stops it being reopened by accident |

---

# Development Lessons 💻

- Reach for the existing seam (`formation`, `budget`, `--include`) before adding machinery.
- Extract a tiny pure helper (`resolve_squad_budget`) so a branch is testable without a DB.
- Keep the thin CLI free of FPL knowledge — the squad shape is an analytics constant.

---

# AI Collaboration Lessons 🤖

- Tony simplified the design mid-plan (reject two-tier); the plan was rewritten to match.
- The gate's worked example — run live — is what made the caveat visible before coding.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-012 | Simple full-squad model (`squad --full`, 2/5/5/3, £100m, ≤3/club); bench via `--include`; two-tier rejected; the 15-total is squad-strength, not a weekly score | Accepted |

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

- Flexible formations (the natural pair to this sprint), FBref xG/xA, or season-dependent
  FPL work once it starts.
- Consider visually separating the manager's bench in the `--full` output.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep pressure-testing ADR mechanisms on real data + the 3-part DoD.

---

# Key Commands Learned

```text
python app.py squad --full                          # best 15 for £100m (no cheap bench)
python app.py squad --full --include A B C:TEAM D    # lock a cheap bench; solver does the rest
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Full squad | The 15 you own (2/5/5/3), vs the starting XI |
| Caller | Code that invokes a generic function with specific arguments |
| Sentinel default | A placeholder default (None) resolved later by context |
| Squad strength | A total that counts the bench — a guide, not a weekly score |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-012 | Records the full-squad model + the rejected two-tier alternative |
| Handbook Ch 22 | Optimisation, now with the full-squad section |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Optimisation / constraints | | |
| Reusing a generic core | | |
| Simple-vs-clever design calls | | |
| Architecture | | |
| AI-assisted Development | | |

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?
i love th eflex in building the squad now. on reflection I think that rather than using include we should use bench and name you 1-4 players that you want in there, double * them and sort to the end of th elist, we can do this for a future sprint. managers may want 2-3 players that are always benched unless using a widlcard. this will add better/clearer visibility,

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-037 Full-squad design + ADR-012
- US-038 The `squad --full` command (15-man squad)

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
