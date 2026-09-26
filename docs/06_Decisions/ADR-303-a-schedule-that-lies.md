# ADR-303 — A schedule that lies, and a screen that does not

**Date:** 2026-09-26
**Status:** ✅ **Built.**
**From:** the owner — *"do 1 now"*, choosing the smaller of the two options after asking what the *"7%
schedule"* was.

---

## The measurement

`.github/workflows/data.yml` declared `cron: "*/15 * * * *"` — ninety-six runs a day. Measured against the
Actions API on 2026-09-26:

| | |
|---|---|
| last 24 hours | **6 runs** against 96 implied — **6%** |
| last 7 days | **48 runs** against 672 — **7%** |
| real gaps | 2h27m · 2h55m · 3h14m · 5h10m · 5h41m |

⭐ GitHub deprioritises scheduled runs on free runners. ⚠️ `backfill.yml` is already **hourly** and
throttled just as hard, which is the evidence that matters here: **this is not a frequency problem that a
different frequency fixes.**

## What was actually wrong

⚠️⚠️ **Two things, and only one of them is the cadence.**

1. **The file claimed a cadence the platform never honoured.** ⭐ *A schedule the platform ignores is a
   schedule that lies in the documentation as well as in the file* — and the person it misleads is
   whoever reads it next wondering why the prices are old.
2. **The app implied a freshness it did not have, and could not have said otherwise.** The staleness
   banner fires only when a **completed gameweek has no rows**. ⭐⭐ *A five-hour-old row is still a row*,
   so a board sitting on yesterday's prices looked identical to one refreshed a minute ago.

## What shipped

**The cron is hourly**, with the measurement written beside it — ⚠️ **this changes the documentation, not
the data**, and the comment says so. Fixing freshness means driving the tick from something that keeps
time and using GitHub as the worker; that has a token in it and was deliberately not taken here.

**The answer carries `age_minutes`**, and ⚠️⚠️ **deliberately not inside `behind`.** `behind` means *a
completed gameweek has no rows*; age means *the last refresh was a while ago*. ⭐ *Two questions, two
fields* — merging them is exactly the mistake ADR-301 caught a day earlier, where a schema lag would have
reached nine testers as *"your data is broken"*.

**The pitch says it quietly**: `5h old`, in the header, at 10.5pt in white38 — ⚠️ *no colour, no icon, no
border.* The banner means **a gameweek is missing**; this means **it has been a while**, and conflating
the two would make the loud one meaningless. ⭐ Threshold **three hours** — two missed hourly refreshes,
which sits *above* the measured normal case rather than at it, because *a notice that is always on is a
decoration* (ADR-248).

⭐ **Computed on the server, not the device.** *A phone an hour fast would tell its owner the data was an
hour staler than it is* — and an older build still reads its own timestamp, so the line never blanks.

## Four edges, each with a reason

| | |
|---|---|
| never refreshed | `None`, **never `0`** — *a database nothing has written is not one written just now* |
| an unreadable stamp | `None` — *a freshness check that throws is a pipeline that stops refreshing* |
| a naive timestamp | read as **UTC** — *guessing local time makes the age wrong by the offset, silently* |
| a clock ahead of ours | clamped to `0` — *a negative age renders as a refresh in the future* |

## Corrections made elsewhere

📌 `docs/DEPLOY.md` said the refresh runs *"every 15 minutes in the hour before a deadline"*. That is what
the tick **decides** when it runs; what actually runs is GitHub's call. Corrected, with the measurement.

📌 **ADR-211** is annotated rather than rewritten: its reasoning and arithmetic are sound, and ⭐ *the
premise that the platform would honour the cadence is the part that was wrong.*

## Tests

8 service, 8 widget — mutation-tested **8/9**, the survivor equivalent (a `None` guard the `try/except`
catches anyway). ⚠️ One real gap the mutants found: nothing pinned that the **server's** number wins over
the device clock, which is the whole point of computing it there.
