# ADR-299 — A card that knows which week you are in

**Date:** 2026-09-25
**Status:** ⏳ **Gate — agreed on the feedback, not yet built.** Nothing in this ADR ships code.
**From:** the owner, with two FFH screenshots — *"in the history GW screens, the player pop up card needs
to be different, it needs to show the history of that GW and not the prediction from the current gameweek
onwards… The future tabs need to show the prediction for GWs from that GW onwards up to our cap of +5."*

---

## The defect behind both halves

⭐⭐⭐ **ADR-298 made the pitch week-aware and left the card behind.** Swipe to GW4, tap a player, and the
sheet opens on *this* week's projection and a row of actions — **Captain · Vice-captain · Bench ·
Transfer** — offered against a gameweek that finished eleven days ago.

⚠️ *A screen that changes what it is about must change what its children are about*, and the sheet is the
one place a reader goes for detail. Today it is the only surface on the swipe that still believes it is
Tuesday.

## Two halves, and they cost very differently

### ➡️ Forward — **the data is already on the phone**

The sheet draws its three fixture cards from `team.runFor(player)` and `team.runXpFor(player)`. Since
ADR-298 widened the window to `SWIPE`, both already carry **six** gameweeks — the live one and five ahead.
The sheet simply starts at the first and stops at three.

⭐ So a GW9 page showing GW9 · GW10 · GW11 needs **no server change, no request, and no new field** — only
a starting index. *The expensive half of this feedback was paid for three commits ago.*

⚠️ **The window shortens as you swipe forward, and that is correct.** On a GW9 page there are three weeks
left inside the cap, not five. Extending to GW14 would mean projecting nine weeks out, which is the
decision ADR-298 took deliberately and for reasons that have not changed — *a number the model cannot
stand behind does more damage on the main screen than anywhere else.*

### ⬅️ Backwards — **one new request per gameweek, and FPL does the hard part**

The owner's screenshot is a **points breakdown**: `Minutes played 80' → 2`, `Goals 1 → 4`,
`Yellow cards 1 → -1`. We hold the raw facts already (ADR-298 stores minutes, goals, assists, bonus,
saves, clean sheets and cards), but not the **attribution** of points to each of them.

🔴 **The obvious implementation is the wrong one.** Deriving the breakdown from a scoring table — goals 6/5/4
by position, assists 3, clean sheet 4/1 — is twenty lines and would be **wrong this season**: FPL added
`defensive_contribution`, worth 2 points, and it appears in real rows right now. ⚠️ *A points breakdown
that disagrees with the total printed above it is worse than no breakdown*, and a hand-rolled table
disagrees the moment the game changes without telling us.

⭐⭐ **FPL publishes the breakdown itself**, on `event/{gw}/live/`, as an `explain` block per player:

```
minutes                 value= 90   points= 2
clean_sheets            value=  1   points= 4
yellow_cards            value=  1   points=-1
bonus                   value=  2   points= 2
defensive_contribution  value= 11   points= 2   ← the line a table would have missed
```

**Verified on real data (GW4):** the breakdown sums to the total we already show, player by player —
Kinsky 7 = 7, Calafiori 6 = 6, Mitchell 1 = 1.

## Cost

| | |
|---|---|
| **Forward half** | zero — the data is on the device |
| **Backwards half** | one `event/{gw}/live/` request **per gameweek**, not per player |
| FPL's payload | 510 KB for all 659 players |
| What we forward to the phone | **1.9 KB** — the fifteen in that squad, ~2.5 lines each |
| Caching | ⭐ a played gameweek never changes, so it caches forever — the same economics ADR-298 already runs on |

⚠️ The request rides the call `gameweek_result` already makes, so a past page still costs **one round trip**,
not two.

## Scope

**In:** a past card showing that week's points, the fixture **with its scoreline** (stored already as
`team_h_score` / `team_a_score`), and FPL's own points breakdown · a forward card whose projections start
at the week you are looking at · the squad actions hidden on any week that is not the live one.

**Out, deliberately:**
- 🔴 **Advice about a past week.** Unchanged from ADR-298, and the same sentence still applies: *a tool
  that grades your history is a tool people stop opening after a bad week.*
- Computing points ourselves, ever — see above.
- A "General stats" tab. The competitor has one; ⚠️ *copying a tab because it is there is how a screen
  acquires content nobody asked for.*

## What must be settled before building

1. **The forward window shortens near the cap** — GW9 shows three weeks, GW11 shows one. Stated above as
   the design; it follows from ADR-298's cap and needs a nod rather than a discussion.
2. **What an unplayed or blank week shows** on a past card — ⭐ probably the fixture and "did not play",
   with no breakdown, since FPL publishes no `explain` lines for a man who never came on.
