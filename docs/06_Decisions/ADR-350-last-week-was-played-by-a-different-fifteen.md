# ADR-350 — Last week was played by a different fifteen

**Date:** 2026-10-16
**Status:** Accepted
**Reported by:** the owner, from build 44 — *"originally showed my GW6 team, but I then made changes to it
and it incorporated those… GW6 I had Gabriel & Calvert-Lewin, it's showing Calafiori & Haaland"*
**Revises:** ADR-346 (the scores endpoint)

---

## Context

`gameweek/scores` took the caller's squad as `player_ids` and joined it to a gameweek's history. ⭐⭐ **That
is correct for a week in play and wrong for every week before it.**

The owner made transfers after GW6. The screen then credited **Calafiori** and **Haaland** with GW6 points
in a week he held **Gabriel** and **Calvert-Lewin** — and ⚠️⚠️ *the card totalled them*, so Arsenal read
**16 pts this match** for a side he did not field.

🔴 **This is the ADR-337 shape again**: not a blank where data is missing, but a **confident number that is
fiction**. A reader has no way to tell it from a true one.

## Why the design walked into it

ADR-298 already names the fact this needed: *"the one thing FPL alone knows is whose team he was in that
week."* ⭐ **That sentence was in the repository, in an ADR this very feature cites**, and the scores
endpoint was still built to take the squad from the client.

⚠️ And nothing caught it, because every test and every sample used a squad that **never changed**. ⭐ *A
fixture that cannot drift cannot exhibit a bug about drift* — the defect needed a manager who makes
transfers, which is every manager.

## Decision

**For a played gameweek, ask FPL whose team it was. For a week still in play, the caller's squad is right.**

| | squad from | why |
|---|---|---|
| every match finished | `entry/{id}/event/{gw}/picks` | only FPL knows, and a played week never changes — one request per manager per gameweek, cacheable for ever (ADR-298) |
| still in play | the caller's `player_ids` | FPL locks picks at the deadline and `my-team` returns that locked side; asking for picks it has not published would answer nothing |

### ⚠️⚠️ It never falls back

No manager id, or a failed fetch, and a played week names **nobody** — `yours` empty, `yours_known: false`.

⭐ *A wrong attribution is worse than none*, and a fallback to the current squad would restore this exact
bug silently, which is how it got here in the first place.

## Tests

Four, each mutation-checked: a played week uses the squad that played it and today's cannot leak in; no
manager names nobody; a failed fetch names nobody; a week in play uses the caller's side and does **not**
reach FPL.

⭐ The first of those builds a "now" squad with **no overlap** with the real one, so the assertion can
distinguish the fix from the bug — the thing the old fixtures could not do.

## Consequences

✅ The sample is generated from a played week with the picks fetch **stubbed**, so it exercises the real
path and stays reproducible — the same reason `_my_team` stubs its own.

⚠️ **Build 44, live to nine testers, has this bug.** Anyone who has made a transfer since GW6 is being
shown a past that did not happen. It is a server fix, so it reaches them without a new build.
