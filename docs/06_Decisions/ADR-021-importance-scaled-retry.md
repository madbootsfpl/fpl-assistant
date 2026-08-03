# Architectural Decision Record: Importance-Scaled Retry Policy

**Decision ID:** ADR-021
**Date:** 2026-08-03
**Status:** Accepted
**Superseded By / Replaces:** N/A (extends ADR-020's retry to both clients)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Sprint 019 (ADR-020) added retry-with-backoff to ClubElo. Two things then became clear:

1. The **FPL client** — the *required* source — has **no retry**, so a single momentary blip
   is fatal to the whole refresh. It arguably needs retry *more* than ClubElo.
2. During ClubElo's ongoing outage, the ClubElo retry (2 × 10s timeout) makes every refresh
   wait **~31s** before degrading — too long for an *optional* source.

The fix is one principle applied to both: **retry effort should scale with how much the source
matters.**

#### Decision Drivers
- **Survive a blip on the source that matters** — an FPL failure is fatal; retry it.
- **Don't let an optional source hold up refresh** — ClubElo should fail fast.
- **One mechanism** — reuse the ADR-020 helper; only the numbers differ.

---

### 💡 Decisions

**1. The principle.** The more a source matters, the harder we try; the more optional it is,
the faster we give up.

| Source | Importance | Policy |
|---|---|---|
| **FPL** | Required (failure is *fatal* — no degradation) | **2 retries** (3 attempts), **10s** timeout |
| **ClubElo** | Best-effort (failure degrades gracefully) | **1 retry** (2 attempts), **5s** timeout |

**2. FPL retry.** `_get_json` wraps its GET in `with_retry` (retries=2). On exhaustion it still
raises `FplApiError` — FPL has no graceful degradation and shouldn't; retry just gives it a
couple of chances before the (unchanged) fatal error. Healthy FPL responds in ~0.1s, so retry
adds **no** happy-path cost.

**3. ClubElo fast-fail.** Timeout drops to **5s** (a healthy ClubElo answers in ~1–2s, so a
2.5× margin) and retries to **1** → a sustained outage degrades in **~10.5s** (down from ~31s),
while a genuine blip is still retried once (preserving ADR-020's intent).

**4. One helper, two callers.** Both clients call the same `src/api/retry.py` `with_retry`;
only `retries` / `timeout` differ. No duplicated retry logic.

**5. Config.** A `config.CLUBELO_TIMEOUT = 5` constant makes the best-effort budget explicit
and separate from the FPL `REQUEST_TIMEOUT` (10s).

**Not in scope:** a circuit breaker (skip a *known-down* source across runs — needs persistent
state); changing FPL's fatal-on-failure behaviour; async fetching; an alternate Elo source.

---

### 🧪 Worked example (pressure-testing — run with the real helper)

Simulated with the actual `with_retry`, and the timing math:

| Case | Outcome |
|---|---|
| FPL blip `502, 200` | ✅ survives on attempt 2 (was fatal before) |
| FPL outage `503 × 3` | exhausted → `FplApiError` — fatal, as today |
| ClubElo outage (old 10s/2) | ~31.5s before degrade — today's pain |
| ClubElo outage (new 5s/1) | **~10.5s** before degrade |
| FPL outage (10s/2) | ~31.5s worst case, then fatal — rare (FPL ~0.1s), acceptable |

Confirms both policies behave as the principle claims, before any client code changes.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** A momentary FPL blip no longer kills refresh (the required source is now
  resilient); a down ClubElo degrades ~3× faster; the ADR-020 helper serves two callers with
  zero duplication; the policy is a stated principle, not ad-hoc numbers.
* **Negative / Trade-offs:** A *real* FPL outage now takes ~30s before the fatal error (rare,
  bounded). A shorter ClubElo timeout could clip a very slow but recovering ClubElo (unlikely
  at a 2.5× margin). A truly-down ClubElo still costs ~10s per refresh (a circuit breaker would
  fix that — deferred).
* **Risks & Mitigations:**
  - *ClubElo false-timeout* → 5s is 2.5× the healthy ~1–2s response (verified).
  - *FPL retry masks an outage* → bounded (2 retries) then `FplApiError`, fails clearly.
  - *Sprint-019 tests* → updated to the new fail-fast ClubElo numbers (US-061).

---

### 🛠 Implementation & Migration
* **Components Affected:** `FplClient` (retry params + wrap `_get_json`), `EloClient` (5s / 1
  retry defaults), `config` (`CLUBELO_TIMEOUT`), Docs. The retry helper and graceful degradation
  are unchanged.
* **Action Items:**
  - [x] Record the principle + policy + worked example (US-060)
  - [ ] Apply retry to FPL, tune ClubElo, update tests (US-061)
  - [ ] (Backlog) a circuit breaker to skip a known-down source across runs

---

### 🔄 Review & Reconsideration
* **Review Date:** If ClubElo's outage persists (consider the circuit breaker), or FPL
  reliability changes.
* **Triggers for Reconsideration:**
  - [ ] A long ClubElo outage makes even ~10s/refresh annoying → circuit breaker.
  - [ ] FPL starts failing often → revisit the FPL retry count / a degradation path.

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-060 (this), US-061
- **External Docs:** [ADR-020 (ClubElo retry)](./ADR-020-clubelo-retry.md) · [ADR-010 (ClubElo — graceful degradation)](./ADR-010-clubelo-external-source.md) · [Sprint 020](../05_Sprints/Sprint20.md)
