# Sprint 019: ClubElo Resilience (retry-with-backoff)

**Dates:** 2026-08-03
**Status:** ✅ Complete
**Capacity:** ~2 working sessions (a focused robustness improvement)
**Carried Over:** None (Sprint 018 closed clean)

---

### 🔎 Verified at planning (per the standing lesson)

Tony hit repeated ClubElo failures on refresh: `502 Server Error: Bad Gateway`. A probe
diagnosed it:

- **The 502 was transient.** `http://api.clubelo.com/2026-08-03` (the exact failing URL)
  now returns **200 OK** with valid CSV (Arsenal 2063.76); other dates 200 too. ClubElo is a
  free hobby API that occasionally has gateway hiccups.
- **Not an http/https or date issue.** ClubElo is **http-only** (https times out); the
  future-looking date returns valid data. So the URL and code are correct.
- **Our graceful degradation already worked** (ADR-010) — it kept last-known Elo, stayed
  non-fatal, and the refresh completed. Nothing is broken.

**The gap:** a *single* transient blip loses the whole Elo refresh for that run, even though a
retry seconds later succeeds. A small **retry-with-backoff** closes it. **No new dependency.**

This sprint is **Tony's Sprint 018 reflection** — a real issue he hit twice.

---

### 🧭 Architecturally, what's new — retry *then* degrade

Today the ClubElo fetch is one-shot: any error → `ClubEloError` → the ingest layer degrades
(keeps last-known Elo). We insert a **retry** step *before* the degrade:

```
attempt 1 → 502  → wait 0.5s ↘
attempt 2 → 502  → wait 1.0s ↘         (transient errors only)
attempt 3 → 200  → success ✓
                    …or, if all fail → ClubEloError → graceful degradation (unchanged)
```

Two layers of resilience, each doing its job: **retry** rides out a momentary blip;
**degradation** (ADR-010) still catches a genuine outage so refresh never fails. Only
*transient* errors retry — a permanent error (a 4xx) fails fast, no pointless waiting.

The retry is written as a **small reusable helper** so the required FPL client could adopt it
later (a backlog item) — but this sprint applies it only to ClubElo, the source Tony hit.

---

### 🎯 Sprint Goal

**Objective:** Make the ClubElo fetch survive a transient failure — retry a few times with a
short backoff on 502/503/504, timeouts and connection errors, before falling back to
last-known Elo — so a momentary blip no longer loses the Elo refresh.

#### Success Criteria
- [x] Retry approach agreed (**ADR-020**) before code
- [x] Transient errors (502/503/504, `Timeout`, `ConnectionError`) **retry**; permanent (4xx)
      **fail fast** (no retry)
