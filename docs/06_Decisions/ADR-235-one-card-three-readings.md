# ADR-235 — One card, three readings

**Date:** 2026-09-22
**Status:** Accepted
**Builds on:** ADR-222 (the pitch), ADR-213 (the published board)

---

## Context

From the Hub review: their pitch card carries **three gameweeks** — `4.9 LEE · 4.5 nfo · 4.9 EVE` — and a
menu switches the whole pitch between *Next GW*, *Next 3 GW* and *Price changes*.

⭐⭐ **A manager deciding whether to HOLD a player is asking about his run, not his Saturday.** Our card
answered only the Saturday — and the per-gameweek numbers had been published since **ADR-213** and thrown
away at the last step.

## Decision

**One card, three readings**, switched by a bar above the pitch:

| mode | what the strip says |
|---|---|
| **Next GW** | projected xP · price · opponent — the original |
| **Next 3** | three gameweeks of xP with their opponents |
| **Price** | the direction, and the crowd movement behind it |

⭐ The switch is **out in the open**, not behind the Hub's `⋯` menu. It changes what every number on screen
*means*, and that is not a thing to hide two taps deep.

### ⚠️ Fixtures are matched by gameweek, never by position

A blank gameweek means a club's third fixture is **not** the third week. Lining the xP up by index would
show the right numbers against the wrong opponents — ⭐ *three correct values arranged into a lie.* So each
fixture carries its `gameweek` and the client looks the xP up by it.

### ⚠️⚠️ The price mode says direction, and refuses to say *when*

The Hub shows `↗ >1 Week · 0.6%`. **We do not compute that.** `price_detector` answers rise/fall/stable
against a live percentile (ADR-215); it has no progress-to-threshold estimate.

⭐ So the card shows the **call and the evidence** — the direction, and net transfers this gameweek, which
is a fact rather than a forecast. *Inventing an ETA would be the "GW rating 88%" mistake: a number that
looks authoritative and is not computed.*

⚠️ And the detector stays bound to **the whole board**, not the fifteen on screen — ADR-215's own warning:
a percentile over a filtered view manufactures a top 2% *inside the filter*, so two of your players would
read as rising every single week.

---

## What the tests found

### ⭐⭐ A field describing another field has to be checked against it

The response reports `run: 3`. A mutation slicing the fixtures to **one** survived — because the test
asserted the *constant*, not the data. The answer would have claimed three and carried one, and a client
sizing its row from `run` would draw two empty columns.

### ⚠️ Presence is not truth — a third time

`isinstance(move["net_transfers"], int)` passes against a field hard-coded to `0`. Fixed by asserting that
**somebody** moved, having checked first that the snapshot's crowd fields are populated.

### ⚠️⚠️ A broken harness reports every mutation as killed

Repairing the first two tests introduced a **syntax error**, and the mutation run came back `✅ ✅` — every
mutation "caught", because the file failed to parse for a reason that had nothing to do with them.

⭐ *A harness that cannot run is not a harness that passes.* The re-run checks its own output for a syntax
failure before believing a kill. This is the same species as the *stale uvicorn* (ADR-231) and the
*not-applied pattern* (ADR-219): **the tool being wrong looks exactly like the code being right.**

### A seam is wherever the caller looks

A test patched `src.analytics.price.price_detector`; the endpoint does `from src.analytics import
price_detector`, so that is the name it reads. ⭐ *A seam is where the caller looks, not where the function
was defined.*

---

## Consequences

**Good:** the pitch answers three questions instead of one, from data already published. The price mode
tells a manager what the crowd is doing without pretending to know when FPL will act.

**Costs:** `my-team` grew from ~10 KB to ~15 KB — three fixtures per club and a price cell per player.
⚠️ Still the landing screen, still the one ADR-217/218 spent a day speeding up; worth watching.

**Open:** the Hub also colours each card by the gameweek's difficulty. ⭐ Still declined (ADR-179), and the
run mode makes the case weaker rather than stronger: three numbers already *show* the run, and colouring
them would be saying the same thing twice in a way that competes with the numbers.
