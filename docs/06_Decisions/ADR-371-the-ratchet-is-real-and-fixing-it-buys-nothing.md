# ADR-371 — The ratchet is real, and fixing it buys nothing the bar can see

**Decision ID:** ADR-371
**Date:** 2026-10-26
**Status:** ✅ **Closed — the owner chose option 2 and it is built: [ADR-372](./ADR-372-a-window-that-forgets.md).**
Originally: ⏳ *Gate — measured, not built.* Option A **declines on §B0's bar** (+0.18 SE against +1 SE) and is
**dominated by option B, which already declined** — but the ratchet argument is not an accuracy argument, and
that is what shipped. 🔴 **Two corrections below: the rule measured here was looser than this ADR described,
and was re-measured before shipping.**
**Superseded By / Replaces:** Runs option **A** of [ADR-320](./ADR-320-a-defender-rated-on-a-season-he-no-longer-plays.md).
Would have replaced [ADR-173](./ADR-173-minutes-you-have-actually-played.md)'s guard. Sits beside
[ADR-204](./ADR-204-the-phase-1-gate.md) / [ADR-367](./ADR-367-the-gw8-review-phase-1-declined.md), which
declined the continuous version of the same idea.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 What was asked

ADR-320 listed four fixes for a defender rated on a season he no longer plays. B and D have both now been
measured and declined (ADR-367/369, ADR-370). **A** was left, and ADR-320 flagged it as the one whose harm
*grows with the season*:

> *"'every completed gameweek' is an all-or-nothing test that gets stricter every week it survives: by GW20
> a single missed match — one rest, one knock, one suspension in August — permanently disqualifies a player
> who has started nineteen games since. A rule whose failure rate only ever rises is one that will
> eventually disqualify everybody."*

The candidate: keep ADR-173's refusal of the ambiguous case, drop the ratchet. Judge him on the **last
`window` completed gameweeks**, forgiving up to `tolerance` misses.

---

### ⚠️⚠️ First, a candidate that was not the candidate

The first implementation expressed the threshold the way ADR-320 phrased it — *"started ≥ 4 of the last
5"*, an **absolute count**. That cannot be met at GW3, so it **switched the in-season term off entirely for
the opening weeks**: it was *stricter* than the rule it was loosening. Board MAE came back **worse at every
single setting** (25.7 → 28.3 at `last 5`), and the per-round ρ said why — worse than live at GW2–GW6,
*identical* at GW8–GW9.

⭐⭐ **A CANDIDATE THAT IS WORSE THAN THE STATUS QUO IN A REGION THE STATUS QUO ALREADY HANDLES IS NOT A
LOOSENING; IT IS TWO CHANGES WEARING ONE NAME.** Re-expressed as a **miss tolerance** —
`need = max(1, len(window) - tolerance)` — it becomes a true superset: identical to ADR-173 until the window
fills, looser after. Every number below is the second version.

⭐ The identity check is what caught it and it is cheap: at `window ≥ completed, tolerance = 0` the
candidate must reproduce `in_season_share` **exactly**. It does — on shares, and to **+0.0000 SE** on the
ranking. *A sweep whose baseline is not reproduced by its own parameterisation is comparing two different
things.*

> 🔴 **CORRECTION (same day, before shipping — ADR-372).** The sentence above claiming *"identical to
> ADR-173 until the window fills"* **is false of the rule this ADR measured.** `max(1, ...)` starts forgiving
> a miss at **two** completed gameweeks — the ratchet table below shows **106 players "rescued" at GW3**, on
> a sample of two. That is [ADR-125](./ADR-125-in-season-minutes-share.md)'s objection, not a loosening of
> it. ⭐⭐ *A rule that forgives a miss out of a sample of two has not loosened a guard, it has removed one.*
>
> ⚠️ And ADR-173's **own test suite said so** — `test_sitting_one_gameweek_out_falls_back_to_history…` is a
> two-gameweek fixture with one 0, and it fails against the rule measured here. ⭐ *I ran an identity check
> at the far end of the grid, where the two rules trivially agree, and never ran one at the near end, where
> the behaviour actually diverges.*
>
> Every number in **this** ADR is the uncorrected rule. ADR-372 gated the forgiveness on a full window and
> re-measured: `last 5, forgive 1` becomes board MAE **25.3** (not 24.7) and ρ **+0.084 SE** (not +0.094),
> the first five per-round ρ values go **bit-identical** to live, and `last 8, forgive 1` scores
> **+0.0000 SE** because its window never fills in eight gameweeks.

