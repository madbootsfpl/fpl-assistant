# ADR-298 — The season you can swipe through

**Date:** 2026-09-25
**Status:** ✅ **Built** (2026-09-25). The gate was agreed first and this document was written before
any code — ⭐ *the section below on what building found is the part a gate ADR cannot contain, and the
reason it is worth coming back to write it down.*
**From:** the owner, with two FFH screenshots — *"swipe the 'My Team' page right you get the previous
week's team with scores, yellow cards picked up etc., swipe left and you get the next GW predicted
score… till you reach GW1 or GW38. How difficult would this be to add and at what cost?"*

---

## The two directions are different problems

⭐⭐ **Backwards is a rendering job. Forwards is a claim about the future.** They arrived as one gesture
and they are not one feature, which is the whole reason this is a gate.

## ⬅️ Backwards — agreed, and most of it exists

| what the screen shows | where it comes from | cost |
|---|---|---|
| points · goals · assists · bonus · saves · clean sheets, per player per week | **`player_history`** — already stored: 3,216 rows, GW1–5, all 667 players, kept fresh by the pipeline | **none** |
| GW points · overall rank · rank movement | `entry_history`, inside the picks payload — **already parsed** (ADR-287) | **none** |
| the squad **as it was** that week | `get_entry_picks(entry, gw)` — the client already has the method | **1 FPL request per gameweek** |
| auto-subs — who actually came on | `automatic_subs`, same payload | **none** |
| 🟡 yellow / red cards | ⚠️ **not stored** — two columns and a backfill re-run | small |

⭐⭐ **A played gameweek never changes.** Fetch GW5's picks once and it is correct forever, so the cost is
one request per manager per gameweek **ever** — not per swipe, not per session. ⚠️ *A cache whose entries
can never go stale is the only kind that needs no invalidation policy*, and this is one.

⭐ It also fits the code rather than fighting it: the pitch already carries a `PitchMode`
(`nextGw` / `run` / `price`), and a past week is a fourth — points where the xP goes.

📌 **Worth naming: this is the first feature that makes the app's own history useful.** The pipeline has
been paying to store per-gameweek data since ADR-027 and nothing on a phone has ever shown it.

## ➡️ Forwards — **capped at 5**, and the cap is the decision

FFH swipes to GW38. The engine could be made to: `MAX_HORIZON = 8` is a constant, and raising it to 33 is
a one-line change.

🔴 **Declined, and the reason is not effort.**

- FPL publishes dependable fixtures only a few gameweeks out; beyond that kick-offs move and
  blanks/doubles appear that are not yet known.
- Form and minutes decay as inputs. By GW15 a projection is mostly *"this is a good player at a good
  team"* — which is true, and is not a number.
- ⚠️⚠️ **Every screen in this app carries *"Confidence is a heuristic from the signals, not a
  probability."*** Printing a confident-looking `4.2` against GW31 in September contradicts that line in
  the most-looked-at place in the product. ⭐ *A number the model cannot stand behind does more damage on
  the main screen than anywhere else, because that is where it is believed.*

**Five, because five is already the answer elsewhere.** ⭐ It is not a hedge picked to sound cautious: the
Lab's wildcard and fresh-season modes plan over 5, Players ranks on *"xP over 5 GW"*, and the Lab's own
result panel says *"xP over 5 GWs"*. ⚠️ *A new limit that disagrees with the limits already in the product
teaches the reader that limits are arbitrary.*

⭐ **The last forward card says why it stops** rather than the swipe silently dying — *a boundary with no
explanation reads as a bug, and the reason is the most honest thing on the screen.*

## Scope when it is built

**In:** swipe right to GW1 · swipe left to GW+5 · points and match events on past weeks · the squad as it
actually was, including auto-subs · GW points and overall rank · cards, once backfilled.

**Out, deliberately:**
- forward beyond 5 — this ADR's decision
- 🔴 **past-gameweek *advice*.** The engine must not say what you *should* have done. ⚠️ *A tool that
  grades your history is a tool people stop opening after a bad week*, and nothing in the product does
  this today.
- other managers' past squads — a different feature with a per-manager cost (ADR-287's economics)

## What had to be settled before building — and what building settled

1. **Cards first.** ✅ `yellow_cards` / `red_cards` are columns on `player_history`, parsed in
   `PlayerGameweek.from_api`, and registered in `_MIGRATIONS` — ⚠️ *which is where this nearly failed
   silently: the migration went in as a **second `player_history` key** in the dict literal and Python
   discarded the first without a word.* `tests/test_migrations_are_registered.py` now guards that shape.
