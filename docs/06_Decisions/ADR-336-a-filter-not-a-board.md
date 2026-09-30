# ADR-336 — A filter, not a board

*The app told people a price might move and gave them nowhere to look.*

**Date:** 2026-09-30
**Status:** Accepted
**Completes:** ADR-335 (price next to the decision) · **Constrained by:** ADR-227 (one player shape)
**From:** the owner — *"a button or two showing risers and fallers? OR do you have a better idea?"*

---

## Context

🔴 **The mobile Players tab had no price movement at all.** Price was a max-price filter and nothing
else. ADR-335 put *"he may cost £0.1m more if you wait"* on a transfer card — and a reader who went
looking for who else was in that position found a board that had never heard of it.

The owner proposed a risers/fallers control. ⭐ **A filter, not a board:** a leaderboard is a different
thing competing with this page for the same job, and *the cheapest version of a feature is the one that
reuses the screen people already know.*

## Decision

Two options behind *Add a filter* — **Rising in price** and **Falling in price** — each producing a
removable chip, using the page's existing progressive-disclosure pattern (ADR-257).

⚠️ **The chip is labelled `Movement`, not `Price`.** The max-price filter beside it is already `Price`,
and two chips both reading `Price: …` would be two questions wearing one name.

⚠️ **The options promise pressure, never the outcome** — *"Under buying pressure — may go up"*. The rule
is right about 40% of the time (ADR-334); ⭐ *a title that promised the rise would be wrong more often
than the waiting it advises against.* A test fails on the word "will".

### 🔴 The direction rides beside the list, and the first attempt put it on the player

I added `price_direction` to each row. `tests/test_player_shape.py` rejected it: ADR-227 requires every
player in every answer to be the same shape, built by `player_summary`, because four shapes once drifted
far enough that one of them shipped **45 database columns to a phone**.

⭐⭐⭐ *A rule about "every call site" only stays true if adding a field to one of them fails.* It did, in
the suite, before the commit.

So `price_directions` is a sidecar map keyed by id — which is how **my-team already carried `prices`**.
Two answers, one habit, and the shared shape untouched. It is also smaller: a map of 487 short strings
against a field on 487 objects, which kept the payload-size guard quiet as well.

⭐ The cuts are bound over `data.players` — **every player, not the rows being returned**. A percentile
over the list on screen manufactures a top 5% inside every filter, so filtering to one club would find a
riser at that club every week of the season (ADR-215).

## Verified

523 Dart and 3,028 Python tests. Both claims checked against their opposite: deleting the predicate
fails, and changing the option's wording to *"will rise"* fails.

⚠️⚠️ **Three of my own tests passed for the wrong reason before they passed for the right one**, and all
three are the same mistake — asserting on something that was never there:

* Rows are a private `_Row`, not `ListTile`. Counting `ListTile`s found **zero on both sides** of the
  filter, so *"the board narrowed"* was comparing 0 to 0. It reads the count the board prints, which
  also changes wording when filtered — `481 players, best first` becomes `10 of 481`.
* The sheet is opened by a chip labelled **Filter**; *"Add a filter"* is the title of the sheet it opens.
* At a 420px surface the chip row scrolls and the control is off-screen. ⭐ *A test that cannot reach the
  control is not testing the control.*

## Consequences

**Good:** someone told a price may move can now find everyone else in that position, on the screen they
were already using, in two taps.

**Costs:** ⚠️ the client now joins a sidecar rather than reading a field, which is one more step between
the wire and the widget. That is ADR-227's price and it is worth paying.

⚠️ **Still not done:** a risers/fallers **board**. Deliberately — it is a third thing, and easier to
judge once the filter has been used. And Streamlit's Players page has had the ▲/▼ column since ADR-092,
so this closes a gap between the two clients rather than opening a new front.
