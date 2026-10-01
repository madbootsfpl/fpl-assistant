# ADR-342 — The limiter forgets what cannot matter

**Date:** 2026-10-01
**Status:** Accepted
**Found by:** the architecture review (`docs/00_Project/REVIEW_2026-10.md`, §5) — the one new finding
**Builds on:** ADR-256 (the rate limit), ADR-305 (the admin door)

---

## Context

`RateLimiter` keeps a sliding window per `(caller, path-rule)`. Expired timestamps were popped from each
deque on access — but **the dictionary entry itself was never removed**. `forget()` exists and is
documented *"for tests. Production never calls it"*; verified, nothing in `src/` calls it.

⚠️⚠️ **The key begins with `caller()`, which returns the left-most `X-Forwarded-For` value** — and the
module's own docstring already says that header is *"trivially spoofed by anyone talking to the service
directly"*, recorded there so nobody mistakes the limiter for authentication.

Put those two facts together and they say something neither says alone:

> 🔴 A caller sending a **fresh forged header per request** opened a brand-new bucket every time. The
> table grew without bound — **and no rate limit applied**, because a new bucket is an empty one.

⭐ *The spoofability was known and written down. The unbounded table was known to be a table. Nobody had
put them next to each other.*

## Decision

**Sweep buckets that can no longer affect anyone's limit. Never evict one that can.**

A sweep runs at most once per `SWEEP_SECONDS` (60), brought forward when the table passes `MAX_BUCKETS`
(10,000) — ⭐ time-based so an idle service does no work, size-based so a burst cannot outrun the clock.

### ⭐⭐ The invariant is the whole design

A bucket is removed **only when its newest hit is already older than that bucket's own window** — which is
exactly the state in which the next `check()` would drain it to empty anyway. So the sweep is
behaviour-preserving by construction, not by care.

⚠️⚠️ **And a table still over `MAX_BUCKETS` after sweeping is left alone.** The tempting next line is to
evict the oldest live buckets to enforce the cap. That would hand an attacker a better weapon than the one
being taken away: *flood the table, and everyone else's limit resets.* ⭐ **A memory fix that becomes a
rate-limit bypass is worse than the leak it closes.** Being over the cap after a sweep means real
concurrent traffic, and the honest response is to carry it.

### Tested, and mutation-tested

| test | catches |
|---|---|
| `test_a_forged_caller_header_cannot_grow_the_table_forever` | the leak — 2,000 vs 40,000 one-shot callers must not give a proportional table |
| `test_the_sweep_never_drops_a_bucket_that_is_still_limiting` | the bypass — a 20,000-caller flood inside a victim's window must not reset it |
| `test_sweeping_does_not_change_what_the_limiter_allows` | drift — identical decisions with sweeping on and effectively off |

⭐ **The first test asserts a ratio, not a size.** A sweep runs at most once a minute, so a bounded amount
of already-stale rubbish is always waiting for the next one — ⚠️ *an exact-size assertion would be testing
the sweep interval, which is a tuning number, rather than boundedness, which is the fix.* The first draft
asserted a size, failed at 79 buckets against 59 live, and was wrong.

Mutants: removing the `_sweep` call fails the first; making the sweep drop every bucket fails the second
**and** the pre-existing `test_the_window_slides_rather_than_resetting`.

## Consequences

✅ Steady-state memory is bounded by traffic inside one window rather than by every caller ever seen.
⭐ The rate-limit bypass is unchanged and still open — a forged header still gets its own bucket, so a
determined caller still evades the limit. ⚠️ *That is ADR-256's accepted position* (**"a cost control, not
a security boundary"**) and this ADR does not reopen it; closing it needs identity, which is ADR-259.

📌 Severity was held at **medium**, not high: the process restarts on Render's scale-to-zero, and there is
no data behind the limiter to leak. ⚠️ It would matter more on an always-on instance — which is the one
setting the Dockerfile already describes changing later.
