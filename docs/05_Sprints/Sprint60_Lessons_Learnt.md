# Lessons Learned

**Sprint:** Sprint 060 — Phase 6 kickoff: the crowd lens (Tier 1, free FPL signals)

**Dates:** 2026-08-05 – 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Open **Phase 6 — Crowd & Sentiment Signals**: fold *"what managers are doing"* + expert signals into the
tools as a **complementary lens + flags, never blended into xP** (owner's calls), starting with the **free
FPL** signals. Ingest the Tier-1 fields, surface a `crowd_flags` lens, and prove the grounded xP is
untouched. External social / pundit deferred (Tier 2/3).

---

# Knowledge Compounded 📈

## Skills Strengthened

- Investigating a data source before designing — the FPL payload already carried most of the signal.
- Adding fields end-to-end through the model → schema → migration → ingest → UI path.
- Guarding an invariant with a single decisive test (xP unchanged by the lens).

### New Skills Acquired

- Recognising "crowd/sentiment" maps largely onto **free, structured** FPL fields (transfers, price, form,
  ICT, ownership) — no scraping needed for the high-value first layer.
- Reseeding the committed `seed.db` after a schema change so the deploy opens a matching schema (no
  migration-on-open write).

---

# What Went Well ✅

- **The investigation reshaped the phase.** Most of the ask was already free & structured in
  `bootstrap-static`, so Tier 1 shipped with zero scraping/APIs.
- **"Lens, not xP input" kept the model trustworthy** — and turned the risk into one clear test (mutate
  every crowd field → identical `decision_xp`).
- **The reseed pre-empted a known failure** — a schema change would otherwise `ALTER` the tracked `seed.db`
  on open (dirtying the tree → the Cloud git-sync glitch); regenerating the seed made opening it a no-op.
- **One pure helper, many surfaces** — `crowd_flags` on Players + three squad tabs, all from full player
  rows.
- Thresholds set on **real ownership data** (≥20% ≈ 17 template picks; ≤5% differential), not guesses.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A schema change would dirty the deployed `seed.db` | `_migrate` `ALTER`s missing columns on open (a write) | Reseed `seed.db` from a fresh refresh so its schema already matches → open is a no-op |
| Momentum/form thresholds can't be calibrated yet | 0 in preseason (live at GW1) | Set as **tunable constants** now; calibrate on the first live gameweek |
| "Differential" flag is common (422 players ≤5%) | Most of the market is low-owned | Kept it (ADR-044's definition); it's most useful in a squad context, and `template` is the rare, decisive one |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Investigate the source first | The available data can flip a "big scraping project" into a small free-fields one |
| Lens vs input | Keeping sentiment display-only preserved the grounded xP — and made the guarantee testable in one line |
| Schema change → reseed | After adding columns, regenerate the committed seed so the deploy doesn't write on open |
| Tunable thresholds | Constants in one module, calibrated on real data, beat magic numbers scattered in the UI |
| SELECT * pays off | `get_players` is `SELECT *`, so new columns flowed to every reader with no getter change |

---

# Development Lessons 💻

- Probe the real payload before scoping — it can collapse the plan (and the cost) dramatically.
- Encode an invariant ("xP unchanged") as a behavioural test, not a comment.
- When you change a schema that ships as a committed snapshot, regenerate the snapshot in the same change.
- Add display signals as a lens the core doesn't depend on — the analytics stay generic.

---

# AI Collaboration Lessons 🤖

- The owner's two calls (lens-not-xP; free-signals-first) set a crisp, buildable scope and a clean ADR.
- Presenting the investigation *before* the backlog let the design follow the data, not the other way round.
- "Proceed without my input" worked because the gate (ADR-057) had already fixed the decisions.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-057 | Crowd/sentiment signals as a **complementary lens + flags, never blended into xP**; Tier-1 **free FPL** fields; a pure `crowd_flags` helper with tunable, real-data thresholds; external social + pundit deferred (Tier 2/3) | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Tier-1 remainder:** Captain + Transfer flags; a **"trends"** `ask`/`chat` intent; a template-risk
  captaincy lens. Then **Tier 2** (external sentiment — Scout/Reddit, degrade like ClubElo) and **Tier 3**
  (backtest crowd-follow vs xP-only). **At GW1 (2026-08-21):** confirm the momentum/price/form flags light
  up and **calibrate `TRENDING_NET` / `FORM_MIN`** on real data.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep investigating the data before scoping; keep sentiment as a lens the grounded model doesn't depend on.

---

# Key Commands Learned

```text
python app.py refresh && cp data/fpl.db data/seed.db    # reseed the deploy snapshot after a schema change
python -m pytest tests/test_crowd.py -q                  # the crowd-flags + xP-invariance tests
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Crowd lens | Display-only crowd/sentiment flags shown alongside xP (never in it) |
| Template / differential | High-owned (≥20%) vs low-owned (≤5%) — ownership risk flags |
| Net transfers | `transfers_in_event − out` this GW — the buy/sell momentum signal |
| ICT | FPL's Influence/Creativity/Threat underlying-stats composite (shown as a column) |
| Reseed | Regenerate the committed `seed.db` so the deploy's schema matches the code |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-057 | The Phase 6 model (lens-not-xP; Tier-1 fields; thresholds) |
| `src/analytics/crowd.py` | The pure `crowd_flags` / `net_transfers` helper + tunable thresholds |
| Roadmap → Phase 6 | The three-tier plan (free → external → evaluate) |

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

- US-181 Gate — ADR-057 (crowd = lens + flags, not xP; Tier-1 free fields; thresholds)
- US-182 Ingest the Tier-1 crowd fields (model + storage + reseed)
- US-183 The `crowd_flags` lens on Players + Build/Analyse/My Squad (xP unchanged)

**Stories Carried Forward:**

- Tier-1 remainder (Captain/Transfer flags · "trends" ask intent · template-risk captaincy)
- GW1: calibrate the momentum/form thresholds on live data

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
