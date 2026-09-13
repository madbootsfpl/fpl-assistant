# ADR-187 — does planning beat greedy?

`measure.py` answers the question ADR-187 gated on, and `result-2026-09-13.txt` is the run it was closed on.

**Answer: no.** Over 24 squads and six gameweeks, with both strategies given the same three transfers:

```
  do nothing   178.8
  greedy       220.1   +41.3   ← what transferring at all is worth
  planned      222.0    +1.9   ← what foresight adds on top

  54% of squads gained NOTHING from planning · median +0.0 · max +14.3
```

Greedy captures **96%** of the available gain.

## Two things to know before re-running it

**Both strategies must get the same number of transfers.** The first run gave greedy one per gameweek (six)
against planned's three, and reported planning *losing* by 12 points a squad — a finding about the budget,
not about foresight.

**`planned` is seeded with greedy's answer**, so `planned ≥ greedy` holds by construction. Without that it
lost, because its shortlist is computed once against the opening squad while greedy re-scans after every
move — which measures shortlist size, not planning.

The XI picker here is a local enumeration rather than `best_legal_xi`, which runs a PuLP solve per call;
`check_xi_picker()` asserts the two agree before any number is reported.

## What would make this worth asking again

A **double or blank gameweek** inside the horizon (none here), **chips** (planning transfers into a Bench
Boost is a different problem), or a **materially larger search** beating +1.9 on these squads.
