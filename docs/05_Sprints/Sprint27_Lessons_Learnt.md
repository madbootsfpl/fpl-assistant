# Lessons Learned

**Sprint:** Sprint 027 — Captain Suggestions (Phase 3 begins)

**Dates:** 2026-08-03

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

A `captain` command that recommends the top 3–5 captain picks for the next gameweek — ranked by the
enriched xP, filtered to available players, and *explained* (opponent, home/away, penalty duty).
Two modes: global, and `--squad <name>` (captain from your own saved squad). FPL-native; no new
dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Composing a feature from existing layers rather than writing new machinery.
- Turning a metric (xP) into a *recommendation* by adding policy + explanation.
- Reusing the shared renderer (ADR-025) for a brand-new view.

### New Skills Acquired

- Decision-appropriate policy on top of a shared metric (exclude GKs; keep-but-flag doubtful).
- A small predicate seam (`is_available`) to reshape a function's behaviour without duplicating it.

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- **The app crossed from *ranking* to *recommending*** — top picks with reasons (opponent, venue,
  penalty duty), not a bare list.
- **Mostly composition, not new code** — xP (ADR-028), availability (ADR-023), saved squads
  (ADR-024) and the shared renderer (ADR-025, its first *new* consumer) clicked together. Clean
  layers paid a dividend a whole phase later.
- **The probe drove two honest calls** — a GK ranking 3rd by mean xP → exclude GKs; and the
  discovery that `player_xp` zeroes doubtful players → an `is_available` seam so a doubtful premium
  is suggested-and-flagged, not dropped.
- **Reused, didn't reinvent** — captaincy ranks by xP + context, not a bespoke "captain rating";
  penalties are shown, not double-counted.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A goalkeeper ranked #3 by mean xP | xP is a mean; GKs have a high floor, no ceiling | Exclude GKs from captain candidates (policy at the edge) |
| Doubtful players were zeroed | `player_xp` treats only status 'a' as available | An `is_available` predicate seam; captain counts doubtful (flagged) |
| Risk of double-counting penalties | Penalty returns are already in xP | Show as context (`pen`), never add to the score |
| Couldn't demo the availability drop | Preseason — no injuries in the top ranks | Unit-tested the filter; noted the in-season case |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Recommend vs rank | A recommendation reuses a trusted metric and *explains itself* |
| Policy at the edge | Decision features need their own filters even on a shared metric |
| A predicate seam | Pass behaviour in (`is_available`) instead of duplicating a function |
| Compounding layers | A new phase's feature was mostly wiring existing pieces together |

---

# Development Lessons 💻

- Don't invent a new score when a validated one exists — extend it with context + policy.
- A tiny seam (a predicate parameter) beats copy-pasting a function to change one rule.
- Let the human decide: show the reasons (and the caveat) rather than an unexplained answer.

---

# AI Collaboration Lessons 🤖

- The gate (ADR-029) pressure-tested a real captain board first — which is what surfaced the GK and
  doubtful decisions before any code.
- Composition over invention kept the change small and the risk low.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-029 | Captain suggestions: rank by next-GW xP; **exclude GKs** (mean ≠ ceiling); keep doubtful players flagged; penalties as **context not a multiplier**; global + `--squad` modes; explain the pick | Accepted |

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

- The next Phase 3 feature (transfer suggestions / team analyser, composing xP + saved squads), or
  a ceiling/differential captain mode once variance data exists.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep the gate + 3-part DoD; probe on real data before designing; re-check ClubElo while down.

---

# Key Commands Learned

```text
python app.py captain                    # top-5 captain picks for the next GW (by xP)
python app.py captain --squad my-team    # captain from your saved squad (the real question)
python app.py captain --limit 3          # just the top 3
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Decision support | Features that *recommend* an action, not just rank data (Phase 3) |
| Recommend + explain | Give the pick *and* the reasons, so it can be trusted or overruled |
| Policy at the edge | Decision rules (exclude GKs, flag doubtful) live in the feature, not the metric |
| Mean vs ceiling | xP is an average; captaincy also cares about upside (a noted limitation) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-029 | The captain design + the two probe-driven policy calls |
| Handbook Ch 21 | Analytics — now with "from ranking to recommending" |
| ADR-025 / ADR-028 / ADR-024 / ADR-023 | The pieces captaincy composed |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Composing features from existing layers | | |
| Turning a metric into a recommendation | | |
| Decision-appropriate policy | | |
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

- US-080 Captain-suggestion design + ADR-029 (gate)
- US-081 Captain analytics + `captain` command (global)
- US-082 `captain --squad <name>` (from a saved squad)

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
