# Lessons Learned

**Sprint:** Sprint 026 — Historical Trend Data & Enriched xP (Phase 2 begins)

**Dates:** 2026-08-03

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Ingest FPL past-season history (`history_past`, via a throttled backfill) into a new store, and
enrich xP with a multi-season baseline so it's robust preseason — the historical foundation Phase 3
will build on. Also stand up CI (lint + tests on push). FPL-native; no new dependency.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Adding a second API endpoint + a new store behind the existing one-way-flow layers.
- Rate-limit discipline: a throttled, idempotent, per-item-degrading bulk fetch.
- Enriching a metric's *input* without changing its formula (policy at the edge).

### New Skills Acquired

- A minutes-gated, recency+minutes-weighted multi-season rate from historical data.
- CI with GitHub Actions + a right-sized ruff ruleset + pre-commit.

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- **Verify-at-planning reshaped the sprint.** Probing the live API first revealed we're preseason
  (no per-GW history) and that history is per-*season* — steering away from a wrong "per-GW trends"
  design before a line of code.
- **Verify-on-real-data caught two more things unit tests couldn't.** (1) A Haaland-only planning
  sample wrongly suggested xG is reliable across seasons; the broad backfill showed `'0.00'` for
  older seasons. (2) The xP smoke showed cameo seasons inventing pp90 = 90 — fixed with the
  ≥900-min gate (the Sprint 016 Meslier lesson, a third time).
- **Enriched xP without touching its formula** — only the rate input changed; the formula, horizon,
  availability, and optimiser were untouched.
- **CI right-sized** — a small stable ruleset that catches real problems without churning correct
  code. DoD held for the 26th sprint.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| No per-GW history to trend | Preseason (0 GWs played) | Use per-*season* summaries; defer per-GW to when GWs play |
| 567 calls could rate-limit | `element-summary` is per-player | Throttled, idempotent, per-player-degrading backfill, out of `refresh` |
| Historical xG/DC read `0.00` | FPL only backfills them recently | Consume only points+minutes; caveat documented (ADR-027) |
| Cameo seasons → absurd pp90 (90.0) | No minimum-sample gate | ≥900-min gate (as DefCon/over-under use); caught by live smoke |
| A first linter can flag working code | Opinionated defaults (DTZ/RUF) | Scope ruff to E/F/I; `date.today()` left alone |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Probe broadly | One marquee player (Haaland) isn't a representative sample — it hid the xG gap |
| Gate small samples | Any computed rate needs a minimum sample, or a cameo invents nonsense |
| Data provenance | A `0.00` in an old season often means "not tracked", not a real zero |
| Enrich the input | Improve a metric by feeding it a better number, not by rewriting the formula |
| CI scope | A first CI should catch real problems, not force churn on correct code |

---

# Development Lessons 💻

- Test on **real data**, not just clean fixtures — it found what the unit tests couldn't (twice).
- Keep bulk network work throttled, idempotent, and out of the hot path.
- Correct the record when a smoke test disproves a planning assumption (ADR-027/028 both amended).

---

# AI Collaboration Lessons 🤖

- The gates (ADR-027/028) settled source, schema, rate-limit, and the modelling method up front,
  each pressure-tested on real numbers before code.
- Being honest about a wrong planning assumption (xG reliability) mid-sprint kept the docs accurate.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-027 | Historical past-season data via FPL `element-summary.history_past`; `player_history_past` keyed by `element_code` (no FK); a throttled/idempotent `history --backfill`; the provenance caveat (old-season xG/DC unreliable) | Accepted |
| ADR-028 | Enrich xP with a multi-season baseline rate (recency+minutes-weighted pp90, ≥900-min gated, reliable fields only); preseason uses it outright, falls back to current ppg; formula unchanged | Accepted |

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

- Pick the next Phase 2 direction: a full backfill in the wild, per-GW history + live-form blending
  once GW1 plays, the web UI, or a Phase 3 decision-support feature on the improved xP.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Probe broadly at planning (a spread of player types, not one star).
- Keep the gate + 3-part DoD; re-check ClubElo while it's down.

---

# Key Commands Learned

```text
python app.py history --backfill            # fetch every player's past-season summaries (throttled)
python app.py history --backfill --limit 50 # a quick slice (testing)
python app.py xp --limit 15                 # xP now uses a multi-season baseline rate (* = baseline)
ruff check .                                # the lint CI runs
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| `history_past` | FPL's per-season summary per player (from `element-summary`) |
| `element_code` | A player's stable id across seasons (vs the per-season `id`) |
| Backfill | A one-off bulk fetch of historical data (throttled, idempotent) |
| Baseline rate | A multi-season points-per-90, recency+minutes weighted, minutes-gated |
| Minutes gate | A minimum-sample threshold so a cameo can't invent a rate |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-027 / ADR-028 | The history source + the xP baseline method, with the caveats |
| Handbook Ch 21 | Analytics — now with "enrich the input, not the formula" + the gate |
| Handbook Ch 11 | Testing — now with the CI section |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Ingesting a new API endpoint + store | | |
| Rate-limit-safe bulk fetches | | |
| Enriching a metric (input vs formula) | | |
| CI / GitHub Actions | | |
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

- US-076 Historical data design + ADR-027 (gate)
- US-077 Ingest past-season history (`history --backfill`)
- US-078 Enrich xP with a multi-season baseline + ADR-028
- US-079 CI/CD (GitHub Actions + ruff + pre-commit)

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
