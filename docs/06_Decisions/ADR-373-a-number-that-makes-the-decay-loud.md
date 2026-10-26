# ADR-373 — A number that makes the decay loud

**Decision ID:** ADR-373
**Date:** 2026-10-26
**Status:** ✅ **Accepted and built.** [ADR-371](./ADR-371-the-ratchet-is-real-and-fixing-it-buys-nothing.md)'s
**option 3**, taken after option 2 shipped rather than instead of it. The backfill now reports what share of
the board the in-season minutes term answers for, and shouts below a pre-registered floor.
**Superseded By / Replaces:** Instruments [ADR-372](./ADR-372-a-window-that-forgets.md). Applies
[ADR-203](./ADR-203-availability-is-recorded-as-it-passes.md)'s lesson **without** its mechanism.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Why, in one line

ADR-372 fixed a term that was decommissioning itself — ADR-173's guard refused **49% of players at GW2 and
78% by GW8** — and **nothing would have reported it if the fix stopped working.** The only reason anybody
noticed the first time was that an owner asked about one defender (ADR-320).

⭐⭐ **A FIX APPLIED ONCE IS NOT A FIX THAT STAYS APPLIED**, and the cheapest response to a slow failure is a
number that makes it loud.

ADR-372 listed this as a cost it shipped with — *"shipping this resets the reach to 37.7% rather than making
it visible, so nothing will report it if it starts falling again."* This closes that.

---

### 🎯 The floor is derived, not chosen

```python
REACH_FLOOR = 0.205
```

⚠️ **Not a tuning knob.** 20.5% is **what ADR-173's rule had decayed to at the moment it was replaced**,
measured on the live GW8 database. So the floor says exactly one thing, and it is falsifiable:

> If the rolling window ever reaches **less** of the board than the all-or-nothing rule it replaced, the
> window is not working.

⭐ A floor derived from a measured fact, pre-registered before it can be breached — which is the only kind
that means anything. The alternative was picking a round number and calling it a threshold.

**It is silent until the window fills.** Before five completed gameweeks the reach is *naturally* high and
falling — one completed gameweek qualifies anyone who played it — so a floor would fire on the ordinary
shape of an opening month. ⭐ *An alarm that goes off every August is reporting the calendar, not a fault.*

---

### ⭐⭐ A report, not a table — and that is the decision

ADR-203 is the obvious precedent and the obvious trap. It had to **store** availability as it passed,
because FPL serves it as a now-field with no history and nothing to backfill from.

**The reach is not like that.** It is recomputable from stored per-gameweek history for any round, at any
time — `spikes/320-rolling-guard/rolling.py` reconstructed the whole GW2→GW8 curve from the database
*after the fact*. So a table would be a second copy of a derivable number, with its own staleness.

⭐⭐ **THE SAME LESSON DOES NOT IMPLY THE SAME MECHANISM.** ADR-203's lesson is *"a now-field that is never
recorded is a fact you will not have later."* The reach fails the premise, so it earns a line of output, not
a schema change.

### Where it runs

`run_backfill` — not the hourly refresh. The reach only moves when a gameweek's rows land, which is exactly
what a backfill is: **one line per gameweek, not one per hour.** ⚠️ *An alarm that fires every hour is an
alarm nobody reads.*

It prints on **every** backfill, not only when it is bad. ⭐ *A number that appears only on a fault is a
number nobody has a baseline for, and the fault then reads as a glitch in the alarm.*

```
Backfilled GW[8]: 5 gameweek rows from 5 players. In-season minutes term answers for 252/669 players (37.7%).
```

🔴 **And it never raises.** `run_backfill`'s whole contract is that an unattended job which dies tells nobody
anything; a diagnostic bolted onto it must not be the thing that breaks that. ⭐ *A number added to catch a
silent failure must not become one.*

---

### 🧪 Definition of Done

**1 — Automated tests.** 10 new tests (6 in `tests/test_minutes.py`, 4 in `tests/test_pipeline.py` — which
had **no coverage of `describe_backfill` at all** before this). **7 deliberate defects, every one caught:**

| mutant | caught by |
|---|---|
| `REACH_FLOOR = 0.0` — the alarm can never fire | the floor-fires test + the shouts test |
| the window-filled gate removed | `test_the_floor_does_not_fire_before_the_window_has_filled` |
| `eligible` counts players with no rows | `test_the_reach_counts_only_players_whose_club_has_played` |
| `answered` counts the refused instead | 4 tests |
| the floor warning never prints | `test_..._shouts_when_the_reach_falls_through_the_floor` |
| the reach is computed but never reported | both backfill-line tests |
| `_reach` catches only `ValueError` | `test_reading_the_reach_never_takes_the_backfill_down` |

**2 — Manual smoke test.** Against the live GW8 database: `(252, 669, False)` → *"answers for 252/669
players (37.7%)"*; a forced `(40, 669, True)` produces the floor warning; `None` and a zero denominator
produce empty strings rather than a crash or a `ZeroDivisionError`.

**3 — Docs.** This ADR, ADR-371's option 3 closed, ADR-372's cost struck, index, PROJECT_STATUS.

---

### 📊 Consequences

**Good:** the one thing ADR-372 could not do for itself. The reach is now a number in the Actions log every
gameweek, with a falsifiable floor underneath it.

**Costs / limits:**
- ⚠️ **It reports; it does not act.** A breach writes a line in a log that a human has to read. ⭐ *An alarm
  wired to nothing is a slower version of no alarm* — but wiring it to a behaviour change would be a model
  decision, and this is instrumentation.
- ⚠️ **One sample per gameweek, and only when a backfill actually runs.** If the backfill is skipped the
  reach is simply not reported that week — no gap is flagged.
- ⚠️ `REACH_FLOOR` is correct for a 5-gameweek window. Change `_WINDOW_GAMEWEEKS` and the floor's derivation
  no longer holds, and nothing enforces that link.

---

### 🔗 Links

- [ADR-372](./ADR-372-a-window-that-forgets.md) — the fix this watches
- [ADR-371](./ADR-371-the-ratchet-is-real-and-fixing-it-buys-nothing.md) — where option 3 was written
- [ADR-203](./ADR-203-availability-is-recorded-as-it-passes.md) — the same lesson, a different mechanism
- [ADR-173](./ADR-173-minutes-you-have-actually-played.md) — the rule whose decay set the floor
