# ADR-298 — The season you can swipe through

**Date:** 2026-09-25
**Status:** ⏳ **Gate — agreed, not built.** Nothing in this ADR ships code.
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

## What must be settled before building

1. **Cards first.** `yellow_cards` / `red_cards` columns and a backfill re-run — ⚠️ *a screen that shows
   every match event except the one the owner named is a screen that gets reported as broken.*
2. **Where the cache lives.** Picks per manager per gameweek: on the device, or server-side beside the
   board? ⭐ On-device is free and private; server-side is shared across a manager's devices. Probably
   on-device, and that is its own small decision.
3. **What an unplayed gameweek looks like mid-week.** ⚠️ GW6 is neither past nor future while it is being
   played — *the state nobody designs for is the one the app spends every Saturday in.*

## Cost

**Effort:** a few days, and mostly UI — one endpoint, one model, a `PageView`, a cache, plus the cards
backfill. No new service, no new FPL integration, no new dependency.

**Running cost:** one FPL request per manager per past gameweek, cached permanently. At nine testers and
38 gameweeks that is a few hundred requests across a whole season.

⚠️ **The real cost is scope creep into judgement.** A screen showing what happened is one feature; a
screen showing what you should have done is a different product, and the boundary between them is one
sentence of copy.
