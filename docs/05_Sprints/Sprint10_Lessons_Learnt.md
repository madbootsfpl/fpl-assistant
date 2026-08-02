# Lessons Learned

**Sprint:** Sprint 010 — Squad Objective Toggle

**Dates:** 2026-08-02

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Let the squad optimiser maximise the metric the user chooses — points (default), value
(points-per-£m), or expected points (xP) — turning "best historical squad" into "best
squad for *this* goal".

---

# Knowledge Compounded 📈

## Skills Strengthened

- Making a component generic (maximise any score) and pushing meaning to the edge.
- Reusing built analytics (value, xP) as inputs to another feature.
- Keeping a change backward-compatible with a no-op default.

### New Skills Acquired

- Parameterising an optimisation objective.
- Composing independent, tested features (objective + include/exclude + budget).

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- The whole toolkit converged — value and xP now feed the optimiser.
- The generic-core / decide-at-the-edge pattern recurred and paid off again.
- It composes — objective + include/exclude + budget all work together.
- The gate ADR was pressure-tested; the 3-part DoD held.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Value divide-by-zero | Price 0 | `points_per_million` → None → coerced to 0 |
| xP needs to map back to a player | `player_xp` didn't return an id | Added `id` to the xP result |
| Risk of changing today's behaviour | New objective param | `scores=None` → points (a regression test pins it) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Generic core | An optimiser can maximise "any score" and not know what it means |
| No-op default | A default that reproduces current behaviour makes an extension safe |
| Composability | Independent, tested pieces combine without extra work |
| Reuse | value/xP became the optimiser's objective, not recomputed |

---

# Development Lessons 💻

- Keep the core generic; push the meaning (the objective) to the edge.
- Prove a default is a no-op with a regression test.
- Fetch only what an option needs (fixtures only for the xp objective).

---

# AI Collaboration Lessons 🤖

- Reviewing the backlog together led to the highest-leverage pick ("tie it together").
- The gate's worked example verified the toggle changes the pick before code.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-011 | Pluggable squad objective (points/value/xp); generic optimiser maximises a score; elo excluded (team-level) | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

| Mistake | What I'll Do Differently Next Time |
|----------|------------------------------------|
| | |

---

# Things That Surprised Me 💡 _(for Tony)_

- how good the xp was, brilliant to compare against points and value


---

# Improvements for Next Sprint 🚀

## Project Improvements

- FBref xG/xA, 15-man squad / formations, or `--type`/`--next` for the xp objective.
- Revisit data-dependent FPL work once the season starts.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep pressure-testing ADR mechanisms + the 3-part DoD.

---

# Key Commands Learned

```text
python app.py squad --objective value              # most points-per-£m XI
python app.py squad --objective xp --include Haaland  # best expected XI around a pick
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Objective | The quantity an optimiser maximises |
| Pluggable | Swappable without changing the core |
| No-op default | A default that leaves current behaviour unchanged |
| Composability | Features that combine cleanly |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-011 | Records the objective-toggle design |
| Handbook Ch 22 | Optimisation, now with the pluggable-objective section |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Optimisation / objectives | | |
| Reusing / composing features | | |
| Reviewing decisions critically | | |
| Architecture | | |
| AI-assisted Development | | |

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?
getting through the backlog

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-034 Objective-toggle design + ADR-011
- US-035 Generic optimiser + objective_scores
- US-036 The `squad --objective` command

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is to record what *you learned* while building it.
