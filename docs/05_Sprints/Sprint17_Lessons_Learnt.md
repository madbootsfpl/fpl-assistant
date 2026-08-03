# Lessons Learned

**Sprint:** Sprint 017 — Defensive Contribution (DefCon reliability)

**Dates:** 2026-08-03

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Add a `defcon` view — rank players by how comfortably they clear their position's Defensive
Contribution threshold (`per-90 − threshold`), minutes-gated — to find reliable DefCon-point
earners. A defensive counterpart to `overperf`; FPL-native, no new dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Adding a data dimension through the existing seams (model, migration, view) — a fifth time.
- Verifying what a third-party field *means* before building a metric on it.
- Reusing a proven pattern (`overperf`'s gate + view) to ship a sibling feature fast.

### New Skills Acquired

- Using a threshold as the reference point for a margin (a stand-in for "expected").
- Excluding a position class cleanly (GK via `THRESHOLD.get`).

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- Came straight from Tony's "no forwards in the value top-20" observation.
- The position-correctness of FPL's field was *verified* — the key assumption held.
- A matched pair of lenses now exists: `overperf` (attack) + `defcon` (defence).
- The migration seam absorbed a new dimension a fifth time; DoD held (17th sprint).

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Is a threshold comparison valid? | The field could count all actions regardless of position | Verified: DEF = CBIT, MID/FWD = CBIT + recoveries — position-correct |
| No "expected DefCon" to compare to | It's not an xG-style stat | Use the per-match threshold as the reference → a margin |
| GK have no DefCon | Not eligible | Excluded via `THRESHOLD.get` returning None |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Verify field meaning | Confirm what a third-party number represents before using it |
| Reference points | A threshold can play the role "expected" plays for xG |
| Pattern reuse | `overperf`'s gate + view shape shipped `defcon` quickly |
| Clean exclusion | A missing dict key (`.get` → None) is a tidy "not eligible" |

---

# Development Lessons 💻

- Prove the load-bearing assumption in the gate (position-correctness) before code.
- Reuse the ingest → migrate → view seam; a sibling metric needs almost no new machinery.
- State the honest limit in the output (reliability, not guaranteed points).

---

# AI Collaboration Lessons 🤖

- Tony's observation set the direction; the planning probe validated the field.
- The "double-check" habit (Sprint 15) caught the one assumption that mattered most.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-018 | DefCon reliability = `defensive_contribution_per_90 − threshold[pos]` (DEF 10, MID/FWD 12; GK excluded); minutes-gated; a single ranked `defcon` view | Accepted |

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

- Exact DefCon points (per-match data); a defensive / combined squad objective; a `--detail`
  flag to show the action components.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep verifying third-party field meanings at planning.

---

# Key Commands Learned

```text
python app.py defcon                 # reliable Defensive Contribution earners
python app.py defcon --pos DEF --min-minutes 1500
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Defensive Contribution (DefCon) | FPL's 2 pts/match for clearing a defensive-actions threshold |
| CBIT | Clearances + blocks + interceptions + tackles (the DEF count) |
| Threshold margin | Per-90 actions minus the bar — how reliably a player clears it |
| Position-correct field | A stat already computed per a position's rules |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-018 | Records the metric, thresholds, and the position-correct verification |
| Handbook Ch 25 | Defensive Contribution — the rules, the metric, the caveats |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Verifying data meaning | | |
| Reference-point metrics | | |
| Reusing a proven pattern | | |
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

- US-053 DefCon reliability design + ADR-018
- US-054 Ingest the five DefCon fields + migration
- US-055 The metric + the `defcon` view

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
