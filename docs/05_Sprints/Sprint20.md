# Sprint 020: Resilience Round 2 — effort scales with importance

**Dates:** 2026-08-03
**Status:** ✅ Complete
**Capacity:** ~2 working sessions (a focused resilience pass on both clients)
**Carried Over:** None (Sprint 019 closed clean)

---

### 🔎 Verified at planning (per the standing lesson)

Two live facts, probed now:

- **FPL is healthy** — `bootstrap-static` returns **200 in 0.1s**. So adding retries costs
  **nothing** on the happy path; it only helps on a rare blip.
- **ClubElo is still down** (a 2nd day) — read timeouts. And a *healthy* ClubElo returns in
  ~1–2s, so a **5s timeout** is a safe 2.5× margin (won't false-timeout a working ClubElo).
- **The live pain:** with the Sprint-019 retry (2 retries × 10s timeout), a *sustained*
  ClubElo outage makes every `refresh` wait **~31s** before degrading — up from ~10s.

**No new dependency** — reuses `src/api/retry.py` (Sprint 019). This sprint is Tony's Sprint
019 retro pick, sharpened by the ongoing outage.

---

### 🧭 Architecturally, what's new — a principle: retry effort scales with how much the source matters

Sprint 019 added retry to ClubElo. This sprint makes the *policy* deliberate and applies it to
both clients:

| Source | Matters how much? | Policy |
|---|---|---|
| **FPL** | **Required** — a failure is *fatal* (no degradation) | **Try hard:** 2 retries (3 attempts), 10s timeout |
| **ClubElo** | **Best-effort** — a failure degrades gracefully | **Fail fast:** 1 retry (2 attempts), **5s** timeout |

The rule: **the more a source matters, the harder we try; the more optional it is, the faster
we give up.** FPL (fatal on failure) earns extra attempts; ClubElo (optional) shouldn't hold up
refresh — so a down ClubElo now degrades in **~10.5s**, not ~31s, while still retrying a genuine
blip once. Both use the *same* `with_retry` helper — only the numbers differ.

**Part 1 (ClubElo):** shorter timeout (5s) + fewer retries (1) → fast, bounded fallback.
**Part 2 (FPL):** apply the retry helper to `_get_json` → a momentary FPL blip no longer kills
the whole refresh (previously any FPL failure was fatal on the first attempt).

---

### 🎯 Sprint Goal

**Objective:** Apply a deliberate, importance-scaled retry policy to both clients — FPL (the
required source) retries harder; ClubElo (best-effort) fails fast — so a momentary FPL blip is
survived and a sustained ClubElo outage degrades in ~10s instead of ~31s.

#### Success Criteria
- [x] Policy agreed (**ADR-021**) before code
- [x] **FPL** `_get_json` retries transient errors (2 retries) via the shared helper; on
      exhaustion still raises `FplApiError` (required source — fatal, no degradation)
- [x] **ClubElo** uses a **5s** timeout and **1** retry → a sustained outage degrades in ~10s
- [x] A healthy source is unaffected (first-attempt success, no added latency)
- [x] Both clients reuse `src/api/retry.py` (no duplicated retry logic)
- [x] The `sleep` is injected on both, so tests stay instant and assertable
- [x] Existing ClubElo retry tests updated for the new (fail-fast) defaults
- [x] Tests cover FPL retry (succeed-after-retry / permanent / exhausted) + ClubElo timing
- [x] **Manual smoke test** run before the sprint is closed (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-060 | Agree the importance-scaled retry policy (**ADR-021**): FPL retries hard (2, 10s), ClubElo fails fast (1, 5s), both via the shared helper; FPL stays fatal on exhaustion — pressure-test with worst-case timings | Critical | ✅ Complete | 0.5 session |
| US-061 | Apply it: `FplClient` gains retry (reuse `with_retry`; `retries`/`backoff`/`sleep` params; wrap `_get_json`); `EloClient` defaults → 5s timeout, 1 retry. Update the Sprint-019 ClubElo tests; add FPL retry tests + smoke test | High | ✅ Complete | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-021 recorded + added to the ADR index — _US-060_
- [ ] Update Architecture doc (resilience policy: effort scales with importance; changelog) — _US-060_
- [ ] Update Handbook Ch 23 (External Data) — the importance-scaled policy — _US-061_
- [ ] A `config.CLUBELO_TIMEOUT` (5s) constant, so the budget is explicit — _US-061_

---

### ✅ Definition of Done (this sprint)

The same 3-part DoD that has held for nineteen sprints — a story isn't done until:
1. **Automated tests pass** (and cover the new logic).
2. **Manual smoke test done** — run the real command, eyeball the output, check `--help`.
3. **Documentation updated & checked** — Handbook, Architecture, ADR + index, README,
   sprint board + PROJECT_STATUS, as applicable (Charter Documentation Rules).

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| FPL client retry via the shared helper | A circuit breaker (skip a known-down source) — backlog |
| ClubElo fast-fail (5s timeout, 1 retry) | Changing FPL's fatal-on-failure behaviour |
| One reusable retry policy, two callers | Async / parallel fetching |
| A `CLUBELO_TIMEOUT` config constant | An alternate Elo source |

**External Dependencies:**
- [ ] `requests` + `src/api/retry.py` (already present); **no new dependency**

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Shorter ClubElo timeout false-times-out a slow-but-healthy ClubElo | Low | Healthy ClubElo responds in ~1–2s; 5s is a 2.5× margin (verified) |
| FPL retry slows a real FPL outage (~30s before fatal) | Low | FPL is very reliable (0.1s); a rare cost for surviving a blip; bounded |
| Changing ClubElo defaults breaks Sprint-019 tests | Med | Update those tests to the new fail-fast numbers (part of US-061) |
| FPL retry masks a real outage | Low | Bounded (2 retries), then `FplApiError` — refresh fails clearly, as today |
| Over-engineering (circuit breaker) | Low | Explicitly out of scope; this is bounded retry + tuning only |

---

### 🗝️ Gating decision (US-060 → ADR-021)

Settle before building — **pressure-test with a worked example** (per the standing lesson).
Proposed answers (Tony to confirm/redirect):

1. **The principle.** Retry effort scales with source importance. **Required (FPL):** try hard.
   **Best-effort (ClubElo):** fail fast.
2. **FPL policy.** 2 retries (3 attempts), 10s timeout, via `with_retry`. On exhaustion →
   `FplApiError` (still fatal — FPL has no degradation, and shouldn't).
3. **ClubElo policy.** 5s timeout, 1 retry (2 attempts) → worst case ~10.5s. Still retries a
   genuine blip once (preserves Sprint 019's intent), but a sustained outage degrades fast.
4. **One helper.** Both clients call the same `with_retry`; only the `retries`/`timeout`
   numbers differ — no duplicated logic.
5. **Config.** A `CLUBELO_TIMEOUT = 5` constant makes the best-effort budget explicit.

**Worked example to verify at the gate:** worst-case timings — FPL outage: 3 × 10s ≈ 30s then
fatal (rare, acceptable); ClubElo outage: 2 × 5s + 0.5 ≈ 10.5s then degrade (down from ~31s).
And FPL blip `502, 200` → survives on attempt 2 (was fatal). Confirms the policy does what we
claim before any code.

---

### 📝 Session Progress Log

#### Session 1 — 2026-08-03 (US-060: ADR-021 — importance-scaled retry)
* **Completed:** Recorded **ADR-021**: retry effort scales with source importance. **FPL**
  (required, fatal) → 2 retries, 10s, via the shared helper; still `FplApiError` on exhaustion.
  **ClubElo** (best-effort) → 1 retry, **5s** timeout → degrades in ~10.5s (was ~31s). One
  helper, two policies; `CLUBELO_TIMEOUT = 5` constant. **Pressure-tested with the real
  `with_retry`:** FPL blip `502,200` → survives on attempt 2 (was fatal); FPL outage `503×3`
  → exhausted → fatal; ClubElo old 10s/2 ≈ 31.5s vs new 5s/1 ≈ 10.5s. Added to the ADR index;
  Architecture §12 changelog. US-060 **complete** — no feature code.
* **Manual smoke test:** N/A (docs-only gate story). The simulation *is* the verification.
* **Docs touched:** ADR-021 (new) + index, Architecture changelog, Sprint20 board, PROJECT_STATUS.
* **Issues / Blockers:** None. (FPL healthy 0.1s; ClubElo still down — retry policy tuned for it.)
* **Next Steps:** US-061 — apply retry to `FplClient`; tune `EloClient` (5s/1); update tests.

#### Session 2 — 2026-08-03 (US-061: apply the policy to both clients)
* **Completed:** **FPL** — `FplClient` gained `retries`/`backoff`/`sleep`; `_get_json` wraps its
  GET in `with_retry` (retries=2) and reports an accurate attempt count; exhaustion still raises
  `FplApiError` (fatal — no degradation). **ClubElo** — `config.CLUBELO_TIMEOUT = 5`; `EloClient`
  defaults → 5s timeout, 1 retry (fail fast). Both reuse the one helper; only the numbers differ.
  **+3 net tests → 197 total, all green** (FPL retry-then-succeed `[0.5,1.0]` / permanent /
  exhausted; updated the two Sprint-019 ClubElo tests to the fail-fast numbers; injected sleep on
  the FPL network-error test). US-061 **complete** — Sprint 020 done.
* **Manual smoke test:** ✅ Real `refresh` — ClubElo now degrades after **2 attempts / 5s
  timeout**, whole refresh **10.9s** (was ~31s — the live pain fixed). Forced FPL blip `502,200`
  → **survived** (was fatal). Existing happy paths unaffected.
* **Docs touched:** Handbook Ch23 (importance-scaled policy + ADR link), Sprint20 board,
  PROJECT_STATUS.
* **Issues / Blockers:** None. (ClubElo still down — but refresh is now fast about it.)
* **Next Steps:** Sprint 020 review & retrospective.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** Both stories — US-060 (ADR-021) and US-061. An importance-scaled retry
  policy applied to both clients via the one Sprint-019 helper: **FPL** retries hard (2, 10s)
  and survives a blip that was previously fatal; **ClubElo** fails fast (1 retry, 5s) so a
  sustained outage degrades in ~10s not ~31s. Tests grew 194 → **197**. **No new dependency.**
* **Carried Forward:** None. Backlog: a circuit breaker (skip a known-down source across runs)
  if ClubElo stays down for days; an alternate Elo source.
* **Key Artifacts / Decisions:** ADR-021 (effort scales with importance); FPL retry;
  `config.CLUBELO_TIMEOUT`; Handbook Ch23 policy table.

#### Retrospective
* **What Went Well?**
  - **The Sprint-19 design paid off immediately.** `with_retry` was written source-agnostic —
    so this sprint was "call the same helper with different numbers", no new machinery.
  - **A principle, not just numbers.** "Effort scales with importance" is a reusable rule any
    future client can follow — and it fixed a real thing (FPL blip fatal; ClubElo 31s wait).
  - **Fixed the live pain, proven live.** The real refresh dropped from ~31s to ~10.9s during
    the ongoing ClubElo outage; a forced FPL blip survived.
  - Both required-source resilience *and* best-effort speed, in one coherent pass. DoD held (20th).
* **What Could Be Improved?**
  - A truly-down ClubElo still costs ~10s per refresh — a circuit breaker would make it
    instant, but needs cross-run state (deferred, honestly).
  - FPL's fatal-after-retry path has no degradation (correct — it's required) but means a real
    FPL outage still fails refresh; nothing to do there, just noted.
* **Lessons Learned?**
  - Write a helper source-agnostic and a second use is nearly free.
  - Encode a *principle* in a decision, not just constants — it guides the next case.
  - Match the resilience budget to the stakes: try hard for what's required, fail fast for
    what's optional.
* **Action Items for Next Sprint (021):**
  - [ ] If ClubElo stays down, consider a circuit breaker; else a feature (combined defensive
    value) or tech debt (shared table renderer) — check first.
  - [ ] Keep diagnose-then-fix + gate + 3-part DoD.

---

**Proposed follow-on (Sprint 021):** a circuit breaker (if ClubElo persists), a combined
defensive-value lens, or a shared table renderer — checked first.

**Completion Date:** 2026-08-03
**Final Notes:** Resilience round 2 — one principle (effort scales with importance), two
policies, one helper. Fixed Tony's ~31s refreshes and made the required FPL source survive a
blip. Sprint outcome: **Successful** — 2/2 stories, zero roll-over, DoD held.
