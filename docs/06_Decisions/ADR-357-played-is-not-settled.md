# ADR-357 — Played is not settled

**Date:** 2026-10-18
**Status:** Accepted
**Found:** tester feedback — *"19 hours post 1st game of GW, nothing posted, yet YouTube vids available on Flashscore"*
**Extends:** ADR-347 (highlights) · **applies:** ADR-356

---

## Context

Nineteen hours after GW7's first kick-off, the Scores screen showed **0/10** highlights links. The videos
existed — a tester was watching one on Flashscore.

It was not the matcher and not ADR-353's date window. Checked against the live feeds, **all five played
matches resolved correctly right then**:

```
EVE 0-2 CHE  ✅    BRE 1-2 LIV  ✅    FUL 1-0 HUL  ✅    MCI 3-2 IPS  ✅    NEW 0-1 AVL  ✅
```

**Nothing ever looked.** `fixtures_wanting_highlights` filtered `WHERE finished = 1`, and FPL's own view
at the same moment was:

```
all five:   finished=False   finished_provisional=True
GW7 event:  finished=False   data_checked=False
```

⭐⭐ **`finished` is a gameweek-level settle, not a per-match one.** It does not flip until the whole
gameweek's bonus is confirmed — after the Monday night match, three days after the Saturday lunchtime one.
⚠️⚠️ *By then the clubs' fifteen-entry feeds have moved on*, which is exactly why GW1–GW5 are permanently
unrecoverable, and it would have happened to every gameweek from here.

## 🔴 The same mistake, for the third time in two days

| | gated on | arrives |
|---|---|---|
| ADR-354 | `started`, written by the hourly refresh | up to 5h late |
| ADR-356 | `finished`, the bonus settle | 96 min late, measured |
| **this** | `finished`, the same flag | **up to 3 days** late |

⚠️⚠️ **ADR-356 was written yesterday and names this exact fact.** It fixed the **display** — the card now
says *Full time* at the whistle — and left the **fetch** on the old flag. ⭐⭐ *A fact applied to one call
site is not a fact applied*, and the other call site was in the same feature, found by a tester rather
than by me.

## Decision

**The clock decides, as it does for the live gate.** A match that kicked off more than
`PLAYED_AFTER_HOURS = 2.5` ago and has a score has been played.

📌 `finished` is kept as an **alternative** rather than replaced — a settled match qualifies either way,
which makes the change purely additive and protects a settled fixture with no stored kick-off time.

⭐ 2.5h is measured: GW7's first match ran 11:30 to about 13:35. ⚠️ Too short merely wastes a feed fetch on
a match still in play; *too long delays a link into the window where YouTube has dropped it*, which is
the failure this constant exists for.

## Consequences

✅ Four mutants, each caught — including *"drop the clock"*, which fixes the reported bug and starts asking
for highlights at half time.

🔴 **The change exposed a false promise in a test fixture.** `store_with_a_played_match` cleared `finished`
to leave *"one candidate only, so a test asserting 'nothing else was fetched' means what it says"* — but
left the seed's **scores** in place. Under a query that no longer reads `finished`, fifty fixtures
qualified and `fill`'s limit of twenty never reached the one under test. ⭐ *A fixture that promises one
candidate has to mean it under the query the code actually runs*, not the one it ran under when written.

📌 Unchanged and worth stating: old fixtures with no link are still retried every tick and still resolve
to nothing, because their videos are gone. That was true before this change — the `finished` flag was
long since set on them — and the newest-first ordering means recent matches are served first regardless.
