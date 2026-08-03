# Lessons Learned

**Sprint:** Sprint 022 — Player Availability (don't pick injured players)

**Dates:** 2026-08-03

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Make the tool honest about who can actually play — the optimiser skips unavailable players by
default (with an opt-out), doubtful players are flagged, and forcing in an unavailable player
warns — using FPL's `status` / `chance` / `news`.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Filtering an optimiser's input at the edge, keeping the core generic.
- Adding a data dimension through the existing seams (model, migration) — a fifth time.
- Chasing a surprising result to its cause before calling it a bug.

### New Skills Acquired

- Treating availability (reference data) as a selection *policy*, not solver logic.
- Warn-not-block for an override (forcing in an injured player).

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- Made the optimiser trustworthy — it was silently picking injured Garner as "optimal".
- Policy at the edge again; `select_squad` stayed a pure "maximise these scores" (5th feature).
- The double-check habit caught a non-bug (flexible formation, not a filter failure).
- Full-stack slice absorbed by the seams a fifth time; DoD held (22nd sprint).

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| The optimiser picked an injured player | It ignored availability | Filter unavailable (status i/s/u/n) at the CLI edge |
| A forced-in injured pick | The manager's explicit override | Keep it, but warn + flag `(inj)` |
| `--include-unavailable` didn't show Garner in the XI | Flexible XI prefers a better MID | Non-bug — demonstrated via `--full` |
| Doubtful players shouldn't be dropped | They might play | Keep them, flag `(d 75%)` |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Garbage in, garbage out | An "optimal" answer is only as good as its inputs |
| Policy at the edge | Availability filters at the CLI; the solver stays generic |
| Diagnose before fixing | A surprising result may be correct — find the cause |
| Keep + flag | Doubtful players stay in but are surfaced, not silently dropped |

---

# Development Lessons 💻

- Put the rule in a pure helper (`is_unavailable` / `available_players`) — testable, one place.
- Flag status inline where the user reads picks; report exclusions plainly.
- When a smoke result surprises you, reproduce it in isolation before changing code.

---

# AI Collaboration Lessons 🤖

- Tony's availability question turned a "saved squad" choice into a real correctness fix.
- The planning probe proved the gap (injured Garner picked) before any code.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-023 | Exclude unavailable (status i/s/u/n) from the squad by default (`--include-unavailable` opts in); keep + flag doubtful; warn on a forced-in injured pick; availability is a policy at the edge | Accepted |

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

- Availability flags in the other views (table/xg/…); a saved-squad availability reload;
  weighting by `chance` rather than a hard exclude.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep the gate + 3-part DoD; diagnose surprises before fixing.

---

# Key Commands Learned

```text
python app.py squad                       # available players only (default)
python app.py squad --include-unavailable  # consider injured/suspended too
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Availability | Whether a player can play next round (status / chance / news) |
| Doubtful (d) | Might play (25–75% chance) — kept, but flagged |
| Policy at the edge | The CLI decides behaviour; the solver stays generic |
| Warn, not block | Allow an override (forced-in injured) but flag it clearly |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-023 | Records the availability policy + warn-not-block |
| Handbook Ch 22 | Optimisation — now with the availability section |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Filtering optimiser inputs | | |
| Policy at the edge | | |
| Diagnosing before fixing | | |
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

- US-064 Player-availability design + ADR-023
- US-065 Ingest `chance` + `news` + migration
- US-066 The availability filter + flags

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
