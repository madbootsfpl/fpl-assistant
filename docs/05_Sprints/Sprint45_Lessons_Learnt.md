# Lessons Learned

**Sprint:** Sprint 045 — Bench-aware squad optimisation (weekly XI vs Bench Boost)

**Dates:** 2026-08-05

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Make the squad optimiser build the team you'll actually field: `--weekly` maximises the starting XI with
a cheap-but-playing bench (rotation cover); `--bench-boost` keeps the max-15 for the chip. A `start`-
variable ILP + a weighted objective; opt-in modes (the transfer-consistent max-15 default stays). No new
dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Sweeping a parameter to find its knee instead of guessing.
- Adding decision variables (`start`) + a weighted objective to an ILP.
- Preserving an invariant by making the riskier option opt-in.

### New Skills Acquired

- A starting-XI-aware squad objective (`Σ xp·start + w·xp·bench`).
- Diagnosing keyword-routing precedence collisions.

---

# What Went Well ✅

- **The probe carried the design** — the weight sweep pinned `0.1` (the XI/rotation knee) and the
  composition test proved it stacks on the archetypes before code.
- **Opt-in kept the guardrail** — max-15 stays the default, so `transfer` stays consistent (no free
  transfers); bench-aware is a mode.
- **Two smoke catches** — the `--bench-boost` arbitrary XI (223.2 vs 233.6) and the "bench boost" →
  start_bench mis-route only showed when run for real; both had clean fixes.
- **The ILP designs the XI** — a stronger team than a post-hoc split, and an exact breakout.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Which bench weight? | 0 = dead bench; 1 = max-15 | Sweep → 0.1 (strong XI + a playing bench) |
| `--bench-boost` showed an arbitrary XI | Weight 1.0 doesn't care which 11 "start" | Make it the default max-15 + an "all 15 score" note |
| "bench boost" mis-routed | `start_bench`'s "bench" keyword matched first | Move `build_squad` before `start_bench` in routing |
| `--weekly` bench invites transfer upgrades | The bench is cheap fodder by design | Keep the default (max-15) consistent; `--weekly` opt-in |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Find the knee | Sweep a parameter across its range; the value that matters reveals itself (0.1) |
| Opt-in preserves invariants | Make the more-correct-but-riskier build a mode, not the default |
| ILP decision vars | A `start[i]` binary + a weighted objective lets the solver *design* the XI |
| Run it for real | The arbitrary XI and the mis-route were invisible to the unit tests |
| Routing precedence | Keyword order matters as intents grow — a collision is a design smell |

---

# Development Lessons 💻

- Prototype the objective and sweep the weight before wiring — the numbers pick the default.
- When a flag's "obvious" value is subtly wrong (weight 1.0), reach for the simpler correct thing.
- Smoke every new phrasing — routing bugs hide behind plausible defaults.

---

# AI Collaboration Lessons 🤖

- The gate probe pinned both the weight and the composition, so the build was mechanical.
- Two real-run catches (arbitrary XI, mis-route) reinforced that the smoke step is not optional.

### Notes _(for Tony)_

- Weekly & bench-boost work incredibly well

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-045 | Bench-aware optimisation: `select_squad(bench_weight=W)` (a `start`-variable ILP; `Σ xp·start + W·xp·bench`); `--weekly` (0.1) / `--bench-boost` (the max-15 + a note); the default is unchanged (transfer-consistent); `ask` picks the mode; None → byte-identical | Accepted |

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

- An **XI-aware `transfer`** (so a weekly squad's cheap bench isn't "upgraded"); chip-timing advice; an
  intent classifier as routing grows. (GW1) the full Phase-5 xMins. Or the web UI.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep sweeping parameters; keep smoking every new phrasing; keep the 3-part DoD.

---

# Key Commands Learned

```text
python app.py squad --full --weekly               # a strong XI + a cheap playing bench (rotation)
python app.py squad --full --bench-boost          # maximise all 15 (the chip week)
python app.py ask "build me a squad for rotation" # ...same, in plain English
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Bench-aware | Optimise the starting XI (weighting the bench low), not the 15-total |
| bench_weight | How much a bench player's score counts vs a starter's (0.1 weekly, 1 = max-15) |
| The knee | The parameter value where a metric's trade-off turns (0.1 here) |
| Bench Boost | The chip week where all 15 score → the max-15 build |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-045 | The bench-aware objective + the modes |
| ADR-041 / ADR-008 | The squad optimiser + the xP metric this extends |
| ADR-044 | The archetype constraints it composes with |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Parameter sweeps | | |
| ILP decision variables | | |
| Preserving invariants (opt-in) | | |
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

- US-133 Gate — ADR-045 (the bench-aware design; weight pinned; default kept)
- US-134 Bench-aware `select_squad` + `--weekly`/`--bench-boost`
- US-135 `ask` modes + a routing fix

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
