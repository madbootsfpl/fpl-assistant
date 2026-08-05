# Lessons Learned

**Sprint:** Sprint 042 — Squad archetypes (build with low-cost + premium constraints)

**Dates:** 2026-08-05

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Let the manager *shape* a squad build — "give me ≥3 cheap enablers and ≥1 premium" — via min-count
price-band constraints in the ILP, exposed as `squad --full --cheap N --premium M` and parsed from a
natural-language build request. Define the **differential** and defer it (needs ownership data). No new
dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Turning a request into the smallest general primitive (a price-band count).
- Adding a constraint to an ILP (PuLP) without disturbing the objective.
- Scoping honestly: ship the buildable part, defer the data-blocked part.

### New Skills Acquired

- Min-count band constraints on a squad optimiser.
- Parsing archetype counts ("3 low cost … 1 premium") from a build request.

### Areas Needing More Practice _(for Tony)_

---

# What Went Well ✅

- **A real feature from one sentence** — "3 low cost + 1 premium" became a clean, general
  `band_minimums` addition powering both the CLI and the NL build.
- **Infeasibility came for free** — the ILP status already flags "no solution", so an over-constrained
  ask gives a friendly message with no special-casing.
- **Byte-identical without bands** — the optional param leaves every existing path untouched.
- **Honest differential scoping** — defined it by ownership (not a price proxy) and deferred the build.
- **The grounding guardrail proved itself live** — the build narration invented cost figures; the ✓/⚠
  line ⚠-flagged them.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| "shape the squad" as a feature | The optimiser had no notion of archetypes | A general `band_minimums=[(count, lo, hi)]` ILP constraint |
| Over-constrained asks | Too many premiums for the budget/pool | The ILP returns non-Optimal → a clear message (no special-casing) |
| Differentials need data we lack | `selected_by_percent` isn't ingested | Define it (ownership), defer the build, a "coming soon" note |
| Build narration invents numbers | The LLM extrapolated cost breakdowns | The ✓/⚠ verifier flags them (working as designed); a prompt polish later |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Smallest general primitive | A price-band count powers CLI + NL; don't build a bespoke feature |
| Let the solver carry the error | The ILP status is the feasibility check — don't reinvent it |
| Optional = safe | A default-None param keeps every existing path byte-identical |
| Honest scoping | Define the hard part (differential = ownership), ship the easy part, defer cleanly |
| Guardrails earn their keep | The grounding verifier caught a real LLM fabrication in the wild |

---

# Development Lessons 💻

- Model a feature as a constraint on an existing optimiser, not a new code path.
- Reuse the solver's status for error messaging — it's already exact.
- Refuse a misleading proxy (price ≠ ownership); a clean "coming soon" beats a wrong answer.

---

# AI Collaboration Lessons 🤖

- The gate probe pinned the thresholds *and* the ILP insertion point before code — the build was
  mechanical.
- The verifier flagged the build narration's invented figures — proof the "analytics decide, LLM
  narrates, verify it" loop holds even as intents grow.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-043 | Squad archetypes: min-count price-band constraints in `select_squad` (`band_minimums`); low-cost ≤£4.5m, premium ≥£9.0m (tunable); CLI `--cheap`/`--premium` + NL parse in `build_squad`; infeasible → a clear message; **differential defined + deferred** (needs ownership) | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- The **differential** (ingest `selected_by_percent`, then a band/predicate + a parsed count). A prompt
  polish to reduce build-narration ⚠. Per-position archetypes ("a premium forward"). (GW1) the full
  Phase-5 xMins. Or the web UI.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the gate probe broad (pin thresholds + the insertion point on real code); keep the 3-part DoD.

---

# Key Commands Learned

```text
python app.py squad --full --cheap 3 --premium 1                                  # shape it: ≥3 ≤£4.5m + ≥1 ≥£9m
python app.py ask "build me a squad for £100m with 3 low cost players and 1 premium player"
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Archetype | A squad role by price: low-cost enabler / premium (differential = ownership, later) |
| band_minimums | ILP constraint: ≥N picked players priced within a band |
| Enabler | A cheap (≤£4.5m) player, usually bench/chip fodder, that frees budget |
| Infeasible | The ILP has no solution under the constraints → a clear message |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-043 | The archetype design + the differential definition/deferral |
| ADR-008 / ADR-012 | The squad optimiser this constrains |
| Backlog → Differential archetype | The ownership-ingest follow-up |

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

- US-124 Gate — ADR-043 (squad archetypes; differential defined + deferred)
- US-125 `select_squad` band constraints + `--cheap`/`--premium`
- US-126 NL parse in `build_squad` + the differential "coming soon" note

**Stories Carried Forward:**

- None (the differential *build* is a Backlog follow-up — needs an ownership ingest)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
