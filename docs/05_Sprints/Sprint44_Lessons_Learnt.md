# Lessons Learned

**Sprint:** Sprint 044 — XI vs bench xP breakout (a comparable squad build)

**Dates:** 2026-08-05

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Show a **Starting XI xP** vs **Bench xP** breakout in a full squad build (CLI + `ask`), auto-deriving the
best XI via `best_legal_xi` — so build iterations compare on the weekly-relevant number, not the
15-total that includes a non-scoring bench. Display-only; save untouched. No new dependency, no new ADR.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Showing the number that matters (XI xP) instead of a proxy (15-total).
- Verifying a coupling before decoupling (the save flow) to make "display-only" provable.
- Quieting an LLM hallucination by supplying the missing fact.

### New Skills Acquired

- An `xi_ids`-driven display split reused across two surfaces.
- Steering a narration task at a specific grounded fact.

---

# What Went Well ✅

- **Pure reuse, big value** — `best_legal_xi` + a render split; no new analytics; builds now compare, and
  it revealed differentials cost the *bench*, not the XI.
- **Display-only, verified** — the save flow reads `p["bench"]` and runs after render, so passing
  `xi_ids` (no mutation) leaves `--save` provably untouched.
- **A bonus bug-fix** — XI/bench points in the facts + a steered task fixed the recurring build-narration
  ⚠ (the LLM cites 233.6 / 72.2 with a ✓ instead of inventing a cost split).
- **Lean sizing** — a gate + two small stories, no ADR padding.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| The 15-total hides the comparison | It counts a bench that won't score | Break out Starting XI xP vs Bench xP |
| Auto-XI must not leak into save | `--save` reads `p["bench"]` | Pass `xi_ids` to the renderer; never mutate `p["bench"]` |
| Build narration invents a cost split | The fact the LLM wanted wasn't in the facts | Add XI/bench points + steer the task to state them |
| Auto vs declared bench | Two sources of the split | `xi_ids` wins when given; else the declared-bench flag |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Show the real number | The display is where comparison happens — surface XI xP, not the 15-total |
| Verify before decoupling | Reading the save flow made "display-only" a proof, not a hope |
| Supply the missing fact | To quiet a hallucination, give the LLM the number it will otherwise invent |
| Reuse over rebuild | `best_legal_xi` already existed; the feature was a render split |
| One param, two surfaces | `xi_ids` served the CLI and `ask` identically |

---

# Development Lessons 💻

- Put the decision-relevant number on screen; a proxy total invites confusion.
- Decouple by passing data, not mutating shared state — then save/display can't interfere.
- A narration guardrail is easier to satisfy by adding a fact than by tightening a rule.

---

# AI Collaboration Lessons 🤖

- The recurring build ⚠ wasn't a verifier flaw — it was a missing fact; adding it closed the loop.
- The grounding line kept steering the design: it told us exactly which number to ground.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| — | No new ADR — a display completion of the analyse XI/bench pattern (ADR-031) on the unified xP (ADR-041). `render_squad(xi_ids=…)`; auto-XI via `best_legal_xi`; display-only (save untouched); XI/bench xP in the `ask` facts | — |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

| Mistake | What I'll Do Differently Next Time |
|----------|------------------------------------|
| | |

---

# Things That Surprised Me 💡 _(for Tony)_

- How good is this now!

---

# Improvements for Next Sprint 🚀

## Project Improvements

- A **bench-aware optimiser** (maximise the XI with cheap fodder — the shown XI is best-of-the-built-15,
  not best-possible). A "compare two builds" command. More Phase 4 / the web UI / (GW1) the full xMins.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep supplying the fact the LLM would otherwise invent; keep the 3-part DoD.

---

# Key Commands Learned

```text
python app.py squad --full                        # shows Starting XI xP vs Bench xP (the comparison number)
python app.py squad --full --differential 5       # ...and the tilt cost lands on the bench, not the XI
python app.py ask "build me a squad for £100m"    # the breakout + a grounded narration of the XI's points
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| XI/bench breakout | Starting XI xP vs Bench xP — the weekly-relevant number vs the non-scoring bench |
| Auto-XI | The best legal XI derived from the built 15 for display, when no bench is declared |
| Display-only | Shown but not saved — passed to the renderer, never mutating the players |
| Supply the fact | Add the datum the LLM would otherwise fabricate, so the ✓ holds |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-041 / ADR-031 | `best_legal_xi` + the analyse XI/bench pattern this completes on screen |
| ADR-037 | The grounding verifier that flagged the invented cost split |
| ADR-013 | The declared-bench display this extends |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Showing the decision-relevant number | | |
| Decoupling via data, not mutation | | |
| Grounding by supplying facts | | |
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

- US-130 Gate — the XI/bench breakout design (no new ADR)
- US-131 CLI breakout — `render_squad` xi_ids split + subtotals
- US-132 `ask` breakout + grounded narration (fixed the build ⚠)

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
