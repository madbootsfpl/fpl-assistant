# Lessons Learned

**Sprint:** Sprint 067 — Community "trending" (free FPL crowd data): a Trending view + a trends `ask`

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Surface **community "trending"** — which players are being picked / moving — from **free FPL crowd data**
(ownership · transfers · form), as a pure `trending` helper powering both a **Trending page** and a
**trends `ask` intent**. Real social-media sentiment (Reddit) recorded as a gated follow-up. Display-only,
never xP.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Reframing a broad ask ("social media sentiment") to the cheapest slice that delivers most of the value.
- One pure helper feeding two surfaces (a page + an `ask` intent) — no duplicated ranking.
- Ordering keyword-routing so a specific phrase ("most transferred") beats a broad one ("transfer").

### New Skills Acquired

- Probing an external source's feasibility up front (Reddit's public JSON now 403s → needs OAuth + a secret).

---

# What Went Well ✅

- **The reframe was the win** — most of "which players are trending as picks" was **free FPL crowd data we
  already ingest**, so no scraping/secret was needed to ship the core.
- **One helper, two surfaces** — `trending()` fed the page and the `ask` intent identically.
- **Clean routing** — "trends" keywords first cleanly split "most transferred" (trends) from "transfer"
  (advice), verified by tests.
- **Honest gating** — each momentum surface says "live at GW1", not a blank board.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A new intent could steal "transfer" questions | "most transferred" contains "transfer" | Put "trends" first with distinctive phrases; a routing test guards it |
| Momentum boards empty preseason | transfers/form are 0 until GW1 | Ownership board works now; momentum boards/questions say "live at GW1" |
| Real social sentiment isn't free | Reddit public JSON → HTTP 403 | Deferred to a gated spike (US-195/ADR-059) needing a Reddit app + a cloud secret |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Reframe to the free slice | "Social sentiment" was largely free FPL crowd data — check what you already have |
| One pure helper, many surfaces | A ranking function in the core feeds page + `ask` with zero duplication |
| Keyword precedence | Order intents so specific phrases win before broad ones (trends before transfer) |
| Probe external feasibility first | The Reddit 403 turned "add social" into "a gated, secret-bearing spike" |

---

# Development Lessons 💻

- Build the free, no-infra slice first; gate the costly external layer behind a spike + a decision.
- Put ranking/shaping in the pure core and let edges (page, `ask`) render it.
- Gate data-dependent surfaces with a clear "live at <date>" message, not an empty view.

---

# AI Collaboration Lessons 🤖

- The owner's "both — free trending now, Reddit spike after" split matched effort to value: ship the cheap
  win, gate the expensive one.
- Surfacing the Reddit 403 + the ownership-now/momentum-GW1 split at planning made the scope honest.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — the trends intent executes ADR-057; the Trending page is UI over the settled edge. The Reddit
spike will get **ADR-059** when it's built (US-195, gated on a cloud secret)._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **US-195 (gated):** the Reddit social-sentiment spike — create a Reddit app + set the client id/secret as
  a cloud secret, then a degrade-gracefully adapter + a mention-counter; ADR-059 decides go/no-go.
- **GW1 (2026-08-21):** confirm the momentum boards/questions populate + calibrate thresholds; the live
  manager-import check; Data Hardening.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep reframing to the free slice; keep gating external/secret-bearing sources behind a spike.

---

# Key Commands Learned

```text
python -m pytest tests/test_crowd.py tests/test_ask.py -q   # the trending helper + the trends intent
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Trending board | A leaderboard by a free crowd metric (most-owned / transferred / in-form) |
| Keyword precedence | Ordering intents so a specific phrase routes before a broad one |
| Gated spike | A feasibility build behind a prerequisite (here: a Reddit app + a cloud secret) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/analytics/crowd.py` (`trending`) | The pure ranking that feeds the page + the `ask` intent |
| `src/web_streamlit/pages/10_Trending.py` | The Trending leaderboards |
| Roadmap → Phase 6 Tier 1/2 | Trends done ✅; Reddit spike recorded (US-195/ADR-059) |

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

- US-193 `trending` helper + a trends `ask`/`chat` intent
- US-194 Trending page (most-owned / transferred in-out / in-form boards)

**Stories Carried Forward:**

- US-195 Reddit social-sentiment spike (ADR-059) — gated on the owner's Reddit app + a cloud secret

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
