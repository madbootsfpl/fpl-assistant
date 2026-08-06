# Lessons Learned

**Sprint:** Sprint 064 — Phase 6 Tier 2 (start): an FPL news lens + import team by manager-ID

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Open Phase 6 **Tier 2** ("social media news, feeds & trends, manager input") with two **free, no-key**
pieces (owner's calls): an FPL official-**news lens** and **import your team by manager-ID**. Degrade
gracefully (ClubElo pattern), lens/import not xP, no server writes; keyed social deferred.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Turning a broad "external data" ask into the cheapest viable slice by probing what's already free.
- Reusing the retry/degrade HTTP client + the graceful-degradation pattern for a new source.
- Unit-testing a network-backed feature with a **fake client** — no network, all branches covered.

### New Skills Acquired

- The FPL **public entry API** (`/entry/{id}/` + `…/event/{gw}/picks/`) and its **post-deadline** gating
  (picks 404 until a GW deadline).
- Mapping FPL picks (positions 1–11 XI / 12–15 bench, `is_captain`) → a `SquadStore`-shaped squad dict.

---

# What Went Well ✅

- **"Social media" became two free wins** — official news was already in the payload; the entry API needs
  no auth/secret. No new services, no secrets.
- **Robust by reuse** — the import reused `_get_json` (retry) + the ClubElo degrade pattern, so a bad id /
  down API / 404 picks all return a clear message, never a crash.
- **GW1-gating didn't block the build** — a **fake client** unit-tested all four branches, and the mapper
  was tested against a mocked picks payload, so the feature ships now and activates at GW1.
- **Architecture intact** — news + import are display/state; the import just joins build/upload as a way to
  set the session squad (no server writes); xP untouched.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A manager's squad 404s preseason | Picks are public only after a GW deadline | Validate the id via `/entry/{id}/`; a clear "available after GW1" message; live at GW1 |
| Testing a network feature preseason | Can't hit real picks | A **fake client** covers valid / preseason / bad-id / 404-picks with no network |
| Showing a source link | `scout_news_link` wasn't ingested | Add the field (model + `_migrate` + reseed), normalising `""`→None |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Probe before scoping | "Social media news" was largely free in the FPL data — check the source first |
| Reuse the degrade pattern | A new external source is robust by reusing the retry client + graceful-degradation flow |
| Fake the client | Network features are fully unit-testable by injecting a fake client — cover the failure branches |
| Public vs auth endpoints | The post-deadline picks are public (no secret); `/my-team/` would need auth — avoided |

---

# Development Lessons 💻

- Investigate the cheapest path before reaching for third-party APIs/secrets.
- Make external fetches degrade to a message, never a raise — and prove it with a fake-client test.
- Build a data-gated feature now (mock its payload) so it activates when the data goes live.

---

# AI Collaboration Lessons 🤖

- The owner's two calls (start with FPL news; "manager input" = import by ID) turned a broad, risky area
  into a crisp, free, buildable sprint.
- Surfacing the GW1-gating at planning made "build now, live at GW1" an informed, easy decision.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-058 | Phase 6 **Tier 2** opener — an FPL official-**news lens** + **import team by manager-ID** (public entry API → the session squad); free/no-secret; degrade-gracefully; not xP; no server writes; keyed social (Reddit/X) + pundit NLP deferred; import picks GW1-gated | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **GW1 (2026-08-21):** confirm the import pulls a real squad once picks unlock (verify the live picks
  shape); build the deferred **trends `ask` intent (US-185)** + **calibrate** the momentum thresholds +
  **Data Hardening**. Later, if wanted: **Tier-2b** keyed social (Reddit/X — needs a Cloud secret) / pundit
  NLP. Keep triaging **tester feedback** (`Feedback_Log.md`).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep probing for the free/lightweight path first; keep external sources degrade-gracefully + fake-client
  tested.

---

# Key Commands Learned

```text
python -m pytest tests/test_manager.py -q     # the picks→squad mapper + degrade branches (fake client)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Manager-ID / entry | A public FPL manager's numeric id; `/entry/{id}/` + `…/picks/` expose their team |
| Post-deadline gating | A manager's picks are public only after that gameweek's deadline (404 before) |
| Fake client | A stand-in for the HTTP client in tests — exercises success + failure branches, no network |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-058 | The Tier-2 model (news lens + manager import; degrade; deferred keyed social) |
| `src/manager.py` | The pure `picks_to_squad` + degrade-gracefully `fetch_manager_team` |
| `src/api/client.py` | The reused retry/`FplApiError` FPL client (now with entry endpoints) |

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

- US-189 Gate — ADR-058 (Tier-2 opener: news lens + manager import; free/no-keys; degrade; deferred social)
- US-190 FPL official-news lens (`pages/9_News.py` + ingested `scout_news_link`)
- US-191 Import team by manager-ID (`src/manager.py`; degrade-gracefully; built now, live GW1)

**Stories Carried Forward:**

- GW1: confirm the live import; US-185 trends intent + calibration + Data Hardening; Tier-2b keyed social

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
