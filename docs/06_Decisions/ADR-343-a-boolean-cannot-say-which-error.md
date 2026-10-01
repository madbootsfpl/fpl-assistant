# ADR-343 — A boolean cannot say which error

**Date:** 2026-10-01
**Status:** Accepted
**Found by:** the first run of `sql/feature_usage.sql` against live data
**Builds on:** ADR-280 (what telemetry may record), ADR-306 (a probe is not usage)

---

## Context

The usage query written during the architecture review was run for the first time on 2026-10-01. It
answered the product question it was written for — people open MadBoots to look at their own fifteen and
decide this week — and then surfaced something nobody was looking for:

| endpoint | failing |
|---|---|
| `squad/replacements` | **19.0%** |
| `squad/signals` | **14.7%** |
| `squad/my-team` | **5.2%** |

Roughly 41 real HTTP errors in front of nine people in eight days, against 0.0% on every Streamlit page.

⚠️⚠️ **And the table could not say which errors.** `record()` stored:

```python
ok=response.status_code < 400,
```

⭐⭐ **Two lines above, the same module formats that same status code into a log string** (`_last = …
f"failing ({response.status_code})"`). So the one field that would make a 19% failure rate diagnosable
was already in the function, used for something else, and discarded on the way to the table.

A 422, a 429, a 502 and a 500 all read as `ok=False`. Those need four different responses — and one of
them is *"nothing; that is an upstream having a bad day"*, which is a live possibility here, because
`/chatter`'s own docstring already records that **Reddit blocks datacentre IPs at times.**

🔴 *A failure rate you cannot attribute is a number that produces activity rather than a fix.*

## Decision

**Record the status code in `meta`, and change nothing else.**

```python
"meta": {"platform": platform or "unknown",
         **({"status": int(status)} if status is not None else {})},
```

### ⭐ Additive, and that is the whole design

**`ok` stays exactly as it was.** `admin.summarise()` reads it, every row ever written has it, and the
queries in `sql/feature_usage.sql` key on it. ⭐ *A column that rewrites what history means is not an
improvement to history.*

Both values come from one expression in the middleware, so they cannot disagree:

```python
ok=response.status_code < 400,
status=response.status_code,
```

### ⭐ In `meta`, not a new column

The `events` table is shared with the Streamlit app, which has no HTTP status to report. A column that is
null for half the rows invites the question of what null means. ⚠️ **Absent is clearer than null**, and a
`jsonb` says absent natively.

### 🔴 There is now a date in the data

Rows written before this deploy have **no** `status` key. ⚠️⚠️ *A query filtering on `status` silently
drops every row from before the fix*, which would make a long-standing failure look like it began the day
the field did — ⭐ the same shape of mistake as counting `/health` as usage (ADR-306).

So `sql/feature_usage.sql` was updated rather than merely extended: query 6 still keys on `ok` and reports
the codes beside it, and the new query 8 carries a **`covered_pct`** column saying what share of each
page's failures carry a code at all. 📌 *A breakdown that does not say how much of the window it covers is
a breakdown that will be read as the whole of it.*

### Privacy unchanged

An HTTP status says what the server did, never who asked. ADR-280's promise — platform, version, a random
install id, endpoint, duration, and nothing that identifies a person — is restated as a test against the
new key.

## Consequences

✅ The next run of query 8 says whether `signals` is our bug or Reddit's, and whether `my-team`'s 5.2% is
the over-budget 422 already fixed in build 39.

⏳ **It says nothing about the eight days already recorded.** Those rows are `ok=False` and will stay that
way. ⚠️ *The fix buys the next question, not this one* — which is the ordinary price of discovering a gap
by needing it.

📌 Four tests, all mutation-tested: a failure carries its code · the middleware passes the real one ·
`status` is absent rather than null when nobody has one · the new key is not a personal field.
