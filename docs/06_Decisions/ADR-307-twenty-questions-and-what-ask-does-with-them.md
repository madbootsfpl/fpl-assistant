# ADR-307 — Twenty questions, and what Ask actually does with them

**Date:** 2026-09-26
**Status:** ⏳ **Gate — measured, not built.**
**From:** the owner's question list — five categories, a Captaincy Engine, a Blank/Double Planning Engine,
and a Live/Post-GW category, each with the underlying decision named.

---

## What was measured

All **31** questions, run through the live router against the owner's real squad. Not a review of the
code: ⭐ *the router's behaviour is an empirical question and it was cheaper to ask it than to reason
about it.*

| | count | what happened |
|---|---|---|
| ✅ **Answered** | **8** | the right engine, answering the question asked |
| ⚠️ **Right engine, wrong question** | **11** | confidently answered something adjacent |
| ✗ **Wrong engine** | **10** | a fixture table for *"who replaces my injured player?"* |
| 🟢 **Honestly declined** | **2** | routed to `chat`, which lists what it can do |

🔴 **The headline is the middle row, not the last one.** Only **2 of 31** admit they cannot help. **21
answer something else**, and 11 of those do it from the correct engine with an authoritative-sounding
headline. ⚠️⚠️ *A wrong answer wearing the shape of a right one* is this project's own phrase for the thing
it least wants to ship, and Ask ships it twenty-one times out of thirty-one.

## The three failure modes, with examples

⚠️⚠️ **1 — The qualifier is ignored.** The router matches a keyword and drops the word that made the
question specific.

| asked | answered |
|---|---|
| *"Who should be my **vice**-captain?"* | the **captain** pick |
| *"Who is the **safest** captain?"* | the same captain pick |
| *"Who is the best **differential** captain?"* | the same captain pick |
| *"Is my captain at **rotation risk**?"* | the same captain pick |
| *"Should I keep or sell **Haaland**?"* | a transfer of **Ndiaye → Belloumi** |
| *"Who should I transfer **out**?"* | a full A → B swap |
| *"Who should I bench, **and in what order**?"* | the XI, with no bench order |
| *"Should I take a **-4**?"* | the weekly plan, with no hit arithmetic |

⭐ **The cheapest of these is one word over an engine that already works**: `_decide_captain` takes a
`rank`, so the *second*-best captain is already computable — nothing detects *"vice"*.

✗ **2 — The wrong engine entirely.** *"Who should replace my injured player?"* returns a **fixture
difficulty table**. So does *"which players are rotation risks?"* and *"which players caused my rank
movement?"* ⚠️ *A table of clubs is not an answer about a player*, and nothing in the reply says so.

🟢 **3 — The honest one**, and there are only two: *"How should I improve my team?"* and *"Who should I
target over the next 5 Gameweeks?"* both route to `chat`, which lists what Ask **can** be asked. ⭐ *This
is the behaviour the other twenty-one should have.*

## What I would do, in order

### First, and before any new engine: **let it refuse**

⭐⭐⭐ **The highest-value change here is not a feature, it is a `None`.** Twenty-one questions get a
confident answer to a different question; making those say *"I can't answer that one yet — here is what I
can do"* costs no analytics at all and converts the worst failure mode into the best one.

⚠️ *A tool that answers everything teaches you to trust nothing it says.* The two questions that decline
are the only two whose answers a reader can currently take at face value.

### Then the engines, cheapest first

| | work | why this order |
|---|---|---|
| **Captaincy variants** (vice · safest · differential · rotation · A vs B) | small — one engine, a `rank` that exists, and a shortlist filter | ⭐ the owner's own instinct was right: *one* Captaincy Engine with an intent, not six functions |
| **Named-player questions** (*keep or sell X*, *is X rising*, *X vs Y as captain*) | small — the name is already resolved elsewhere (ADR-152) | ⚠️ *the router throws the name away*, which is why #9 answered about two other players |
| **Hits and free transfers** (*-4 worth it*, *how many FTs to save*) | medium — the plan already computes the gain; the comparison is the missing half | the arithmetic exists, the framing does not |
| **Replacement / rotation risk** | medium — `replacements` and `minutes_weight` are both built and neither is reachable from Ask | two endpoints away from working |
| **Blank / Double Gameweek planning** | 🔴 large — and the owner is right that it is *"a proper multi-week optimisation problem"* | needs blanks and doubles in the fixture model first |
| **Live / Post-GW** (effective ownership, rank movement, versus the field) | 🔴 large, and **a different product surface** | ⚠️ these are not *"what should I do"* questions; they are *"what just happened"*, which is the season swipe's territory (ADR-298), not Ask's |

## Two judgements worth recording

⭐ **The owner's architecture instinct is right and should be kept**: one Captaincy Engine with an intent
parameter, not six analytics functions. ⚠️ *Six functions would be six places for the definition of
"best captain" to drift apart.*

📌 **Live/Post-GW belongs with the swipe, not with Ask.** *"How did my rank move?"* and *"which players
caused it?"* are about a week that has been played — the screen for that already exists and already has
the data (ADR-298/299). ⭐ *A question is a routing decision; it does not have to route to a sentence.*