2. **Where the cache lives.** ✅ **On the device, in memory, for the session.** `ServiceClient` holds a
   `Map<int, GameweekResult>` and writes to it **only when `played` is true** — ⭐ *the cache key is not
   the gameweek, it is the gameweek's finality.* A week still being played is re-fetched every time it is
   looked at, which is exactly what item 3 turned out to need.
   ⚠️ **Not persisted, and that is the smaller decision inside this one.** A settled gameweek never
   changes, so persisting it would be safe — but it would also be the first thing in this app that stores
   a manager's history on the device, and a session-length cache already removes every repeat request
   within the one sitting where repeats happen.
3. **What an unplayed gameweek looks like mid-week.** ✅ It says so, and it is never cached. `played` comes
   from the service and the page prints *"This gameweek has not been played yet"* — ⭐ *the state nobody
   designs for got the shortest code path, because the honest answer to "what happened?" during a match is
   "ask again later."*

## What building found that planning did not

⚠️⚠️⚠️ **The forward limit was off by one, and no test noticed for an hour.** The service sent `WIDE` = 5
gameweeks of projection and the app walked 5 pages *past* the live one — so the fifth forward page had no
data at all: fifteen dashes under a confident **0.0 Predicted**. ⭐ *A window includes the week you are
standing on*, so five forward pages need six weeks. There is now a `SWIPE = WIDE + 1` constant that says
this in one line, and `tests/test_forward_limit_agrees.py` reads **both halves** — the Dart constant and
the Python one — because neither suite can see the other's number.

⭐⭐ **It was a surviving mutant that found it, not a reading of the code.** The mutation *"a missing
projection becomes 0.0"* survived, which said no test cared about a missing projection. Chasing why led
straight to a whole page of them. ⚠️ *The bug was invisible to every test that existed and to me; the only
thing that pointed at it was a deliberately broken version of the code passing.*

⚠️⚠️⚠️ **And a past page never said which week it was — found on a device, with twenty tests passing.**
Every number was right: the points, the rank, the bench, the goals, the cards, the auto-subs. After four
swipes there was no way to know which gameweek you were reading. ⭐ *A screen whose entire purpose is
"which week is this?" has to answer it, and every test here was checking the answers to other questions.*
Each page now carries its week in one shape — `GW5 · final`, `GW6 · Sat 10 Oct, 11:00`, `GW9 · projected`,
`GW6 · not played yet` — so the four page types read as one screen rather than four.

⚠️ Chasing that also found `GameweekResult.gameweek` parsing as `?? 0`, one class above the comment
stating the rule it broke — *null means not known, never zero*, and **GW0 is a week that does not exist.**

⭐ **The header was lying in the same direction.** Summing `?? 0` over a week with no data printed
`0.0 Predicted` above fifteen cards that all read `—` — *a header that contradicts every number under it
is worse than no header, because it is the one a reader trusts.* It is a dash now too.

## What shipped

**Service:** `POST /api/v1/squad/gameweek` → `gameweek_result()`; `run_xp` and the fixture map widened from
`RUN` to `SWIPE`; `yellow_cards` / `red_cards` through the model, the schema, and the migrations.

**App:** `season_view.dart` — `SeasonPages` (the `PageView` and the index arithmetic), `PastGameweek` (the
result list), `ForwardEdge` (the page that says why it stops). `PitchView` gained an optional `gameweek`,
and on a forward page it drops the mode bar, the deadline countdown, the bank, the value, the transfers and
the price — ⭐ *every one of those is a true fact about today that becomes a false claim four weeks out.*

**Tests:** 21 in `mobile/test/season_pages_test.dart` and 7 in `mobile/test/gameweek_result_test.dart`,
mutation-tested at **19/19 caught** after the three gaps above were closed; `test_forward_limit_agrees.py`,
plus the widened window pinned in `tests/test_run_window_and_opponents.py`.

## Cost

**Effort:** a few days, and mostly UI — one endpoint, one model, a `PageView`, a cache, plus the cards
backfill. No new service, no new FPL integration, no new dependency.

**Running cost:** one FPL request per manager per past gameweek, cached permanently. At nine testers and
38 gameweeks that is a few hundred requests across a whole season.

⚠️ **The real cost is scope creep into judgement.** A screen showing what happened is one feature; a
screen showing what you should have done is a different product, and the boundary between them is one
sentence of copy.
