# Architectural Decision Record: ClubElo Retry-with-Backoff

**Decision ID:** ADR-020
**Date:** 2026-08-03
**Status:** Accepted
**Superseded By / Replaces:** N/A (extends ADR-010's graceful degradation)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Tony hit repeated ClubElo failures on refresh — `502 Server Error: Bad Gateway` — on two
separate attempts. A probe diagnosed it as **transient**: the exact URL
(`http://api.clubelo.com/2026-08-03`) returns 200 with valid CSV now; ClubElo is a free hobby
API that occasionally has gateway hiccups. Our graceful degradation (ADR-010) handled it
correctly (kept last-known Elo, non-fatal) — but a *single* blip loses the whole Elo refresh
for that run, when a retry seconds later succeeds.

#### Decision Drivers
- **Robustness** — a momentary blip shouldn't cost the Elo refresh.
- **Don't waste time** — only retry errors a retry can fix.
- **Preserve the existing contract** — graceful degradation stays the final backstop.

---

### 💡 Decisions

**1. Classify errors.**
- **Transient (retry):** HTTP **502 / 503 / 504**, `requests.Timeout`, `requests.ConnectionError`.
- **Permanent (fail fast):** 4xx and anything else — a retry won't help, so don't wait.

**2. Retry policy.** Default **2 retries** (3 attempts total) with **exponential backoff**,
base 0.5s → waits 0.5s then 1.0s. Both `retries` and `backoff` are configurable on the client.

**3. Retry *then* degrade.** The retry lives inside the ClubElo fetch. On exhaustion it raises
`ClubEloError` **unchanged** — so the ingest layer's graceful degradation (ADR-010: keep
last-known Elo, non-fatal) is the final backstop. Two layers: retry rides out a blip;
degradation catches a genuine outage. Refresh never fails.

**4. Injectable sleep.** The `sleep` function is injected (default `time.sleep`), so tests
pass a no-op — instant runs, and they can assert the backoff was called the right number of
times with the right delays.

**5. A reusable helper.** The retry is written as a small, source-agnostic helper (not
ClubElo-specific), so the **required FPL client** can adopt it later (a backlog item). This
sprint applies it only to ClubElo — the source Tony actually hit.

**Not in scope:** a circuit breaker, a caching layer, async/parallel retries, or changing the
graceful-degradation behaviour.

---

### 🧪 Worked example (pressure-testing — simulated before code)

The proposed classification + retry loop, run across three scenarios (injected no-op sleep):

| Scenario | Outcome |
|---|---|
| `502, 502, 200` (Tony's case) | ✅ succeeds on **attempt 3**; waited `[0.5, 1.0]`s |
| `404` (permanent) | fails after **1 attempt** — no retries |
| `502 × 3` (real outage) | exhausted after 3 → `ClubEloError` → graceful degradation keeps last-known Elo |

Confirms all three behaviours *before* touching the client: transient rides out the blip,
permanent fails fast, and a true outage still falls through to the existing degradation.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** A momentary ClubElo blip no longer loses the Elo refresh (Tony's exact
  problem); the existing degradation is preserved as the backstop; the helper is reusable for
  the FPL client. No new dependency.
* **Negative / Trade-offs:** A genuine outage now takes slightly longer to fall back (up to
  ~1.5s of backoff) before degrading — a small, bounded cost. Retry is not a cache: if ClubELo
  is down for the whole window, we still degrade (as today).
* **Risks & Mitigations:**
  - *Retrying a permanent error* → classification fails 4xx fast (a test covers it).
  - *Slow tests* → injected `sleep`; tests assert it without waiting.
  - *Masking a real outage / hanging* → bounded retries, then degrade — never hangs.

---

### 🛠 Implementation & Migration
* **Components Affected:** `EloClient.get_elo_csv` (wrap the fetch in the retry helper), a small
  reusable retry helper, Docs. Graceful degradation in `ingest` is **unchanged**.
* **Action Items:**
  - [x] Record the design + worked example (US-058)
  - [ ] Implement the retry helper + apply to ClubElo + tests (US-059)
  - [ ] (Backlog) apply the same helper to the FPL client (required source)

---

### 🔄 Review & Reconsideration
* **Review Date:** If ClubElo reliability changes materially, or FPL transient failures appear.
* **Triggers for Reconsideration:**
  - [ ] Want the FPL client (fatal on failure) to retry too → apply the helper.
  - [ ] Transient outages last longer than the backoff window → consider a cache/longer policy.

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-058 (this), US-059
- **External Docs:** [ADR-010 (ClubElo — external source + graceful degradation)](./ADR-010-clubelo-external-source.md) · [Sprint 019](../05_Sprints/Sprint19.md)
