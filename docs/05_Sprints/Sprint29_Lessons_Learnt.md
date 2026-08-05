# Lessons Learned

**Sprint:** Sprint 029 — Team Analyser (Phase 3 decision-support capstone)

**Dates:** 2026-08-04

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

An `analyse --squad <name>` command that grades a saved squad's health over the next N gameweeks —
projected XI xP, the XI and bench with per-player xP + availability, and highlights (issues, weak
links → transfer hints, club concentration). Composes the existing pieces; shows indicators, not a
fake grade. FPL-native; no new dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Composing a feature almost entirely from existing, tested layers.
- Reusing the optimiser (`select_squad`) for a sub-problem (pick the best XI from 15).
- Designing an *overview* that cross-links point-features into a workflow.

### New Skills Acquired

- A pure "summarise state → indicators" analytics fn.
- Choosing honest indicators over a false-precision score.

### Areas Needing More Practice _(for Tony)_

---

# What Went Well ✅

- **Almost pure composition** — the analyser added ~no new computation; it aggregates xP,
  availability, the optimiser's XI pick, and the club rule into one health check.
- **Reused the optimiser for the XI pick** — the no-declared-bench fallback is `select_squad` over
  the owned 15, proven on TS to return the same XI/bench the manager declared.
- **Indicators over a grade** — projected XI xP, # issues, weak links; concrete and honest.
- **The trio became a workflow** — weak link → `transfer`, top XI → `captain`.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Which 11 start (no declared bench)? | Saved squad may lack `bench_ids` | Best legal XI via `select_squad` (reuse); proven identical on TS |
| "Health grade" risks false precision | A letter/number implies more than we know | Show indicators (projected xP, # issues, weak links), not a grade |
| Bench xP could be read as "projected" | The bench doesn't score | Projected = XI only; bench shown separately |
| Preseason hides availability value | No injuries yet | Unit-tested the issue flag; matters in-season |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Composability | Clean one-way-flow layers make new features mostly wiring — the whole of Phase 3 |
| Reuse the tool you own | The optimiser picked the XI; no new selection code |
| Indicators vs grades | Concrete numbers a manager can read beat an invented score |
| Cross-linking | An overview that points at the point-features turns silos into a workflow |

---

# Development Lessons 💻

- Aggregation features still deserve a *pure* core (state in → indicators out) for testability.
- Prefer pointing the user at an existing command over re-implementing its logic inline.
- Be honest about what a summary is (indicators), not what it isn't (a verdict).

---

# AI Collaboration Lessons 🤖

- The gate probe validated both the numbers *and* the fallback path before code, so "build" was low-risk.
- Composition kept the diff small: one pure fn + one view + one command on proven pieces.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-031 | Team Analyser: a saved squad's health check over a horizon; indicators not a grade; projected = XI only; XI = declared bench else best-XI via `select_squad`; cross-links to captain/transfer; manager-ID fetch + numeric score deferred | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Sprint 030 — Data Hardening (the last of the three): a full 567-player history backfill, and —
  once GW1 plays — per-GW `history` + in-season xP blending. Then xMins can retire bench-blindness.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the gate + 3-part DoD; probe on a real squad before designing; re-check ClubElo while down.

---

# Key Commands Learned

```text
python app.py analyse --squad TS            # squad health over the next 5 GW (XI xP + highlights)
python app.py analyse --squad TS --next 3    # over a 3-GW horizon
# the trio, as a workflow:
#   analyse --squad TS  ->  transfer --squad TS  ->  captain --squad TS
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Health check | An overview of a squad's projected points + problems (not a verdict) |
| Projected XI xP | The starting XI's expected points over the horizon (bench excluded) |
| Best-XI fallback | Picking the legal XI from 15 via the optimiser when no bench is declared |
| Cross-link | Pointing the user from one tool to the next (analyse → transfer → captain) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-031 | The analyser design + the two probe validations |
| Handbook Ch 21 | Analytics — now with "a summary that composes + cross-links" |
| ADR-008 / ADR-024 / ADR-028 | The optimiser, saved squads, and xP the analyser composed |

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

- US-086 Team-analyser design + ADR-031 (gate)
- US-087 `analyse_squad` engine (pure, unit-tested)
- US-088 `analyse` command + summary view

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
