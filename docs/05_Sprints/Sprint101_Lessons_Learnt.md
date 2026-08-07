# Lessons Learned

**Sprint:** Sprint 101 — Pitch on Build + a season countdown / deadline banner

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

(1) The **Build** page shows its optimal 15 on the **green pitch** (reusing ADR-084), not only a table;
(2) a **season countdown / deadline banner** surfaces the next FPL deadline across the app, derived from
fixtures.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Reuse over rebuild** — a pure renderer (`render_pitch`) and stored data (`kickoff_time`) covered both
  features with tiny changes.
- **`now`-injected pure functions** — deterministic, unit-testable time logic.

### New Skills Acquired

- The next FPL deadline is **derivable from fixtures** (earliest `kickoff_time` of the next unfinished GW − 90
  min) — no `events` table needed; it matches the API's exact `deadline_time`.
- `get_upcoming_fixtures` didn't return `kickoff_time` (stored, not selected) — one additive column to the
  SELECT unlocked the feature; existing callers ignore the extra field.
- **stdlib `zoneinfo`** converts the UTC deadline to UK time ("Europe/London") for display — no dependency.
- A `next_deadline` that returns the first deadline **still ahead of now** rolls forward automatically once a
  gameweek locks — season-long, not just GW1.

---

# What Went Well ✅

- **Both were reuse** — the pitch is a pure renderer; the deadline comes from data we already store.
- **Verified first** — 380/380 fixtures carry `kickoff_time`, so derive-from-fixtures was a safe call.
- **Deterministic tests** — `now`-injected, so the roll-forward + UK-time conversion are pinned exactly.
- **Season-long** — a GW1 countdown now, the next GW's deadline later.
- 672 → 679 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| No `events` table for a deadline | never ingested | Derive it from fixtures' `kickoff_time` − 90 min |
| `kickoff_time` not returned | stored but not SELECTed | Add `f.kickoff_time` to `get_upcoming_fixtures` |
| A "today"-dependent test would be flaky | uses the current time | Inject `now` into the pure functions |
| Deadline shown in the wrong zone | stored as UTC | Convert to UK time with stdlib `zoneinfo` |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Derive, don't ingest | The deadline = earliest kickoff − 90; no new table |
| Additive SELECT | Return `kickoff_time`; existing callers ignore it |
| `now`-injected purity | Testable time logic, no flaky clocks |
| `zoneinfo` | UTC → UK time for display, stdlib only |

---

# Development Lessons 💻

- Check what's already stored before adding ingest — the `kickoff_time` column made the banner nearly free.
- Reuse a pure renderer across pages for consistency (the pitch now on My Squad + Build).
- Inject `now` so time-based features are deterministic under test.

---

# AI Collaboration Lessons 🤖

- Two small asks mapped to "reuse the pitch" + "derive from fixtures" — the least-code path that still ships
  the value. Verifying the data (kickoff times present) up front made the lightweight call obvious.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-086 | **A season countdown / deadline banner derived from fixtures** — a pure `next_deadline(fixtures, now)` (earliest `kickoff_time` of the next unfinished GW − 90 min; rolls forward each GW; empty-safe) + a `deadline_banner` (countdown + UK time via `zoneinfo`); on Home + Squads. No `events` ingest (the derivation matches the API's `deadline_time`); no live tick | Accepted |

_US-261 (pitch on Build) needed no ADR — it reuses ADR-084._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- **Chip Strategy — the gated half:** DGW/BGW detection (in-season) + mini-league position (leagues API, GW1).
- **Price Change Predictor** — plumbing dormant until GW1 (net transfers are 0 preseason).
- Post-**GW1 (2026-08-21)**: the Data Hardening flip + xP calibration.
- Backlog still open: a hosted LLM for the deploy (to light up free-form chat); persisted chat context;
  server-side squad persistence; grow the rules KB.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep checking stored columns before reaching for new ingest.

---

# Key Commands Learned

```text
python -m src.web_streamlit   # Home + Squads show the ⏳ next-deadline countdown; Build shows the 15 on a pitch
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Next deadline | Earliest kickoff of the next unfinished GW − 90 minutes |
| Roll forward | The banner advances to the next GW once a deadline passes |
| Derive-not-ingest | Compute a value from stored data instead of adding a table |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-086 | The deadline-derivation decision + why no `events` table |
| `src/analytics/deadline.py` | The pure `next_deadline` |
| `src/ui/deadline.py` | The countdown + UK-time banner |

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

- US-261 Pitch on Build — the optimal 15 on the green pitch (reuse ADR-084)
- US-262 Season countdown / deadline banner — a pure `next_deadline` from fixtures, on Home + Squads (ADR-086)

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
