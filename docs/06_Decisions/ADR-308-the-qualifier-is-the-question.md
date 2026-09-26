# ADR-308 — The qualifier is the question

**Date:** 2026-09-26
**Status:** ✅ **Built.** Captaincy lenses + the refusal mechanism.
**Follows:** [ADR-307](ADR-307-twenty-questions-and-what-ask-does-with-them.md), which measured the problem
and left it unbuilt.

---

## The decision

**One captaincy engine, one intent — the qualifier selects a lens over the same shortlist.** Five questions
that used to get one answer now get five, and a qualifier that *cannot* be honoured is said out loud
without sending the reader anywhere else.

This was the owner's own instinct and it is the right one: ⭐ *six analytics functions would be six places
for the definition of "best captain" to drift apart.*

## What was wrong

ADR-307 measured it: **11 of 31** questions were answered by the right engine, confidently, with the wrong
question. The captaincy row was the clearest case. All four of these returned **the same top pick**:

| the question asked | what came back |
|---|---|
| Who should be my **vice**-captain? | the captain |
| Who is the **safest** captain? | the captain |
| Who is the best **differential** captain? | the captain |
| Is my captain at **rotation risk**? | the captain, described in expected points |

⚠️⚠️ The router matched `captain` and dropped the word that made the question specific. ⭐ *A wrong answer
wearing the shape of a right one* — and the cheapest of them, the vice, needed no new analytics at all:
`_decide_captain` has always taken a `rank` parameter. **Only the word was unrecognised.**

## The lenses

| lens | criterion | why that and not xP |
|---|---|---|
| *(none)* | highest xP | the existing behaviour, unchanged |
| **vice** | the second-ranked pick | `rank=1` — the engine could always do this |
| **safest** | unflagged first, then expected minutes, xP as tie-break | ⭐ *a captain who does not play is the only captaincy outcome that cannot be recovered from* |
| **differential** | least-owned, xP as tie-break | *a differential is a bet on other people not having him*, so ownership is the criterion |
| **rotation** | the same man, described in minutes | the question is about **the** captain, not a different one |

Two further shapes, because people do not ask in keywords:

- **Two named players** — *"is A a better captain than B?"* is a question about two men. Names resolve
  through the **same index the buzz counter uses** (ADR-152), against the **whole market**, never the
  squad. A player outside the shortlist is told he is outside it: ⭐ *"he is not in your top options" is
  more useful than silently substituting somebody who is.*
- **A name that cannot be placed** — see below.

⚠️ A lens must see the **whole** shortlist. The plain question needs three picks; `limit` goes to 15 when a
lens is active, because ⭐ *a filter applied to a truncated list is a filter that answers about the
truncation.* Measured: truncated to three, the "best differential captain" is owned by **13.5%**. Given
the whole shortlist, **0.4%**.

## The refusal, and why it is not a redirect

The owner's constraint, verbatim:

> *"humans will ask anything, will want the quickest route to an answer, if they use Ask they will want the
> answer from there and not to be directed somewhere else to find it."*

⭐⭐ So **nothing here returns an apology and a signpost.** Every path that cannot honour the qualifier
returns *the answer it can stand behind* **and** a plain note saying which question it actually answered,
in one reply:

| when | what comes back |
|---|---|
| a comparison naming someone unresolvable | the captain pick **·** *"I could not place one of those players — check the spelling, or he may not be in the game this season. I did recognise B.Fernandes."* |
| no ownership data | the highest-scoring captain **·** *"I cannot tell you which is the differential"* |
| a one-man shortlist, asked for a vice | that man **·** *"I cannot separate a vice from him"* |
| **neither** named player is rankable | *"Neither is among the captain options I can rank. My pick is Haaland — xP 6.2."* |

⚠️⚠️⚠️ The unresolvable-name case is the one worth keeping in view, because the engine had **reintroduced
ADR-307's own defect one function along**: *"is Mbappé a better captain than Haaland?"* resolved one name,
fell through to the ordinary path, and answered *"Captain pick: Haaland."* ⭐ *A correct sentence and a
dishonest answer* — it silently dropped the half of the question the reader was asking about.

## The heading carries the proof

Every answer names the question it answered — *"Vice-captain (squad 'yours')"*, *"Safest captain"*,
*"Captain, and his minutes"*. ⭐ *A heading that repeats the question is a heading that proves it was
heard*, and it is the only part of an answer a reader checks before trusting the rest.

⚠️ And a minutes question is answered **in minutes**: the `rotation` and `safest` lenses add
`expected_minutes_share` as a sentence — *"100% of a full game — he starts"*, not `0.82`. Naming the lens
in the heading and handing back the same four facts would be *the same failure in nicer clothing*.

## Verification — and the fixture gap it exposed

⭐⭐⭐ **The most useful result in this ADR is a testing one.** Twelve end-to-end tests passed while
**eleven of fifteen mutants survived** — including *"safest" ranked by expected points*, *"safest" picked
the **least** safe*, *every player "starts"*, *the flag went unmentioned*, and *the comparison picked the
**lower** xP*.

⚠️⚠️ **Not missing assertions — a fixture gap.** In the committed fixture the highest-xP player is *also*
the highest-minutes player, nobody is flagged, and ownership never ties. So **a lens that ignores its own
criterion returns the same man as a lens that honours it**, and no assertion about the answer can see the
difference.

⭐ The worst offender was the test that looked strongest: *"five questions get five answers"* compares
**headings**, which differ per lens whether or not the pick does.

The fix was to test the decision functions on **inputs built to discriminate** — a shortlist where the
best scorer is a rotation risk, the safe man scores less, and the differential is neither. **15/15 killed**,
36 tests, full suite green (2796 passed).

⭐ One mutant survives and *should*: reordering `CAPTAIN_LENSES` changes nothing, because the match is by
phrase **length**, not table position. The comment there previously claimed the opposite — ⚠️ *a table
whose correctness depends on its own line order is a table the next edit breaks silently* — and now says
what is true.

## Consequences

- **The app is unchanged except for two chips.** The lenses are server-side, so Android, iOS and web get
  them on the next API deploy. ⚠️ But Ask offered only *"who should I captain?"* as an example, which
  taught the box that captaincy is one question with one answer — ⭐ *a reader who never learns he can ask
  for the vice never finds out the engine can tell him.* Two examples added.
- **ADR-307's remaining rows are untouched**: named players in the other engines (*keep or sell X*), hits &
  free transfers, replacement/rotation, Blank/Double planning. Live/Post-GW questions should route to the
  season swipe (ADR-298) rather than grow an Ask answer.
- 🔴 **The pattern generalises and the next engine should assume it applies.** Every intent with a
  qualifier vocabulary has this defect latent in it, and the fixture cannot see it.
