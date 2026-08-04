# Lessons Learned

**Sprint:** Sprint 037 — Expected minutes (xMins) v0

**Dates:** 2026-08-04

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Build xMins v0 — a lightweight, FPL-native estimate of expected minutes (`chance_of_playing%` × a
historical minutes share) that **weights xP by playing time** at the decision edge, so rotation risks
stop out-ranking nailed-on starters. Shown as expected minutes, default-on, with a `--no-xmins`
opt-out; the raw `xp` view stays pure. No ML, no new dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Verifying a data assumption on the real table *before* building on it.
- Generalising an existing seam (a binary gate → a continuous [0,1] weight) rather than adding a path.
- Keeping a change provably safe with a default-off hook (byte-identical without it).

### New Skills Acquired

- A recency-weighted "share of a full season's minutes" as a rotation signal (minutes-only).
- Threading a per-player weight through analytics into a display column, in the user's units.

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- **Planning caught a real bug before code — twice.** The probe proved `starts` is all-zeros
  pre-2022/23 (so "minutes/starts ratio" would divide by garbage → corrected to a minutes *share*),
  and that suspended players carry `chance = None` (so the guard must key on *status*).
- **Policy at the edge kept the blast radius tiny** — the raw `xp` view is byte-identical; every prior
  test stayed green.
- **It visibly changes recommendations** — captain re-ranks, analyse projects a truer 209 (Ampadu at
  41 mins), transfer targets the rotation risk; `ask` stays grounded (✓).
- **Minutes, not fractions** — Tony's "show 56, not 0.62" made the feature read instantly.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| "minutes / starts ratio" would break | `starts` is 0 for every season pre-2022/23 | Minutes-only **share** = minutes / (38×90) |
| Suspended players not zeroed | They show `chance = None`, not 0 | The availability guard keys on **status** (i/s/u → 0) |
| Signal barely fired | History backfill was only 29% | Broadened the backfill to 87% |
| Changing every recommendation's numbers | Weighting is default-on | Policy at the **edge**; raw `xp` untouched; `--no-xmins` reproduces today; the weight is shown |
| A nailed-on premium demoted | Historical minutes reflect past injuries (role change) | Honest v0 limit; `--no-xmins` + Phase 5 (in-season minutes) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Verify the data, not the docs | `starts` looked usable and wasn't — check the real table |
| Generalise the seam | A binary availability gate becomes a [0,1] weight — one hook, not a parallel path |
| Provably safe defaults | A default-off (`minutes_weight=None`) hook keeps existing output byte-identical |
| Units matter | Show a weight as expected minutes (×90) — the unit the user reasons in |
| Different gate for a different job | No 900-min gate here — low minutes *should* lower the weight (opposite of the rate baseline) |

---

# Development Lessons 💻

- A one-line data probe (`SELECT … starts>0 …`) can save a whole wrong implementation.
- Put realism where decisions are made; keep the raw analytics pure and comparable.
- Give the user the off-switch for any heuristic that changes their numbers.

---

# AI Collaboration Lessons 🤖

- The gate's worked example (weights on TS) surfaced the coverage gap and the role-change limit before
  a line of production code — the pressure-test *is* the design review.
- One focused UX question ("how to show it?") + Tony's "minutes, not 0.65" shaped the display better
  than guessing would have.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-038 | Expected minutes (xMins) v0: `availability_weight = chance_factor × recency-weighted minutes share` (minutes-only — no `starts`, no 900-min gate; graceful fallbacks); a `minutes_weight` hook on `player_xp` (byte-identical without it); default-on at the decision edge (captain/transfer/analyse/`ask`) shown as expected minutes with a `--no-xmins` opt-out; the raw `xp` view stays pure. Honest scope: not a per-fixture probability (role-change + coverage limits → Phase 5) | Accepted |

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

- The full probabilistic xMins (congestion / European / rotation profiles) — Phase 5, post-GW1
  (needs in-season per-GW minutes + external fixture data). Or the web UI, or more Phase 4.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep verifying data assumptions on the real table at the gate; keep the 3-part DoD.

---

# Key Commands Learned

```text
python app.py history --backfill                 # broaden past-season coverage (feeds xMins)
python app.py captain --squad TS                 # xP weighted by expected minutes (xMins column)
python app.py captain --squad TS --no-xmins      # the raw "assumes 90" numbers
python app.py analyse --squad TS                 # the xMins column flags rotation risks in the XI
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| xMins | Expected minutes — how long a player is likely to play; used to weight xP |
| Minutes share | A player's minutes as a fraction of a full season (38 × 90) — the rotation signal |
| chance_factor | `chance_of_playing% / 100`; status i/s/u → 0 (suspended shows chance None) |
| Policy at the edge | Realism applied where decisions are made; the raw analytics stay generic |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-038 | The xMins v0 design + the honest scope |
| ADR-028 / ADR-006 | The xP rate baseline + the binary availability gate this generalises |
| Backlog → Expected minutes (xMins) | v0 marked done; the full model (Phase 5) |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Verifying data assumptions | | |
| Generalising a seam safely | | |
| Modelling expected minutes | | |
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

- US-109 xMins v0 design + ADR-038 (gate — pressure-tested on real data)
- US-110 The engine: `analytics/minutes.py` + the `player_xp` `minutes_weight` hook
- US-111 Wire into the decision edge (default-on; `xMins` column; `--no-xmins`; backfill broadened)

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
