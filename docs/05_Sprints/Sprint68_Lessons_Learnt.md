# Lessons Learned

**Sprint:** Sprint 068 — Community Signals: Reddit RSS buzz (no auth)

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Ship real community "buzz" — who r/FantasyPL is talking about — **without** Reddit Developer access or a
secret, by reading the **public RSS** feed. Degrade-gracefully, cached, button-gated. Buzz (mention
frequency), not sentiment; display-only, never xP.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Probing an external source's real behaviour before committing (`.json` 403 vs `.rss` 200).
- Reusing the best-effort external-source pattern (ClubElo) for a new, flaky source.
- Keeping the network out of tests with an injectable fake client.

### New Skills Acquired

- Reddit's public **RSS** feed is reachable without OAuth while the `.json` API is blocked — a legitimate,
  lightweight substitute for a keyed API (for low-volume, cached reads).
- `@st.cache_data(ttl=…)` + button-gating to respect an external rate limit and avoid fetch-on-every-rerun.

---

# What Went Well ✅

- **The owner's RSS idea removed the blocker** — no Developer application, no secret; a probe confirmed it.
- **Robust by pattern** — mirroring ClubElo (self-contained client, retry-then-error, caller degrades) made
  it crash-proof; any 403/429/parse error → "unavailable".
- **Testable without network** — a fake client covered degrade + success; the pure counter took a sample
  RSS string; the board is button-gated so the page test makes no network call.
- **Honest scope** — framed as *buzz* (mention frequency), not sentiment.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| The `.json` API 403s (all UAs) | Reddit locked it down / IP block | Use the public `.rss` feed instead (200, no auth) |
| Rate limits (429 on rapid repeats) | Reddit throttles | Cache (~30 min) + button-gate + a descriptive UA |
| Network in tests would be flaky | The board fetches Reddit | Button-gate (no fetch on load) + a fake client for the orchestrator |
| The cloud may be blocked | Datacenter IP | Degrade to "unavailable" (best-effort, like ClubElo) — accepted |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Probe first | The exact failure (`.json` 403 / `.rss` 200) reshaped the whole design |
| Reuse the degrade pattern | A new flaky source is robust by reusing the ClubElo client + graceful-degradation flow |
| Fake the client | Network features are fully testable by injecting a fake client + a sample payload |
| Gate the fetch | Button-gate + cache an external, rate-limited call — don't fetch on every rerun |

---

# Development Lessons 💻

- Read the source's real responses before designing — a blocked API can have an open side door (RSS).
- Make external reads best-effort + cached + gated; degrade to a message, never a crash.
- Keep the pure parser separate from the network so it's trivially unit-tested.

---

# AI Collaboration Lessons 🤖

- The owner's "use the public RSS instead of the API?" was the key unlock — worth probing a user's idea
  literally before assuming the harder path.
- Naming it "Community Signals" (owner) framed it well — a buzz lens, not a prediction.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-059 | **Community Signals** via the Reddit **RSS** feed (no auth/secret); degrade-gracefully; cached + button-gated; buzz (frequency) not sentiment; a Trending "💬 Talked about" board; not xP; cloud-IP may block → degrades | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Verify on the live cloud IP** after redeploy (it may degrade to "unavailable"). If it's reliably
  blocked, a tiny proxy/cache is the fallback — or accept it as local-only. A future NLP step could turn
  buzz into real sentiment. **GW1 (2026-08-21):** the momentum boards/questions, threshold calibration,
  Data Hardening, and the live manager-import all light up.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep probing the source; keep external reads best-effort + cached + gated.

---

# Key Commands Learned

```text
python -m pytest tests/test_community.py -q     # the buzz counter + the degrade-gracefully orchestrator
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Community Signals | The buzz feature — who r/FantasyPL is talking about (Reddit RSS mention counts) |
| Buzz (vs sentiment) | Mention *frequency*, not positive/negative — a lighter first signal |
| Button-gated fetch | An external call that runs on a click, not on every page render |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-059 | The RSS-not-OAuth decision + the degrade/cache/gate design |
| `src/api/reddit.py` + `src/community.py` | The best-effort RSS client + the pure buzz counter |
| `r/FantasyPL/.rss` | The public feed (no auth) that made this possible |

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

- US-195 Community Signals — a Reddit RSS buzz counter + a Trending "Talked about" board (no auth)

**Stories Carried Forward:**

- None (GW1 markers stand; verify Community Signals on the live cloud IP)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
