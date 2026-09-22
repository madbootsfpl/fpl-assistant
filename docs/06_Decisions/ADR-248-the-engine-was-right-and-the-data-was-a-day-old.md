# ADR-248 — The engine was right and the data was a day old

**Date:** 2026-09-22
**Status:** Accepted
**From:** tester feedback — *"See Pascal Groß stats. His last game was v Arsenal, scored 14pts and the prior
one was v Coventry score 17 points. Not sure why it's not reflected. Also why showing only last 4 GW versus
last 5."*
**Builds on:** ADR-211 (the pipeline runs without you), ADR-237 (the player card)

---

## Context

The owner opened a player card and found a blank against Coventry and no Arsenal fixture at all. He was
right on both counts:

| Groß | our board | live FPL |
|---|---|---|
| GW4 vs COV | **0 pts, 0 mins** | **17 pts, 90 mins** |
| GW5 vs ARS | **missing** | **14 pts** |
| season total | 33 | **47** |

Not an isolated row: **260 of 662 players** disagreed with FPL. The database was last written on **21 Sep
at 13:10**; GW5 finished after that.

⭐⭐⭐ **And nothing on any screen could tell the difference between a stale board and a wrong engine.** The
app reported yesterday's reality with complete confidence, so the only available conclusion was that the
maths was broken.

## What was actually wrong

**Three separate things, and only one of them was a bug.**

1. **The data was stale.** A local `refresh` had not been run. ⚠️ ADR-211's *"the data refreshes itself"*
   is true of the **deployed Streamlit app on Postgres**; the phone talks to a local API reading a local
   SQLite file that nothing updates on a schedule. ⭐ *A property that holds for one deployment is not a
   property of the system.*

2. **`refresh` does not touch per-gameweek history.** It corrected `total_points` to 47 and left the five
   rows behind it untouched — the history walk is a separate, deliberately rare job
   (`pipeline --backfill`), because it is one throttled request per player.

3. ⚠️ **"LAST 5" sat over four boxes.** There genuinely were only four, so the card was right and its
   heading was wrong. ⭐ *A heading that names a number it is not showing turns a correct screen into a bug
   report* — and here it hid a real problem underneath, because the fifth gameweek really was missing.

## Decision

**`my-team` reports the data's own freshness, and the pitch warns when a finished gameweek is missing.**

⚠️⚠️ **`refreshed_at` alone is not the answer.** *"Updated 20 hours ago"* is fine on a Tuesday and useless
the evening a gameweek finishes. What matters is whether a **completed gameweek is absent** — a different
question, and one `backfill_due` already answers for the scheduler.

⭐⭐ **So this asks the pipeline's own question rather than inventing a second definition of "behind".** If
the app reasoned separately, the app and the pipeline could disagree about whether the board is current —
and the app is the one a person believes.

**The banner appears only when the board is behind**, and names the gameweek: *"Results for GW5 are
missing, so points, form and projections are out of date."* ⭐ *"Missing GW5" is a fact someone can act on;
"stale" is a mood.* ⚠️ A permanent "last updated" strip would be read once and then never again — *a warning
that is always on is a decoration.* The plain age lives in Settings, where someone goes to ask.

**The heading now counts what it shows** — `LAST 4` when there are four.

## What building it found

⚠️⚠️ **I called `backfill_due` with `get_upcoming_fixtures()` and it told me everything was fine.** A
completed gameweek is not *upcoming*, so the narrower list contains nothing finished, and the function can
only ever answer *"nothing is due"* — reassuringly, and falsely. The real caller passes
`get_all_fixtures()`. ⭐ **A question asked of the wrong input gets a confident answer to a different
question**, which is this session's third instance of that shape. There is a test that fails if the
fixture list looks like the upcoming-only one.

⚠️ **A test's own guard fired after the refresh, exactly as intended.**
`test_the_gain_never_counts_the_selection_fiction` asserts that its fixture can actually tell the two
numbers apart; when the board updated, the top-xP player moved onto the bench and the assertion became
vacuous. It refused to pass. ⭐ *A fixture derived from live data drifts with it, and an assertion that
says so is worth more than one that quietly starts passing for free.*

⚠️ **`backfilled_at` was returned briefly and removed.** It is a string in a backfilled database and null
in the committed test fixture, which made the contract sample unstable — and nothing read it. ⭐ *A field
nobody reads is a field that can only cause drift.*

## Consequences

📌 **The local API still has no scheduled refresh**, and that is now visible rather than fixed. Someone has
to run `refresh` and, after a gameweek, `pipeline --backfill`. ⚠️ *This is a real gap for the phone build,
and the banner is a smoke alarm, not a sprinkler.* It belongs with hosting.

📌 **`backfill_due` asks at gameweek granularity**, so a round that is *held but incomplete* — a late
fixture leaving stub rows inside an otherwise-finished gameweek — is not detected. That is what left Groß's
GW4 wrong while the round counted as held. Open, and worth its own look.

## Verification

* **4 tests**: the field is on the screen a manager opens rather than on `/health`; it names the gameweeks;
  a failing check never takes the pitch down; and — by spying — that it really is `backfill_due` being
  called, with the whole fixture list.
* **4/4 mutations killed**: the upcoming-only list (the exact mistake above); the rounds dropped to leave a
  bare flag; a crash escaping to the screen; and nothing ever reported as behind.
