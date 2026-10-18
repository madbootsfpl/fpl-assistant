# ADR-361 — The current gameweek was the blank one

**Date:** 2026-10-18
**Status:** Accepted
**Found:** the owner, on build 46 — *"GW7 does not show any player detail, even on tapping"*
**Extends:** ADR-360

---

## Context

Build 46 staged to the phone. GW6 drew in full, GW9 drew its fixtures and the players involved, and
**GW7 — the current week — showed scorelines and nothing else.** Tapping a match offered only the
highlights row.

Not the screen. The server returned nothing to draw:

```
GW6:  people=108  goals=34  bonus_race=50
GW7:  people=0    goals=0   bonus_race=0      ← the week being played
GW8:  people=0    goals=0   bonus_race=0      ← correct; not played
```

## 🔴🔴 The backfill waits for the whole round, and the card did not know

ADR-360 built the card on `player_history`, which is filled by `backfill.yml` — and `backfill_due` asks
for a round only once **every fixture in it is complete**:

> *"Expensive and deliberately rare. One request per player, throttled — so this is gated on a gameweek
> actually being missing rather than run on a clock."* (ADR-211 2d)

GW7 ran Saturday to **Monday**. Its Saturday matches had been over for two days and still had no stored
history, and would not until Spurs–Coventry settled the week.

⚠️⚠️ **The week people care most about was the one week the card was blank**, and it would have been blank
every week, every weekend, for the two days that matter.

⭐⭐ This is the fourth time in three days a feature waited on *"the whole gameweek is settled"*: live
scores on `started` (ADR-354), the caption on `finished` (ADR-356), the highlights lookup on `finished`
(ADR-357), and now the card on the backfill. 📌 *The pattern is not four coincidences.*

## Decision

**Stored history first; the live fixture payload when there is none.**

⭐ The data was already in hand. `/fixtures/` carries a `stats` block per match — goals, assists, cards,
bonus and BPS, keyed by player **id** where history keys by **code** — and this module already fetched
that payload whenever a match was in flight. ⚠️ *The fix was to stop throwing it away.*

A gameweek whose history is stored asks upstream for **nothing**; only a played fixture with no rows
triggers the fetch, which in practice is the current week and nothing else.

📌 `yours` still waits for the backfill: the live payload has BPS and bonus but no `total_points`, and
⭐ *a points total this app worked out itself would eventually disagree with FPL's* (ADR-346). `yours_known`
already says so, which is why that half degrades honestly and this half did not.

## 🔴 Two tests that proved nothing

**The headline test left its fixtures unfinished**, three hours old — so `_playing` was true, the ordinary
live fetch ran, and the fallback was never reached. ⭐⭐ *The mutation deleting the fallback passed it.*
GW7's Saturday matches were **finished** and outside the live window; that is the state to reproduce, and
the test does now.

**The economy test used a double that raises.** `_live_fixtures` catches every exception and degrades, by
design — so it passed even with the fallback firing on every single request. ⭐ *A spy that records is the
only kind this module cannot swallow.*

## Consequences

✅ Four mutants, each caught — after two of them survived and sent the tests back.

⚠️ One extra upstream call per request for the current week, behind the same 60-second cache. A week whose
history has landed makes none.