---

### ✅ The premise is confirmed — the ratchet is real and it is worse than ADR-320 thought

Players whose club has played, and whom the live guard refuses:

| GW | completed | with rows | refused | refused % | window answers |
|---|---|---|---|---|---|
| 2 | 1 | 610 | 300 | 49.2% | 0 |
| 3 | 2 | 626 | 368 | 58.8% | 106 |
| 4 | 3 | 654 | 423 | 64.7% | 80 |
| 5 | 4 | 659 | 453 | 68.7% | 73 |
| 6 | 5 | 667 | 486 | 72.9% | 74 |
| 7 | 6 | 667 | 505 | 75.7% | 98 |
| **8** | **7** | **668** | **521** | **78.0%** | **107** |

Monotone, as predicted. ADR-320 counted **23** affected players at GW5; at GW8 it is **115**. ⭐ *The ADR
undercounted its own finding because it sampled the top of a curve it had correctly described as rising.*

**And the level is not the point — the trend is.** 22.0% of players still qualify at GW8, with mean weekly
survival among survivors of **0.870**. Held constant that projects to **8.3% at GW15, 2.1% at GW25, 0.3% at
GW38**. ⚠️ **A pessimistic projection, deliberately labelled:** survivors are selected for being nailed-on,
so the real hazard should fall and the real numbers be higher. The *direction* is not in doubt.

⭐⭐ **SO THIS IS NOT A RULE THAT IS OCCASIONALLY STRICT. IT IS A TERM THAT DECOMMISSIONS ITSELF OVER A
SEASON** — and it is the term ADR-204 measured as already earning **2.9 SE**.

---

### 📊 The candidate is good at its job — on minutes, for both populations

Walk-forward, 8 gameweeks, `available` denominator:

| guard | board MAE | bias | start call | owned MAE | owned start |
|---|---|---|---|---|---|
| ADR-173 (the app) | 25.7 | +11.5 | 72.4% | 22.0 | 73.3% |
| last 5, forgive 1 | 24.7 | +10.6 | 73.6% | 21.8 | 73.3% |
| last 5, forgive 2 | 24.0 | +9.0 | 74.4% | 21.7 | 73.6% |
| **last 8, forgive 3** | **22.4** | **+6.0** | **76.2%** | **21.6** | 73.9% |
| last 3, forgive 2 | 22.5 | +7.2 | 76.3% | **21.3** | **74.6%** |

Monotone in tolerance on every column, and the bias halves. ⭐ **Unlike ADR-204's blend, it improves
*both* populations** — there is no owned-player regression to ship with it. On ADR-204's own framing
(*"more accurate is a claim about a population"*), this candidate does not have to pick one.

⚠️ **The denominator mattered more than the threshold.** Dividing by *available* minutes rather than
*appeared* minutes is what removes the bias (+6.0 vs +9.6 at the same setting) — because it is the
denominator, not the threshold, that bounds one bad week's influence at `1/window`. ⭐ *The window does not
protect a rested starter by refusing to answer; it protects him by capping what the answer can cost him.*

---

### ❌ And it does not move the ranking

| guard | ρ | MAE | hit@20 | vs live |
|---|---|---|---|---|
| ADR-173 (the app) | 0.617 | 1.26 | 0.19 | — |
| last 8, forgive 0 | 0.617 | 1.26 | 0.19 | **+0.0000 SE** (identity) |
| last 5, forgive 1 | 0.621 | 1.25 | 0.19 | +0.0935 SE |
| last 5, forgive 2 | 0.623 | 1.24 | 0.19 | +0.1410 SE |
| last 6, forgive 3 | 0.624 | 1.23 | 0.18 | +0.1754 SE |
| **last 8, forgive 3** | **0.624** | **1.23** | 0.18 | **+0.1830 SE** |

