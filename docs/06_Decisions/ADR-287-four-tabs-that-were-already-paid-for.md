# ADR-287 — Four tabs that were already paid for

**Date:** 2026-09-24
**Status:** Accepted
**From:** the owner — *"lets do the mini-league sub-tabs next"*
**Completes:** ADR-267's *"📌 Not built: Transfers, Rank and Chips sub-tabs, and the Awards tab."*

---

## They were parked as unbuilt. Three of them were already being fetched.

The Captains tab spends **one FPL request per manager**. The payload that comes back:

```json
{ "active_chip": "bboost",
  "entry_history": { "points": 77, "overall_rank": 3842466,
                     "event_transfers": 2, "event_transfers_cost": 0,
                     "points_on_bench": 8 } }
```

⭐⭐ **Chips, Rank and Awards were arriving and being discarded**, and the transfer *count* and *hit* with
them. Only the transfer **detail** — who each manager bought and sold — needs a second request per
manager, and the owner chose not to spend it.

⚠️ *Four features were on a roadmap as work when the data for three of them was already crossing the
wire.* The cost of this ADR is one `sorted()` and some rendering.

## What each tab is for

| | The question | Cost |
|---|---|---|
| **Transfers** | Who is churning their squad, and what did it cost them? | free |
| **Rank** | Where are these people **in the world**, not just among each other? | free |
| **Chips** | Who has spent what this gameweek? | free |
| **Awards** | Who won it, and who wasted the most? | free |

⭐ **Rank is the one a league table structurally cannot answer.** The standings carry a league position;
`overall_rank` is the only column here that comes from outside the twelve people you know.

## Decisions

**Five tabs, one flag.** `withCaptains` now buys the whole per-manager read, and opening the fifth tab
costs nothing if you opened the second. ⚠️ *A panel that re-spends twenty requests every time you tab
back to it punishes browsing*, so it is still fetched exactly once.

**Awards are structured, not worded.** The server sends `kind`, `manager` and `value`; the app supplies
the trophy, the title and the sentence. ⭐ The badges' rule from ADR-286, for the same reason: *a client
that has to take a sentence apart to lay it out will one day take it apart differently.*

**The bench award is omitted when it is zero.** ⭐ *An award for wasting nothing is not an award*, and a
row reading "0 pts left on the bench" makes the reader work out whether that is good.

**A tie does not move.** `max` is stable, so the award goes to the highest-placed manager in the table
rather than to whichever order a dict happened to iterate in — ⚠️ *an award that changes hands on a
refresh is an award nobody believes.*

**Chips are named in FPL's words** — Bench Boost, not `bboost`. *An app that renames the game's moves
makes the manager translate* (ADR-286's rule again).

**Each column adds itself up.** *"The league made 8 transfers, costing 4 points in hits"* — ⭐ *a list of
twelve numbers invites the reader to add them up, and doing that arithmetic for them is the whole job.*

## ⚠️ Three things the screen taught me

**The sample documented the empty case.** The regeneration stub omitted `entry_history`, so the first
`league.json` I generated had **every new field null and no awards at all** — a fixture that would have
let a wrong renderer pass. ⭐ *A sample that documents the empty screen documents the one screen nobody
will see*, which is precisely what that script's own docstring says samples are for. The stub now has
three managers who differ on every column.

**`Container(alignment:)` expands to fill.** Seven tabs in a `Wrap` came out as **seven full-width
buttons stacked down the screen** — the opposite of a wrapping tab bar. One word, and only a screenshot
found it: ⚠️ *the tests asserted what each tab renders, and never that the tab bar was a tab bar.*

**A prefix a mutation still satisfies is not a test.** The Rank footnote check asserted `'3 squad'`,
which stayed true when the wording dropped the word **read** — the word that makes it a count of what
was fetched rather than the size of the league. 8/8 killed after sharpening it.

## What this does not do

- **No transfer detail.** Who came in and out needs a second N-call pass; the owner chose the free half.
  The button would go here if it is ever wanted.
- **No season-long awards.** Everything here is this gameweek. A season table would need a fetch per
  manager per gameweek, which is a different order of cost and a different decision.
