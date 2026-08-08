# Lessons Learned

**Sprint:** Sprint 115 — Signal feeds (a media-headlines lens + sharper "talked about")

**Dates:** 2026-08-16

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Review ~12 external signal sources and add the ones that add value to **News** / **Trending** — without
scraping, auth, or crossing the lens→xP line. Adopt: Fantasy Football Scout + BBC Football (News) and Reddit
weekly-top (Trending), via one generic best-effort mechanism; defer the rest with a recorded policy.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Source triage** — judging a feed by public/no-auth, parseable, FPL-relevant, cloud-safe, lens-only.
- **Best-effort integration** — cached, gated, degrade-gracefully, tested without live network.

### New Skills Acquired

- **Verify feeds before planning.** Fetching each candidate from the environment (FFS 12 · BBC 70 · Reddit-top
  25) turned a long list into a grounded adopt/defer split, and caught that the FFS *tag* feed is malformed
  (use the main `/feed/`).
- **One parser for RSS *and* Atom.** `parse_feed` handling `<item>` and `<entry>` meant FFS, BBC, YouTube and
  Reddit all share one tested path — no per-source code, no new dependency (stdlib `ElementTree`).
- **Degrade is a design, not an afterthought.** Per-feed try/except + a cache + a button gate means a blocked
  feed never delays or breaks the page — and it's testable with a fake client (no network in CI).
- **Record the policy, not just the code.** ADR-093 writes down *why* each source is adopted/deferred, so the
  next "add this feed?" is a quick triage against stated rules.
- **Don't hard-code what you can't verify.** The YouTube channel-id hit a consent wall; shipping the mechanism
  + a documented slot is more honest than guessing an id.

---

# What Went Well ✅

- **The review was the deliverable** — a clear adopt/defer verdict + ADR-093.
- **A generic, dependency-free mechanism** covered four feeds through one path.
- **Best-effort held** — gated + cached + degrade; tests use fixtures/fakes, no live network.
- 739 → 746 tests; ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| 12 sources, unclear value | mixed feeds/HTML/auth/odds | Verify each from the env → adopt 4 (public RSS) / defer 8 (policy in ADR-093) |
| RSS vs Atom formats | FFS/BBC are RSS, YouTube/Reddit Atom | One `parse_feed` handling `<item>` + `<entry>` |
| Cloud IPs get 403'd | rate-limits / bot blocks | Button-gate + cache + per-feed degrade |
| No verifiable YouTube id | YouTube consent wall in the sandbox | Ship the mechanism + a documented `MEDIA_FEEDS` slot |
| No live network in tests | best-effort clients hit the net | Fixtures + a fake/monkeypatched client; render tests don't click |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Source triage | public + no-auth + parseable + FPL-relevant + lens-only |
| One parser | RSS `<item>` + Atom `<entry>` share a code path (stdlib) |
| Best-effort | gate + cache + per-feed try/except → resilient by construction |
| Test boundary | fake the client / don't click → no live network in CI |

---

# Development Lessons 💻

- Verify external inputs from the actual environment before designing around them.
- Prefer one generic mechanism + a config list over per-source code.
- Make "it can fail" a first-class path (degrade), and test it with fakes.

---

# AI Collaboration Lessons 🤖

- Feeds are a *lens*: headlines/buzz inform the human, and ADR-093 pins them out of `decision_xp` — so richer
  context never distorts the grounded recommendations.

### Notes _(for Tony)_

---

# Decisions Made 📋

_**ADR-093** (new) — an external signal-source **policy** (adopt public, no-auth, FPL-relevant RSS/Atom;
defer scraping/auth/odds) + a **media-headlines lens**: `api/feeds.py` (`MediaFeedsClient` + `parse_feed` for
RSS + Atom), `config.MEDIA_FEEDS`, `web_streamlit/media.py::media_headlines`; a News Headlines section +
`RedditRssClient.get_top_weekly()` for Trending. Display-only, best-effort, no new dependency._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Wire a YouTube creator** once a `channel_id` is supplied (one `MEDIA_FEEDS` line).
- **A hosted LLM for the deploy** so prose + the free-form tail work on the cloud.
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- Post-**GW1 (2026-08-21)**: Data Hardening + xP calibration; the price/form/ownership signals sharpen;
  calibrate the price-predictor thresholds; possibly revisit odds as a *Tier-3 modelling* input (not a lens).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep verifying external sources from the environment before building — it right-sizes the work and the risk.

---

# Key Commands Learned

```text
python -m src.web_streamlit   # News → "Load headlines" (FFS + BBC) · Trending → "Top discussions this week"
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Media-headlines lens | Aggregated public RSS/Atom headlines (title + link), display-only |
| Best-effort feed | Fetched on demand, cached, degrades to a note on failure |
| Signal-source policy | ADR-093's adopt/defer rules for external feeds |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/api/feeds.py` (`parse_feed`) | One parser for RSS + Atom |
| `docs/06_Decisions/ADR-093-signal-sources-and-media-lens.md` | The adopt/defer policy + design |
| `src/config.py` (`MEDIA_FEEDS`) | Add/remove a feed in one line |

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

- US-291 Media-headlines lens on News — a generic RSS/Atom aggregator (FFS + BBC; YouTube documented) (ADR-093)
- US-292 Sharper "talked about" on Trending — Reddit weekly-top discussions (titles + links)

**Stories Carried Forward:**

- None. (YouTube feed wired but needs a channel-id.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
