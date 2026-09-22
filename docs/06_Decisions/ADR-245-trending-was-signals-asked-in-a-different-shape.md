# ADR-245 — Trending was Signals asked in a different shape

**Date:** 2026-09-22
**Status:** Accepted
**From:** tester feedback — *"Trending could be integrated into signals — filter on my Squad & Global"*
and, from the previous round, *"Signals — I was expecting more, let's build steadily inc market."*
**Builds on:** ADR-150 (evidentiary ordering), ADR-232 (Signals), ADR-210/215 (live thresholds)

---

## Context

The owner asked for Trending inside Signals with a scope filter. ⭐ **He is right that they are one
screen**: both answer *what is the crowd doing?*, and a second screen would have meant a second ordering, a
second idea of what counts as evidence, and two places to keep honest.

Signals was squad-scoped — deliberately, as the decision layer. What it could not do was answer the
question a manager asks *next*: **what is happening to everyone else's players?**

## Decision

**`scope: "squad" | "global"`**, defaulting to `squad`. ⚠️ *A default that widens the question is a default
that surprises somebody*, and the app is the decision layer before it is the exploration one.

### ⭐⭐⭐ The market has to be bounded, and the bound has to be visible

Measured on the live board before choosing anything:

| | |
|---|---|
| ownership, median | **0.2%** |
| players with FPL news | **194** |
| at the 75th percentile (**1.2% owned**) | **22** |

⚠️ **An unbounded sweep is 194 news items, nearly all about players almost nobody holds.** ⭐ *A list that
long is not more information, it is a screen a person stops reading.*

So the cut is the **75th percentile of the live ownership distribution**, not a number typed here. It is
not a judgement about 1.2%; it is *"the quarter of the board most managers consider"*, and it moves when
the league does — ADR-210's rule, and there is a test that halves every share and fails if the cut does
not follow.

⚠️⚠️ **The answer reports the cut it used** (`ownership_floor`), and the app prints it: *"36 across 167
players owned by 1.2% or more"*. A market view that silently drops four fifths of the board **lies by
omission** — ⭐ *a filter the reader cannot see is one he will eventually be surprised by* (ADR-215).

### Trending becomes a signal kind, and sorts last

`trending` joins `official · departure · exodus · headline` — ⚠️ **at the bottom.** It is the weakest
evidence here: a fact about other managers, not about the player. ⭐ *"Lots of people did this" is the
reason a template forms, and it is not on its own a reason to join one.* The label is **"The crowd"**, not
"Trending", because *trending* sounds like a verdict the data cannot support.

⭐ It never fires for a player you already hold. *"12,000 managers bought him"* about one of your own is not
news — you are one of them. For your player the interesting version is the exodus, a different kind, which
still fires.

### Every signal says whether it is one of yours

⭐⭐ **"Yours" changes what a signal means, not just who it is about**: an exodus from a player you hold is
a decision; the same exodus from one you do not is a fact about the market. ⚠️ Flagged by the service, so
the client is not matching ids itself and getting it wrong.

⭐ This is why the squad ids are still sent in global scope — they do not narrow the sweep, they only mark
the list.

## Consequences

* `SignalsRequest` is **the one squad-shaped request where the squad is optional**. Noted in the DTO,
  because every other one raises without it.
* The web app's Trending page is untouched. ⚠️ It is now the second implementation of this question, and
  the two will drift — 📌 *whether the web page should become a view of this answer is open, and is a
  bigger decision than this ADR.*

## Verification

* **10 tests**: scope isolation, the floor being read and reported, the floor moving when the distribution
  does, the crowd sorting below an injury FPL confirmed, the crowd never reporting your own player, and the
  `owned` flag agreeing with the squad.
* **7/7 mutations killed**: an unbounded market; a hard-coded 1.2%; the floor computed but not reported;
  the crowd outranking an official injury; the crowd reporting a player you own; nothing flagged yours; and
  an unvalidated scope.
* ⚠️ **One assertion in the first draft was `assert … or True`** — vacuous, and written to paper over the
  fact that `player_summary` does not carry ownership. It now checks the board. ⭐ *A hedge in an assertion
  is a confession.*
