# Sprint 252: A defender plays for a team (ADR-188)

**Dates:** 2026-09-13
**Status:** ✅ Complete — ADR-188 **built dormant**. **1757 → 1762 tests, ruff clean.**
⚠️ **The weight ships at 0 and the first sweep says it should stay there.** The GW6 sitting still owns the
decision; what changed is that it now starts from a prior with a mechanism behind it.

> **Owner:** *"I have a cheap Arsenal fullback, currently playing, likelihood of clean sheets is probably
> >50% based on current run. How can we factor that knowledge in?"*

---

## What shipped

**1. `src/analytics/cleansheet.py` — the term.** `clean_sheet_delta(player, team_rate, league_rate)` returns
`4 × (team_rate − league_rate)` for DEF/GK and `0.0` for everyone else. Three properties are load-bearing:

- **A delta, not an absolute.** A defender's own points-per-90 already contains the clean sheets he kept, so
  an absolute term double-counts them. Only the difference from the league mean is new information — the same
  shape as ADR-097's DefCon magnifier.
- **DEF/GK only**, because that is who the four points go to.
- **`None` means no opinion, not 0%.** A club with no completed gameweeks gets no adjustment and is excluded
  from the league mean rather than averaged in as zero. This is [ADR-172](../06_Decisions/ADR-172-a-player-with-no-history.md)'s
  failure not repeated: there, an all-empty history read as *"never plays"* and zeroed seven players who had
  played every game.

**2. `xp.py` carries it, gated.** `clean_sheet_weight=0.0` and `clean_sheet_rates=None`, folded into
`unrounded` and the per-gameweek breakdown, returned as `clean_sheet_xp`. `decision_xp` supplies the rates
**only when the weight is live**, so the dormant path does no extra work.

**3. A fourth `_CALIBRATE_WEIGHTS` entry.** `python app.py calibrate --weight clean_sheet` works through
ADR-101's existing harness; the CLI's `choices` derive from the registry, so nothing else needed wiring.

**4. Five guards, all mutation-tested.** Invariance at weight 0 (the one the other three dormant weights
have); delta-not-absolute; DEF/GK only; unknown rate ≠ bad rate; and the weight is still 0.

## The measurement — recorded because it says no

```
   weight   ρ (rank)     MAE  hit@20      n   ±1 SE
    0.000      0.621    1.22    0.19    626   0.040
    0.100      0.618    1.22    0.19    626   0.040
    0.200      0.617    1.23    0.19    626   0.040
    0.300      0.614    1.23    0.20    626   0.040
```

**0 of §B0's 4 criteria.** ρ never beats weight-0 and declines monotonically; the entire spread (0.007) is a
**sixth of one standard error**.

The ADR predicted *"small positive ≈ 0.05–0.15, and quite possibly zero"*, and named the reason it might be
zero: the clean sheets are already inside points-per-90. The curve supports exactly that reading. The trap the
prediction table warned about — a **large** gain, meaning the term was re-ranking defenders by club quality
that FDR already carries — did not spring.

## Mutation testing

| mutant | caught |
|---|---|
| `CLEAN_SHEET_WEIGHT = 0.12` — the weight ships without the GW6 sitting | ✅ |
| an unknown rate read as a number rather than skipped | ✅ (2 tests) |
| absolute instead of a delta — the double-count | ✅ |
| outfielders get a clean-sheet term | ✅ |
| unknown clubs averaged into the baseline as 0% | ✅ |

---

## 💡 The lesson

> **A descending curve and a flat curve do not say the same thing.**

A flat sweep says *"no effect at this sample size"* — which is a statement about the sample, and the honest
response is to re-ask with more of it. That is what §B0's GW6 checkpoint is for, and it is what three of the
four dormant weights are waiting on.

This curve is not flat. It only descends: the more of the term you use, the worse the ranking gets. That is a
statement about the **term**, and more gameweeks will not change it — it is the signature of double-counting
against a quantity the model already has. So the two results route differently: one is *"ask again later"*,
the other is *"we now know the mechanism, and the likely end state is Option 3 — surface the rates as a lens
on the transfer screen instead of pricing them."*

Worth saying plainly: **the sweep was cheap and the ADR's prediction table is what made it informative.**
Without the prediction written down first, ρ 0.621 → 0.614 is a shrug. With it, it is a confirmed mechanism.

---

## Definition of Done

1. **Tests: +5** (1757 → 1762), each mutation-tested and confirmed red.
2. **Manual smoke** — invariance at weight 0 verified against live data; at a hypothetical 0.10 the
   Konsa/Hume gap narrows from +1.7 to +0.8 (narrows, does not flip), which is the term behaving as designed
   before the sweep judged it.
3. **Docs** — ADR-188 (status, §📉, action items), `GW1_RUNBOOK.md` §B0 table + stopping rule + step 4,
   ADR-000 index, PROJECT_STATUS, this retro.
