# Lessons Learned

**Sprint:** Sprint 136 — Beta usage & experience analytics (foundation)

**Dates:** 2026-08-09

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Answer *"what do beta testers use, do they return, does the app feel fast/reliable — without a separate analytics
project?"* with a **lightweight, anonymous, opt-in** analytics path to Supabase — where the **non-negotiable** is
that analytics can **never affect normal app operation**. This sprint builds the safe *foundation* (client +
returning-user id + wiring + the guardrail + docs); full event coverage + the admin view are Sprint 137.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Make the hard constraint the tested invariant** — "never affect the app" is a guardrail test, not a hope.
- **Reuse the proven edge** — a sibling table + the verified cookie component, not new infrastructure.

### New Skills Acquired

- **Fire-and-forget is how analytics stays non-blocking in Streamlit.** Streamlit reruns constantly; a synchronous
  POST per event would tax every interaction. Build the payload on the **main thread** (so session state is safe to
  read) then POST on a **daemon thread** with a tight timeout, the whole post wrapped to swallow everything. The app
  never waits; a dropped event never matters.
- **A "returning user" id must resist the cookie loading-run, or it over-counts.** Reading the `fpl_anon` cookie via
  the component returns `None` on the first run (loading) — if we minted a new id then, a *returning* user would get
  a fresh id every visit and unique-users would inflate. The fix is **defer-then-mint**: only mint once the
  component has settled (one-shot), so the first run trusts nothing and the second run trusts the read. (The Sprint
  134 lesson, reused.)
- **"Off by default" makes broad instrumentation safe.** `boot()` is a hard no-op without `FPL_ANALYTICS`, so
  wiring it into all 9 pages changed **nothing** for the existing suite — the off-path is byte-identical, pinned by
  a "no secrets → no POST" test. Broad wiring is safe precisely because the default path does nothing.
- **Anonymity is a payload contract you can test.** A test that asserts the **exact key-set** and scans for banned
  substrings (email/@/handle/player_ids/ip) turns "anonymous + minimal" from a promise into a check that fails if a
  future `meta` leaks PII.

---

# What Went Well ✅

- **The #1 rule is pinned** — the guardrail (raising store → the page still renders) + off-by-default (no writes)
  are tests, so "never affect the app" can't erode.
- **Reused, didn't re-architect** — endpoint derived from `FPL_STORE_URL` (no new secret) + the verified cookie
  component for the returning id; the feature is a sibling table + a thin client.
- **Non-blocking by construction** — main-thread payload, daemon-thread POST; every rerun stays fast.
- **Double-count trap avoided** — defer-then-mint on the anon id.
- 867 → 885 tests (+18); ruff + CI green; the 100th ADR.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A sync POST would slow reruns | Streamlit reruns a lot | Fire-and-forget: main-thread payload, daemon-thread POST |
| Analytics must never crash the app | any bug in a call site could | Blanket try/except in `track`/`_post`/`boot`; a guardrail test |
| Returning-id over-counts | the cookie reads None on the loading run | Defer-then-mint once the component has settled |
| Anonymity is easy to erode | a future `meta` could carry PII | A payload key-set + no-PII substring test |
| Instrumenting 9 pages is broad | a mistake could hit every page | `boot()` no-ops when off → the off-path is byte-identical |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Non-blocking emit | Payload on the main thread; POST on a daemon thread; swallow everything |
| Returning id | Defer minting until the cookie component settles (else the loading run over-counts) |
| Off-by-default wiring | A no-op-when-off hook makes broad instrumentation byte-identical |
| Testable anonymity | Assert the exact key-set + scan for banned PII substrings |
| Reuse | Derive a sibling endpoint + reuse the verified cookie component — no new secret |

---

# Development Lessons 💻

- For a cross-cutting side effect (telemetry), wrap it so it can never raise, and prove it with a guardrail test.
- When a background write must not block, build its inputs on the main thread and hand a plain payload to a thread.
- Instrument broadly only when the default path is a genuine no-op — then the change is safe by construction.

---

# AI Collaboration Lessons 🤖

- Analytics **observes the app, never the model**: it records *that* a page/analysis/save happened, never *what*
  the FPL engine decided — so the grounded/analytics-decide posture (ADR-037/041) is untouched. It's the **third**
  opt-in, secret-gated server write; the read-only invariant now names three exceptions, each pinned by a test.

### Notes _(for Tony)_

---

# Decisions Made 📋

_**ADR-100** — beta usage & experience analytics: an opt-in (`FPL_ANALYTICS` + the store), anonymous (a session
`uuid4` + a persistent `fpl_anon` UUID cookie — no PII, not the handle), **fail-silent** (fire-and-forget daemon
thread, swallow-all, no-op when off) write of small usage + `perf` events to a Supabase `events` table (endpoint
derived, no new secret). The 3rd opt-in secret-gated server write; guardrail-pinned. Built: US-332 (client +
`APP_VERSION`), US-333 (the returning-user id), US-334 (wiring + guardrail + `ANALYTICS.md`). Sprint 137 = full
coverage + admin. Docs: ANALYTICS.md, DIRECTION, BETA.md, PROJECT_STATUS, Architecture._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner (the smoke):** create the `events` table (+ anon-insert RLS, `docs/ANALYTICS.md`) → set `FPL_ANALYTICS=1`
  → use the app → confirm rows land in Supabase **and** the app is unaffected (kill the network — still fine).
- **Sprint 137:** the feature events (`squad_created`/`analysis_run`/`player_viewed`/`squad_*`/`feedback_*`) +
  `error` at the key sites + perf timers on the key ops + a minimal gated **admin view** (`FPL_ADMIN_KEY`).
- **GW1 (2026-08-21):** the big body — calibrate the set-piece / DefCon / form weights + backtest; momentum;
  live manager import.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep cross-cutting side effects fail-silent + off-by-default + guardrail-pinned; keep telemetry observing the app,
  never the model.

---

# Key Commands Learned

```text
python -m pytest tests/test_analytics.py -q          # the client, the anon id, boot, and THE guardrail
# enable (Streamlit secrets): FPL_ANALYTICS = "1"  (+ the events table, docs/ANALYTICS.md)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Fire-and-forget | Emit on a daemon thread, don't wait; a dropped event is acceptable |
| Fail-silent | Swallow every error so telemetry can never surface into the app |
| Defer-then-mint | Wait for the cookie to settle before minting a new returning-id (avoids over-counting) |
| The guardrail | A test that a raising store never breaks a page + no writes when off |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/web_streamlit/analytics.py` | The fail-silent client (`is_enabled`/`track`/`timed`/`boot`/`anon_id`) |
| `docs/ANALYTICS.md` | Owner setup — the `events` table SQL/RLS, the flag, the inspection queries |
| `docs/06_Decisions/ADR-100-…` | The analytics decision + the privacy/guardrail posture |
| `tests/test_analytics.py` | The guardrail + the anonymity + off-by-default tests |

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

**Sprint Outcome:** ☑ Successful (foundation — owner smoke to confirm the live write) ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- ADR-100 The analytics write path (opt-in, anonymous, fail-silent)
- US-332 The analytics client (`analytics.py` + `APP_VERSION`)
- US-333 The `fpl_anon` returning-user id (named cookies + defer-then-mint)
- US-334 Core wiring (`session_started`/`page_viewed`) on all 9 pages + the guardrail + `ANALYTICS.md`

**Stories Carried Forward:**

- Sprint 137: full event coverage + `error` + perf timers + a minimal gated admin view.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
