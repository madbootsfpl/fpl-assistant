# Sprint 255: Spend the transfers you hold (ADR-191 proposed)

**Dates:** 2026-09-14
**Status:** 📋 **ADR-191 proposed** — a gate, not a build. One spike committed
(`spikes/191-two-transfers/`), no behaviour change. **1758 tests, unchanged.**

> **Owner:** *"I have £1.0m in the bank, I have 2 free transfers for the next gameweek, so is this advice the
> best or most effective? … Should we not be triangulating number of available transfers, spending the money
> on the starting 11, looking at budget and then making a decision?"*

---

## Checking the unfounded half first

The report contained two claims and one of them was wrong, so it was worth separating them before
investigating. *"Bringing Rayan in provides a good 12th man"* — **it does not.** `suggest_transfers` runs
`xi_aware=True`, so a move's gain **is** the lift to the best legal XI; a buy who would sit on the bench
scores +0.0 and never appears. The recommended buy made the XI in **60 of 60** squad-runs.

That mattered for where to look next: the fault is not *which* player is recommended, it is **how many**.

## The measurement

| | 30 random squads (2 seeds) | RoboTS | TS |
|---|---|---|---|
| one move (today's answer) | +21.7 / +22.2 | +7.9 | +12.6 |
| two moves, greedy | +40.1 / +40.6 | +12.4 | +22.6 |
| two moves, planned | +40.6 / +40.9 | **+18.3** | +22.6 |

**The second transfer is worth roughly as much again as the first** — and `gameweek.py` already asks
`suggest_transfers` for two moves, shows one, and spends the second on answering *"bank or use"*.

Three further faults fell out of reading the code around it: the app **doesn't know** how many free transfers
you hold (the Transfer tab's input feeds `bank_or_use` alone); the affordability cliff's *"wait"* is **never
compared** to *"use your second transfer now"*; and the shortlist is a **menu of alternatives, not a plan** —
both moves are priced against the same squad and the same bank, so their gains do not add.

## The split, and why §2 is gated rather than built

Joint pair-planning is worth **+0.4 mean** across random squads (8/30 saw any gap) and **+5.9 on RoboTS**,
where greedy opens Hume → Ballard and thereby blocks *Mukiele → Ballard + Watkins → Isak* — the same incoming
player, routed through the sale that leaves enough money for a second move.

I think random squads understate this: they have so much headroom that almost any two moves gain a lot, so the
*order* matters less than it would on a well-built squad. **But believing that is not measuring it, and n=2
real squads is a hint, not evidence.** So §2 is recorded with what would unblock it, not built.

⚠️ **Option 4 refused explicitly**: *"ADR-187 already closed multi-transfer planning."* It did not. ADR-187
measured planning **across** gameweeks — one transfer per gameweek, money carried, foresight worth 4%. This is
**two free transfers within one gameweek, sharing a budget**. The first is about *when*; this is about *how
many*.

---

## 💡 The lesson

> **A number computed for one question and discarded is invisible in a way a missing number is not.**

The second-best transfer has been in memory on every render since ADR-173. It was fetched deliberately, used
honestly, and dropped. A feature that was never built leaves a hole someone eventually notices; a value that
is computed and thrown away leaves behind *a comment explaining why two were requested*, which reads as
thoroughness.

And the narrower one, which ADR-186 nearly taught already: **two features answering competing questions have
to be made to compete.** *"Save your money"* and *"use your second transfer"* are both correct; showing
whichever happens to render presents an arbitrary choice as a recommendation.

---

## Definition of Done

1. **Tests: unchanged (1758)** — no behaviour changed; the deliverable is a measurement and a gate.
2. **Manual smoke** — the spike run at two seeds and against both saved squads; results in
   `result-2026-09-14.txt`.
3. **Docs** — ADR-191, ADR-000 index, Roadmap, this retro.