**§B0's bar is +1 SE. The best setting anywhere in the grid is +0.18 SE.** Every value is a gain, the gain
is monotone in tolerance, MAE improves monotonically — and hit@20 is flat at 0.19 where ρ is small and
**falls to 0.18 exactly where ρ peaks**, so §B0's "hit@20 not falling" fails at the only settings worth
arguing for.

🔴 **It is also dominated by a candidate that already declined.** Against ADR-204's blend at GW8:

| | board MAE | owned MAE | ρ vs live |
|---|---|---|---|
| ADR-173 (the app) | 25.7 | 22.0 | — |
| **B — the blend, k=1** (declined) | **18.6** | 21.9 | **+0.9 SE** |
| A — last 8, forgive 3 | 22.4 | **21.6** | +0.18 SE |

⭐⭐ **B BEATS A ON BOARD MINUTES AND ON THE RANKING, AND B WAS DECLINED. SHIPPING A AFTER DECLINING B WOULD
BE PREFERRING THE WEAKER CANDIDATE BECAUSE ITS NUMBER ARRIVED LATER.**

---

### ⭐⭐ The finding worth keeping: the correction is right player-by-player and invisible board-wide

115 players move at GW8. **5 are in the top 20; 14 are in the top 100.** The other 101 sit below rank 100,
where the ranking metric cannot see them and no pick reads them.

The individual corrections are **not** marginal, in either direction:

| player | rank | xMins now | xMins after | last 5 |
|---|---|---|---|---|
| Onyeka | 396 | **6** | **45** | 72,90,12,30,23 |
| Konsa | 167 | 79 | 90 | 90,90,90,90,90 |
| Manzambi | **2** | **90** | **64** | 27,71,85,71,65 |
| Cherif | **20** | **90** | **46** | 30,0,77,59,66 |
| Thomas | 101 | 90 | 49 | 30,62,85,67,0 |

⚠️ Note which direction the top-of-board cases run. Manzambi is **rank 2** on a projected full ninety and
has not played one in five weeks; Cherif is **rank 20** on the same. The live guard refuses them and the
*historical fallback hands them a 90* — so the loosening's effect at the top of the board is to **demote**,
correctly, two players it is currently promoting on last season's evidence. ⭐ *The all-or-nothing guard is
not conservative at the top of the board; it is conservative about changing its mind, which is not the same
thing.*

And two of ADR-320's own claims about A do not survive contact:
- *"Fixes all 23"* — it is 115, and rising.
- *"Costs ~0.4/GW of accuracy on Konsa specifically"* — it **helps** Konsa (0.879 → 1.00 share, 79 → 90
  xMins) because he has played all of the last five. ⭐ *A cost estimated against GW5's data expired when
  GW6 was played.*

⭐⭐ **A CORRECTION CAN BE RIGHT ON EVERY PLAYER IT TOUCHES AND WORTH NOTHING TO THE METRIC, BECAUSE THE
METRIC IS A CLAIM ABOUT A BOARD AND THE CORRECTION IS A CLAIM ABOUT 115 PLAYERS NOBODY PICKS.** This is
ADR-204's top-of-board finding read backwards, and it is the fourth candidate in a row to land here.

---

### 🎯 The one question left, and it is not an accuracy question

§B0's bar governs **accuracy bids**, and as an accuracy bid this declines cleanly — 5× short, dominated,
hit@20 falling. ⚠️ **But the ratchet argument was never an accuracy argument**, and it is not answered by
+0.18 SE:

> A term that answers for 22% of players at GW8 and trends toward single digits is **switching itself off**,
> and the app will not notice, because nothing measures the share of the board a term still speaks for.

⭐ What makes that admissible rather than a rationalisation after a bad number: **ADR-320 wrote it on
2026-09-27, a month before any of these numbers existed.** It is pre-registered, by the ADR that raised it.
The same test ADR-204 applied to its own clause 2 — *"the reason is independent of the outcome, which is the
only thing that makes it admissible"* — passes here.