- [x] A configurable policy: default 2 retries (3 attempts) with exponential backoff (0.5s, 1s)
- [x] After all retries fail → `ClubEloError` (unchanged) → existing graceful degradation
- [x] The backoff `sleep` is injectable, so tests are instant and can assert the retries
- [x] The final-failure message reports the attempt count
- [x] Existing behaviour unchanged on first-attempt success (no extra latency)
- [x] Tests cover: succeed-after-retry, permanent-no-retry, exhausted-then-error (offline)
- [x] **Manual smoke test** run before the sprint is closed (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-058 | Agree the retry approach (**ADR-020**): transient vs permanent error classification, retry count + backoff, injectable sleep, placement (retry *then* degrade), reusable helper — pressure-test with a worked example | Critical | ✅ Complete | 0.5 session |
| US-059 | Implement retry-with-backoff in the ClubElo fetch (reusable helper); classify errors; inject sleep. Tests (succeed-after-retry / permanent-no-retry / exhausted) + smoke test | High | ✅ Complete | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-020 recorded + added to the ADR index — _US-058_
- [ ] Update Architecture doc (resilience note: retry then degrade; changelog) — _US-058_
- [ ] Update Handbook Ch 23 (External Data) — add the retry layer — _US-059_
- [ ] (Backlog) apply the same retry helper to the FPL client (required source) — _US-059_

---

### ✅ Definition of Done (this sprint)

The same 3-part DoD that has held for eighteen sprints — a story isn't done until:
1. **Automated tests pass** (and cover the new logic).
2. **Manual smoke test done** — run the real command, eyeball the output, check `--help`.
3. **Documentation updated & checked** — Handbook, Architecture, ADR + index, README,
   sprint board + PROJECT_STATUS, as applicable (Charter Documentation Rules).

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Retry-with-backoff for the ClubElo fetch | The FPL client retry (backlog — required source) |
| Transient vs permanent error classification | A full circuit-breaker / caching layer |
| Injectable sleep for testability | Changing the graceful-degradation behaviour (kept) |
| A reusable retry helper | Async / parallel retries |

**External Dependencies:**
- [ ] `requests` (already used); **no new dependency** (verified above)

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Retrying a permanent error wastes time | Med | Classify: only 502/503/504 + timeouts/connection retry; 4xx fails fast |
| Tests become slow (real sleeps) | Med | Inject the `sleep` callable; tests pass a no-op and assert it was called |
| Retry masks a real outage | Low | Bounded (2 retries); after that, degrade exactly as today — never hangs |
| First-attempt success pays a latency cost | Low | Backoff only happens *between* failed attempts; success returns immediately |
| Over-engineering (circuit breakers, etc.) | Low | Scope is a bounded retry; anything more is explicitly out |

---

### 🗝️ Gating decision (US-058 → ADR-020)

Settle before building — **pressure-test with a worked example** (per the standing lesson).
Proposed answers (Tony to confirm/redirect):

1. **Transient (retry):** HTTP **502 / 503 / 504**, `requests.Timeout`, `requests.ConnectionError`.
   **Permanent (fail fast):** 4xx and anything else — retrying won't help.
2. **Policy:** default **2 retries** (3 attempts total); **exponential backoff** base 0.5s
   (waits 0.5s, then 1.0s). Both configurable on the client.
3. **Placement:** inside the ClubElo fetch; on exhaustion raise `ClubEloError` — so the
   existing graceful degradation (keep last-known Elo) is unchanged. **Retry then degrade.**
4. **Testability:** the `sleep` function is injected (default `time.sleep`); tests pass a
   no-op and assert the backoff was called the right number of times.
5. **Reusable:** a small helper (not ClubElo-specific) so the FPL client can adopt it later.

**Worked example to verify at the gate:** three scenarios — (a) `502, 502, 200` → succeeds on
attempt 3 (Tony's case fixed); (b) `404` → no retry, immediate `ClubEloError`; (c) `502 × 3`
→ exhausted → `ClubEloError "after 3 attempts"` → graceful degradation keeps last-known Elo.
Confirms the classification *and* that degradation still backstops a true outage.

---

### 📝 Session Progress Log

#### Session 1 — 2026-08-03 (US-058: ADR-020 — retry-with-backoff)
* **Completed:** Recorded **ADR-020**: retry transient errors (502/503/504, `Timeout`,
  `ConnectionError`); fail fast on permanent (4xx). Default 2 retries (3 attempts),
  exponential backoff 0.5s→1.0s, configurable. Retry lives in the ClubElo fetch; on exhaustion
  raise `ClubEloError` unchanged → existing graceful degradation (ADR-010) is the backstop —
  **retry then degrade**. Injectable `sleep` for instant, assertable tests; a reusable helper
  (FPL client can adopt later). **Pressure-tested by simulation before code:** (a) `502,502,200`
  → success on attempt 3, waited [0.5, 1.0]s; (b) `404` → fails after 1 (no retry); (c) `502×3`
  → exhausted → degrade. Added to the ADR index; Architecture §12 changelog. US-058 **complete**
  — no feature code.
* **Manual smoke test:** N/A (docs-only gate story). The simulation *is* the verification.
* **Docs touched:** ADR-020 (new) + index, Architecture changelog, Sprint19 board, PROJECT_STATUS.
* **Issues / Blockers:** None. (ClubElo diagnosed: transient 502; API up now; degradation held.)
* **Next Steps:** US-059 — implement the retry helper + apply to ClubElo + tests.

#### Session 2 — 2026-08-03 (US-059: implement retry-with-backoff)
* **Completed:** New reusable `src/api/retry.py` — `is_transient` (502/503/504, `Timeout`,
  `ConnectionError`) + `with_retry(fetch, retries=2, backoff=0.5, sleep=time.sleep)`
  (exponential backoff, re-raises otherwise). `EloClient` gained `retries`/`backoff`/`sleep`;
  `get_elo_csv` wraps its GET in `with_retry` and, on final failure, wraps in `ClubEloError`
  with an **accurate** attempt count (`retries+1 if is_transient else 1`). **+4 tests → 194
  total, all green** (is_transient classification; retry-then-succeed with `sleeps==[0.5,1.0]`;
  permanent-no-retry `sleeps==[]`; exhausted "after 3 attempt(s)"); updated the existing
  network-error test to inject a no-op sleep. US-059 **complete** — Sprint 019 done.
* **Manual smoke test:** ✅ Real `refresh` still works (happy path intact) — and *live*, ClubElo
  read-timed-out this run, so the retry fired ("after 3 attempt(s)") then degraded gracefully
  (kept last-known Elo, refresh completed). Forced-502 path: 3 attempts, backoff `[0.5, 1.0]s`,
  then `ClubEloError` → degrade.
* **Honest note:** on a *full* outage, retry adds latency (up to `timeout × attempts` ≈ 30s
  with a 10s timeout × 3) before degrading. Bounded, only-on-failure, tunable — documented in
  Handbook Ch23. A retry helps a blip, not a sustained outage (which still degrades).
* **Docs touched:** Handbook Ch23 (retry-then-degrade section + ADR link), Sprint19 board,
  PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** Sprint 019 review & retrospective.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** Both stories — US-058 (ADR-020) and US-059 (the retry helper + ClubElo).
  A momentary ClubElo blip no longer loses the Elo refresh: transient errors retry with
  backoff before falling back to last-known Elo. Tests grew 190 → **194**. **No new
  dependency.** The first purely-robustness sprint.
* **Carried Forward:** None. Backlog: apply the same retry helper to the FPL client (the
  required source, where a failure is fatal); consider a shorter ClubElo timeout to bound
  full-outage latency.
* **Key Artifacts / Decisions:** ADR-020 (transient/permanent classification, retry then
  degrade); reusable `src/api/retry.py`; `EloClient` retry params; Handbook Ch23 section.

#### Retrospective
* **What Went Well?**
  - **A real bug report → a resilience layer.** Tony's ClubElo 502s were diagnosed
    (transient, API up, degradation held) and closed with a bounded retry.
  - **Diagnose before fixing.** The probe showed nothing was broken — the fix is an
    *improvement* to a working system, scoped precisely (retry the right errors only).
  - **A live confirmation.** During the smoke test ClubElo actually timed out — the retry
    fired ("after 3 attempts") then degraded gracefully. The feature proven in the wild.
  - **Layered resilience.** Retry (blip) + degradation (outage) — each doing its own job;
    refresh still never fails. DoD held (19th sprint).
* **What Could Be Improved?**
  - Full-outage latency grew (~30s with a 10s timeout × 3) — bounded and tunable, but a
    shorter ClubElo timeout would trade less waiting for the same resilience (backlog).
  - The retry helper is reusable but only ClubElo uses it — the FPL client (fatal on
    failure) arguably needs it more (backlog).
* **Lessons Learned?**
  - Diagnose a "bug" before fixing — sometimes the system is fine and the fix is a
    hardening, scoped accordingly.
  - Classify errors: retry only what a retry can fix; fail fast on the rest.
  - Inject time (`sleep`) so time-based logic is testable instantly *and* assertable.
  - Document the trade-off (latency on outage), don't hide it — same honesty as a metric caveat.
* **Action Items for Next Sprint (020):**
  - [ ] Consider: apply the retry helper to the FPL client; a combined defensive-value view;
    a shared table renderer; or another backlog pick — check first.
  - [ ] Keep diagnose-then-fix + gate + 3-part DoD.

---

**Proposed follow-on (Sprint 020):** apply the retry helper to the FPL client, a combined
defensive-value lens, a shared table renderer (tech debt), or another backlog pick.

**Completion Date:** 2026-08-03
**Final Notes:** The project's first robustness sprint — from Tony's real ClubElo 502s to a
bounded retry-then-degrade, confirmed live when ClubElo timed out mid-smoke-test. Sprint
outcome: **Successful** — 2/2 stories, zero roll-over, DoD held.
