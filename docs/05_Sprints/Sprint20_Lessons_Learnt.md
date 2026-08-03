# Lessons Learned

**Sprint:** Sprint 020 — Resilience Round 2 (importance-scaled retry)

**Dates:** 2026-08-03

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Apply a deliberate, importance-scaled retry policy to both clients — FPL (required) retries
harder; ClubElo (best-effort) fails fast — so a momentary FPL blip is survived and a sustained
ClubElo outage degrades in ~10s instead of ~31s.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Reusing a source-agnostic helper for a second caller (nearly free).
- Encoding a principle in a decision, not just constants.
- Matching a resilience budget to the stakes (required vs best-effort).

### New Skills Acquired

- Tuning a timeout/retry budget to bound worst-case latency.
- Keeping a required source fatal-on-exhaustion while still retrying.

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- The Sprint-19 helper was source-agnostic, so this sprint added no new machinery.
- "Effort scales with importance" — a reusable rule, not just numbers.
- Fixed the live pain (refresh ~31s → ~10.9s) and made FPL survive a blip — proven live.
- Required-source resilience + best-effort speed in one coherent pass; DoD held (20th).

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| FPL blip was fatal | No retry on the required source | Apply the helper (2 retries); still fatal only on exhaustion |
| ClubElo outage = ~31s per refresh | 10s timeout × 3 attempts | Fail fast: 5s timeout, 1 retry → ~10s |
| Changing ClubElo defaults broke tests | Sprint-19 tests assumed 2 retries | Updated them to the fail-fast numbers |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Source-agnostic helpers | A second use is nearly free if the first was written generic |
| Principle over constants | A stated rule guides the next case; bare numbers don't |
| Budget vs stakes | Try hard for required; fail fast for optional |
| Fatal-after-retry | A required source retries, then still fails clearly (no silent bad data) |

---

# Development Lessons 💻

- Reuse the helper with different parameters rather than copying logic.
- Bound worst-case latency deliberately (timeout × attempts) for an optional source.
- Update the tests that encode a default when you change the default.

---

# AI Collaboration Lessons 🤖

- The ongoing outage sharpened a vague "add FPL retry" into a clear principle + a fix.
- The gate simulated both policies (with the real helper) before any client changed.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-021 | Importance-scaled retry: FPL (required) 2 retries/10s, still fatal on exhaustion; ClubElo (best-effort) 1 retry/5s, fast degrade; one helper, two policies | Accepted |

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

- A circuit breaker (skip a known-down source across runs) if ClubElo stays down for days.
- A combined defensive-value lens; a shared table renderer (tech debt).

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep encoding principles in ADRs, not just values.

---

# Key Commands Learned

```text
python app.py refresh     # FPL now survives a blip; ClubElo degrades in ~10s, not ~31s
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Required vs best-effort | A source whose failure is fatal vs one that degrades gracefully |
| Importance-scaled retry | Retry budget matched to how much a source matters |
| Fatal on exhaustion | A required source still errors clearly after retries (no silent pass) |
| Circuit breaker | Skip a known-down source for a cooldown (deferred) |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-021 | Records the principle + the two policies |
| Handbook Ch 23 | External Data — now with the importance-scaled policy table |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Reusing a generic helper | | |
| Principle-driven decisions | | |
| Tuning timeout/retry budgets | | |
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

- US-060 Importance-scaled retry policy + ADR-021
- US-061 Apply retry to FPL + tune ClubElo

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
