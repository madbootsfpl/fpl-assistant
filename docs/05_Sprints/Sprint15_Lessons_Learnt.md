# Lessons Learned

**Sprint:** Sprint 015 — Evaluate soccerdata (a spike → decision)

**Dates:** 2026-08-03

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Decide — with evidence — whether to adopt `soccerdata`. Quantify name-matching and the
unique value (npXG), weigh them against the cost, and record the call in ADR-016. No
production dependency until decided.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Running a boxed evaluation spike in a throwaway venv (no impact on the app).
- Measuring, not guessing — match rate, npXG deltas, dependency footprint.
- Weighing decision-driving value vs nice-to-know against real cost.

### New Skills Acquired

- Fuzzy entity-matching across data sources (formal vs common names, team tiebreak).
- Recognising a season-alignment trap between two datasets.

### Areas Needing More Practice _(for Tony)_

---

# What Went Well ✅

- The spike said **no** with evidence — matching (~95%) and npXG were real, but narrow +
  costly, so defer was right.
- Tony's Haaland point (you own penalty-takers *because* of penalties) settled the value.
- Discipline held: nothing leaked into `src/`; the evaluation is reproducible.
- A subtle season-alignment trap was caught before it could mis-join data.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Names don't match cleanly | FPL full legal names vs Understat common names | Two layers: formal name + `web_name` (common), team tiebreak → ~95% |
| npXG looked like false matches | Wrong Understat season (2024/25 vs FPL 2025/26) | Aligned seasons; divergence vanished (Thiago 0.1 → 24.7) |
| Is the value worth it? | npXG is real but penalty-focused | For FPL, penalties score — so it's nice-to-know, not decision-driving |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Spike-before-adopt | A throwaway venv turns "should we?" into measured evidence |
| Entity matching | Match on the *common* name; keep team as a tiebreaker |
| Season alignment | Two datasets must cover the same season, or they silently mis-join |
| Cost of a dependency | Count it — 14 → 72 packages, incl. a browser/scientific stack |

---

# Development Lessons 💻

- Box evaluation code away from `src/`; keep the app clean until a decision is made.
- Sanity-check a cross-source join (do the shared fields agree?) to catch mis-alignment.
- A dependency's real cost is its transitive footprint, not just the one package.

---

# AI Collaboration Lessons 🤖

- Tony brought the idea (soccerdata) and made the product call; the spike supplied evidence.
- The rubric (matching / value / cost) kept the decision honest and structured.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-016 | **Defer** soccerdata — matching reliable (~95%) and npXG real but narrow; cost high (14 → 72 packages, scraping, season trap). Backlog it; proceed with the lighter FPL-native model | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Build the lighter FPL-native over/under-performance lens (expected vs actual attacking
  points) — no new dependency, decision-relevant.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the spike-before-adopt habit for future dependency questions.

---

# Key Commands Learned

```text
# (spike only — throwaway venv, not the app)
python3 -m venv sd_probe && ./sd_probe/bin/pip install soccerdata
./sd_probe/bin/python spikes/015-soccerdata/match_fpl_understat.py
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Spike | A boxed, time-limited investigation to answer a question before committing |
| npXG | Non-penalty expected goals — open-play threat, penalties excluded |
| Entity matching | Linking records for the same real thing across two datasets |
| Season alignment | Ensuring two datasets refer to the same season before joining |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-016 | Records the defer decision + the rubric verdicts |
| spikes/015-soccerdata/FINDINGS.md | The reproducible evidence behind the call |

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

- US-047 Name-matching prototype (~95%)
- US-048 npXG value + operational cost
- US-049 ADR-016 — Defer

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
