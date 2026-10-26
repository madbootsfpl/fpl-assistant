# ADR-370 — Option D was already built, and it declines

**Date:** 2026-10-26
**Status:** ❌ **`CLEAN_SHEET_WEIGHT` stays 0** — and ADR-188's pre-registered fallback is now triggered.
**Decides:** [ADR-320](./ADR-320-a-defender-rated-on-a-season-he-no-longer-plays.md) option D ·
**Re-measures:** [ADR-188](./ADR-188-a-defender-plays-for-a-team.md) on 8 gameweeks
**No production code changed.**

---

## Context

With ADR-204 declined, ADR-320's option B was gone and the owner asked to pursue **D** — *"a team-strength
term for defenders, so a club change moves the rate."* ADR-320 called it *"the largest: a modelling change,
not a parameter"*.

## 🔴 It is a parameter, and it has been built since September

**ADR-188 — "A defender plays for a team"** — accepted 2026-09-13: *"machinery built, weight held at 0."*
`CLEAN_SHEET_WEIGHT = 0.0` in `config.py`, applied to DEF/GK, adding `4 × (team_rate − league_rate)`.

⭐⭐ I wrote a spike implementing it from scratch before finding that. Its reasoning and the shipped code's
comment are the same sentence — *"own pts/90 already contains the clean sheets he kept at his old rate, so
only the difference"* — because there is only one right way to do it and ADR-188 had already found it.
⚠️⚠️ **That is the fifth time this week a fact the repository already held did not reach the work that
needed it.** The spike is deleted: *a second copy of a shape is a second thing to get wrong.*

📌 ADR-320 described D as a modelling change two weeks **after** ADR-188 built it. ⭐ *An options list is
also a claim about what exists.*

## The measurement

`spikes/192-defender-only-calibration/measure.py` already scores this weight **on the population it
applies to** — ADR-190 having established that a whole-board rank metric *cannot see* a term scoped to a
sub-population. Re-run on 8 gameweeks:

| weight | DEF/GK ρ | hit@20 | whole-board ρ |
|---|---|---|---|
| **0.00** | **0.611** | 0.21 | 0.617 |
| 0.10 | 0.610 | 0.21 | 0.617 |
| 0.20 | 0.607 | 0.19 | 0.615 |
| 0.30 | 0.606 | 0.19 | 0.615 |
| 0.50 | 0.603 | 0.21 | 0.614 |

`1 SE = 0.059`. ⚠️ **The curve declines monotonically on its own population.** Not "fails to clear" — it
makes the ranking **worse**, on the players it exists to help, over twice the data GW4 had.

## ⭐⭐ And the term is doing exactly what it was built to do

Measured before the ranking was scored, so this is not an excuse constructed afterwards. Across 157
defenders and keepers the correction moves a rate by **0.39 points per 90** on average:

```
Konsa    2.98 -> 3.90   (+0.92)     ← his actual this season is 3.84
Igor     1.85 -> 3.37   (+1.52)
Tomiyasu 4.89 -> 3.76   (-1.13)
```

⭐ **The complaint is real, the correction is right, and the ranking still gets worse.** That is the same
shape as ADR-367: a materially better input that does not produce a better output. ⚠️ *Two independent
attempts at the same conclusion is evidence about the model's ceiling, not about either attempt.*

## Decision

**The weight stays 0**, and ADR-188's pre-registered fallback is triggered:

> **Option 3: Surface it as a warning rather than pricing it.** *"⚠️ Konsa's club keeps 75% clean sheets;
> Ballard's keeps 25%."* … *"the right fallback if the weight fails §B0, and should be adopted then rather
> than leaving the blind spot unmarked."*

⭐ That is ADR-057's rule — team signals are **lenses, never xP** — and it is the one outcome here that
ships something. 📌 It is a card change, so it goes to the owner before it is built.

## What is left of ADR-320

**B** declined (ADR-367/369) · **D** declined here · remaining: **A** (loosen the all-or-nothing in-season
guard — *"a rule whose failure rate only ever rises is one that will eventually disqualify everybody"*) and
**C** (the dormant form blend). ⚠️ A is the one whose harm **grows with the season**.
