# ADR-280 — Load, not people

**Date:** 2026-09-24
**Status:** Accepted
**From:** the owner — *"I want to see the distribution & number using the apps on the different
platforms, the reason, to make sure that we are scaled enough to support. **I am not interested in
personal information**."*
**Follows:** ADR-100 (the web's anonymous analytics), ADR-259 (accounts, still parked)

---

## Context

ADR-278 established there was nothing: the mobile app sent no telemetry, and the desktop's tester roster
runs entirely on the email allow-list a phone does not have.

⭐ **The brief is narrower than "who is testing", and better for it.** *Are we scaled enough* is answered
by **load**, not by identity — and the owner said so before anyone had to ask.

## Decisions

**Three values ride on every request, and they are the whole of it.**

| | |
|---|---|
| `platform` | `ios` · `android` · `web` — ⭐ the distribution asked for |
| `version` | which build — ⚠️ *an old build in the wild is invisible until something breaks on it* |
| `install` | a random id, ⚠️ **tied to nothing** |

⭐ **The install id earns its place**: *"1,400 requests"* does not answer *"how many people"*, and
counting devices needs something stable. It is random, never derived — ⚠️ *an identifier computed from
something personal is that personal thing in a costume* — and it can be reset.

**⚠️⚠️ What is never recorded, each for a reason:**

* **The manager id.** The API receives it on four endpoints. ⭐ *The difference between "twelve Android
  devices" and "Tony opened Trending" is the whole of the promise here*, and the join is what would break
  it.
* **The caller's IP**, which the rate limiter next door *does* read — ⚠️ *an IP is personal data in a way
  a random install id is not.*
* **The request body.** Squads, player ids, feedback text.

**It reuses the web's `events` table** (ADR-100) rather than inventing a second system — ⭐ *one place to
read, whichever surface a tester used* — with the install id in the same `anon_id` column the web's
random returning-user id already uses.

**Off unless configured, and stoppable without a deploy.** No store, no thread, no write; `FPL_USAGE_OFF`
halts it — ⭐ *a thing that records people should be possible to stop without a deploy.*

**⚠️ Recorded outside the rate limiter, deliberately** — *a capacity measure that cannot see the traffic
it refused is the one measure you need when refusing.*

## ⚠️ I put it in the request path first, and it was wrong twice

The identity began as `await Telemetry.installId()` **inside** the HTTP client — a storage read on every
request. ⭐ *Telemetry that can slow the app is telemetry that will be blamed for it*, and it also made
the API client depend on a plugin: **eighteen tests with nothing to do with telemetry began failing** on
*"Binding has not yet been initialized"*.

⭐⭐ **Telemetry that can break a test suite has already cost more than it measures.** `main()` now
resolves it once before the first frame and the client reads a plain field.

## ⚠️ And the privacy sweep matched its own docstring

The source guard fired on the module's own documentation, which names `X-Forwarded-For` precisely to say
the recorder must not read it. ⭐ *A guard that fires on the prose explaining the guard teaches people to
delete the prose* — the same trap as ADR-261's Dockerfile comments. It now strips docstrings and comments
via `ast` before sweeping.

## Verification

* **8 Python tests** — ⭐ the **negative** ones are the point: no personal field in a row, the middleware
  reading only three headers with an IP present on the request, off by default, stoppable, and a failing
  recorder that cannot take a request down.
* **A source sweep** that fails the day somebody adds the join, **proved** by adding a `manager_id` and
  watching both it and the behavioural test fail.
* **4/4 mutations killed** — ⚠️ three only after the harness was rewritten to a file, having silently
  failed to apply from a shell heredoc. *The recurring fault of this project's week.*
* **11 Dart tests**: the install id is minted once, is random, is resettable, and the headers carry
  exactly three keys and no manager id. Plus a guard that `kAppVersion` matches `pubspec.yaml`.
* 2,596 Python · 274 Dart.

📌 **Still parked:** accounts (ADR-259) and therefore subscriptions. ⭐ Nothing here blocks either — and
*usage history cannot be backfilled*, which is the one reason to start recording before the question is
asked rather than after.
