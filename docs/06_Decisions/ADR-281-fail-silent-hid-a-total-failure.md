# ADR-281 — Fail-silent hid a total failure

**Date:** 2026-09-24
**Status:** Accepted
**From:** the owner, reading the new panel — *"all I am seeing under Platform is web with 66 under
Devices 1000 Requests and 4703 Slowest 5%"*
**Fixes:** ADR-280 (which recorded nothing at all)

---

## What happened

`FPL_STORE_URL` is a **full table URL** — `https://…/rest/v1/squads` — and the web app derives the events
table as its *sibling*: strip the last segment, append `events`.

The API **reimplemented** that rather than matching it, appending `/rest/v1/events` to the whole thing:

```
https://…/rest/v1/squads/rest/v1/events        ← 404, every time
```

⭐⭐ **And the writer is fail-silent by design**, so every write 404'd and nothing complained. ADR-280
shipped, the owner configured it, redeployed, looked — and the panel read exactly like *"nobody has used
the app yet."*

⚠️ **Indistinguishable from success by anyone, including the two people looking at it.**

## ⚠️ Two mistakes, and the second is the one that mattered

**I reimplemented a derivation instead of matching the one that worked.** The correct rule was eleven
lines away in `analytics.py`. It could not simply be imported — `src/web_streamlit` is excluded from the
API image (ADR-261) — but *it could have been read.* ⭐ *Two copies of one rule need a test that they
agree, or one of them is already wrong and nobody knows.* That test exists now.

**And fail-silent was applied in one direction too many.** The rule from ADR-100 is right and stands:
*a lost event never matters; a broken request would.* ⭐ **But silence towards the request is not the same
as silence towards the owner**, and the two had been collapsed into one.

## Decisions

**`events_url()` matches the web app exactly**, with a test asserting both derive the same URL from the
same input — ⚠️ *and a second test naming the specific shape of the failure*, because a test that says
what went wrong is worth more than one that says what should be true.

**A 404 is a failure.** ⚠️ It does not raise, which is precisely how this went unnoticed: the write
"succeeded" as far as `requests` was concerned. The status code is now checked.

**`/health` reports the write status** — `off` · `never` · `ok` · `failing (404)`. ⭐ Enough to tell *not
configured* from *configured and broken*, which is the distinction that cost an afternoon. No URL, no
key, no payload — ⭐ *one word.*

📌 This is ADR-239's lesson arriving somewhere new: *a bare `{ok: true}` cannot tell this API from a
captive portal.* A bare empty panel cannot tell a quiet week from a broken pipe.

## Verification

* **18 Python tests**, including the URL agreement, the doubled-path shape, a 404 recorded as failing,
  and health distinguishing unconfigured from broken.
* **Proved by re-breaking**: restoring the original derivation fails two tests.
* ⚠️ **A contract guard fired correctly and then broke on formatting** — the Dart health fixture is pinned
  from the Python side, and `dart format` wrapped the literal so the pattern stopped matching. ⭐ *A guard
  that breaks when the formatter runs is a guard people learn to edit rather than trust* (ADR-269's
  help-link regex, again). Made whitespace-tolerant and re-proved against a real drift.
* 2,606 Python · 274 Dart.
