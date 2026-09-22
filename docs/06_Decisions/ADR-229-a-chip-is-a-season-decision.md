# ADR-229 — A chip is a season decision, and the sweep only saw what it was pointed at

**Date:** 2026-09-22
**Status:** Accepted
**Completes:** the bottom bar (ADR-223/228)
**Extends:** ADR-227

---

## 1. The window is the chip's deadline

`POST /api/v1/squad/chips` accepts `horizon` **and ignores it**.

⭐⭐ **ADR-166's rule, and it is the whole design.** A chip expires at the end of each half-season, so the
question is never *"is this week good?"* but ***"is this week better than the weeks I have left?"*** — and
that is **not a smaller version of the first question, it is a different one.** Answering it over the
one-gameweek window the rest of the app uses would be answering something else.

So the server derives the window from `chip_deadline` and **returns the window it used**. ⚠️ A client
rendering *"next gameweek"* over a three-week answer would be describing someone else's question.

⭐ **The wildcard says what it is worth, not only when.** ADR-185, which the owner found from a two-team
A/B he was forty points ahead in: the advisor said *"Wildcard GW5-7, your weakest stretch"* while his squad
already overlapped an optimal rebuild by **3 of 15**. ⚠️ *A recommendation that measures only WHEN presents
itself as an answer to WHETHER.* The screen leads with the overlap — *"a rebuild would change 13 of your
15"* — and warns when it is small.

---

## 2. ⚠️⚠️ The finding: ADR-227 claimed "one shape everywhere" and was true of five surfaces out of seven

The chips endpoint's first run returned a **45-column raw database row** as its triple-captain pick — the
exact thing ADR-227 had just finished removing.

Adding `chips` to the shape sweep then found **four more**, all inside `gameweek-plan`:

* `captain` and `captain_ranked` — the xP model's working (`rate`, `ep_next`, `defcon_xp`), because
  ADR-227 normalised the captain **endpoint** and never touched the captain **inside the plan**
* `lineup.start`, `.bench`, `.bring_in`, `.drop` — the squad's own rows

⭐⭐ **A guard covers the surfaces it was pointed at, and a new surface is not one of them until someone
points it.** `gameweek` was never in the sweep's fixture; `chips` could not have been. The claim was not a
lie, it was **unchecked in exactly the places nobody had listed**.

### So the sweep now asserts its own completeness

`test_the_sweep_covers_every_endpoint` compares `service.__all__` against what the fixture actually
exercises, and fails on anything missing. It cannot build the request for you — every endpoint takes a
different DTO — but it can refuse to let you forget.

⭐ *A guard that requires manual registration is a guard that will be forgotten.* It found `gameweek` on its
first run.

---

## 3. ⚠️ A third hedge, in my own test

`assert "gain" in wildcard or "margin" in wildcard` — and `margin` is present with or without the
valuation, so the assertion reduced to its always-true half and a mutation dropping `rebuild=` survived.

⭐ *A hedge is not a weaker assertion, it is the absence of one* (ADR-180). **Third time this week**: the
same `or` shape, the same result. The fix names the four fields the rebuild actually contributes.

---

## Consequences

**Good:** the bottom bar is complete — every tab works. Chips answers a season question in season terms. Two
endpoints stopped shipping the database.

**Costs:** ⚠️ chip advice runs the optimiser (`rebuild_value`) over the whole market, which is the most
expensive call in the API. It is a screen opened rarely, which is why that is acceptable — and worth
remembering if it ever becomes one opened often.

**Note on the bar:** Chips has now moved three times — greyed (ADR-223), into More (ADR-228), back to the
bar (here). ⭐ *A tab earns its slot by working*, which is the rule both earlier moves were reaching for and
neither could apply while it did nothing.