**For the owner, three ways to close this:**

1. **Decline A and leave the guard.** Honest and consistent with B and D. ⚠️ Accepts that the in-season
   term's 2.9 SE is a **decaying asset**, and that the decay is now measured and recorded rather than
   discovered next August.
2. **Ship `last 5, forgive 1` as a correctness change, not an accuracy one.** The case: a true superset of
   today's rule, **+0.09 SE (not worse) with no regression on either population**, MAE improving, hit@20
   unchanged at 0.19, and an unbounded failure mode replaced by one bounded at `1/window`. ⚠️ This is a
   deliberate widening of §B0 of exactly the kind ADR-204's clause 2 was, and should be decided as one — not
   slipped through on "it's only a guard".
3. **Decline A and instrument the decay instead.** Add the qualifying-share number to the pipeline so the
   term's reach is visible, and revisit when it crosses a pre-registered floor. ⭐ *The cheapest response to
   a slow failure is a number that makes it loud.*

> ✅ **The owner chose 2 — and then 3 as well.** Option 3 is built as
> [ADR-373](./ADR-373-a-number-that-makes-the-decay-loud.md): the backfill now reports what share of the
> board the in-season term answers for, with a floor of **20.5%** — *what ADR-173's rule had decayed to at
> the moment it was replaced*, so the alarm says one falsifiable thing rather than a round number.
>
> ✅ **The owner chose 2.** Built as [ADR-372](./ADR-372-a-window-that-forgets.md) — on the *corrected*
> rule, and at ADR-320's pre-registered `≥ 4 of the last 5` rather than the `last 3` setting that scored
> better, because ⭐ *a value picked off a curve drawn on eight gameweeks has already spent some of its
> result* (ADR-204, the lesson that cost ADR-367 a feature). ⚠️ Option 3 was **not** taken, so nothing
> reported the reach if it started falling again — **since closed by ADR-373.**

**Recommendation (as written, before the owner's call): 2, at `last 5, forgive 1`** — with 3 as the fallback if the owner would rather not widen
§B0 twice. The reason is not the +0.09 SE; it is that **no setting of this candidate is worse on anything
measured**, which is a materially different position from B (which shipped an owned-player regression) and
D (which made ρ worse). ⚠️ If 1 is chosen, 3 should be taken anyway — the decay is real either way.

---

### 📊 Consequences

**Good:** ADR-320 is now fully measured — A, B, C(untouched), D — rather than three-quarters argued. The
ratchet is confirmed, quantified, and projected. The all-or-nothing guard's behaviour at the *top* of the
board turns out to be the opposite of what "conservative" suggested, which is new.

**Costs / limits:**
- ⚠️ **8 gameweeks, and the window variants only diverge from live once the window fills** — so `last 5`
  settings carry their entire result on GW6–GW8. `last 3` has more rounds and less window.
- ⚠️ The projection to GW38 assumes a constant hazard it almost certainly does not have. It is directional.
- ⚠️ **Blank gameweeks remain unhandled** and the window makes the exposure *worse*, not better: a missing
  row now counts as a forgiven miss against the `available` denominator rather than disqualifying him
  outright. No blanks have landed yet; ADR-173's caveat is still live and now has a second claimant.
- **C (the dormant form blend) is still unmeasured** and is the last unopened option on ADR-320.

---

### 🔗 Links

- [ADR-320](./ADR-320-a-defender-rated-on-a-season-he-no-longer-plays.md) — the gate this runs option A of
- [ADR-173](./ADR-173-minutes-you-have-actually-played.md) — the guard, and why it refuses
- [ADR-204](./ADR-204-the-phase-1-gate.md) · [ADR-367](./ADR-367-the-gw8-review-phase-1-declined.md) ·
  [ADR-369](./ADR-369-the-edge-of-the-grid.md) — option B, measured and declined
- [ADR-370](./ADR-370-option-d-was-already-built-and-it-declines.md) — option D, same
- `spikes/320-rolling-guard/` — `rolling.py` · `rolling_on_points.py` · `who_it_moves.py`
