# Lessons Learned

**Sprint:** Sprint 019 — ClubElo Resilience (retry-with-backoff)

**Dates:** 2026-08-03

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Make the ClubElo fetch survive a transient failure — retry a few times with a short backoff
on 502/503/504, timeouts and connection errors, before falling back to last-known Elo — so a
momentary blip no longer loses the Elo refresh.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Diagnosing a "bug" before fixing (often the system is fine; the fix is a hardening).
- Classifying errors into transient (retry) vs permanent (fail fast).
- Injecting time (`sleep`) so time-based logic is testable instantly.

### New Skills Acquired

- Retry-with-exponential-backoff as a reusable, source-agnostic helper.
- Layering resilience: retry (blip) + graceful degradation (outage).

### Areas Needing More Practice _(for Tony)_

-
-

---

# What Went Well ✅

- A real bug report (ClubElo 502s) became a scoped resilience layer.
- Diagnosis first: the probe proved nothing was broken — the fix is an improvement.
- Live confirmation — ClubElo actually timed out mid-smoke-test; the retry then degrade fired.
- Layered resilience; the 3-part DoD held (19th sprint).

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A transient 502 lost the whole Elo refresh | One-shot fetch | Retry transient errors before degrading |
| An existing test would now sleep ~1.5s | ConnectionError is transient → retried | Inject a no-op `sleep` in the test |
| Report an accurate attempt count | Permanent vs exhausted differ | `retries+1 if is_transient(exc) else 1` |
| Full-outage latency grew (~30s) | 10s timeout × 3 attempts | Documented, bounded, tunable (backlog: shorter timeout) |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Diagnose first | A failing system may be fine; scope the fix to the real gap |
| Error classification | Retry only what a retry can fix; fail fast on 4xx |
| Inject time | An injected `sleep` makes backoff instant *and* assertable in tests |
| Layered resilience | Retry (blip) + degradation (outage) each do a distinct job |

---

# Development Lessons 💻

- Wrap only the network call in the retry; keep the degradation contract unchanged.
- The last exception's type tells you the path taken (permanent vs exhausted).
- Write the helper source-agnostic so another client can reuse it.

---

# AI Collaboration Lessons 🤖

- Tony's reflection carried a real bug; diagnosing it first avoided a wrong fix.
- The gate simulated the retry across three scenarios before any client code changed.

### Notes _(for Tony)_

-

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-020 | ClubElo retry-with-backoff: retry 502/503/504 + timeouts/connection (2 retries, exp backoff), fail fast on 4xx, then degrade; reusable helper; injectable sleep | Accepted |

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

- Apply the retry helper to the FPL client (required source, fatal on failure).
- Consider a shorter ClubElo timeout to bound full-outage latency.

## Personal Improvements _(for Tony)_

-

## Workflow Improvements

- Keep diagnosing before fixing; keep the gate + 3-part DoD.

---

# Key Commands Learned

```text
python app.py refresh     # ClubElo now retries a transient 502 before degrading
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Transient error | A momentary failure a retry can fix (502/503/504, timeout) |
| Exponential backoff | Waiting longer between each retry (0.5s, 1s, …) |
| Fail fast | Give up immediately on an error a retry can't fix (4xx) |
| Retry then degrade | Retry a blip; if it's a real outage, fall back gracefully |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-020 | Records the classification, policy, and retry-then-degrade placement |
| Handbook Ch 23 | External Data — now with the retry layer + the latency trade-off |

---

# Questions for Future Me ❓ _(for Tony)_

-

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

| Topic | Before | After |
|--------|-------:|------:|
| Diagnosing before fixing | | |
| Retry / backoff patterns | | |
| Testable time-based logic | | |
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

- US-058 Retry-with-backoff design + ADR-020
- US-059 The retry helper + ClubElo resilience

**Stories Carried Forward:**

- None

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
