# ADR-375 — The defence he played behind

**Decision ID:** ADR-375
**Date:** 2026-10-30
**Status:** 📋 **Gate — measured enough to propose, not built.** A baseline error in `clean_sheet_delta`,
found while answering a tester complaint. **Nothing in `decision_xp` changes until this is agreed.**
**Superseded By / Replaces:** Reopens [ADR-188](./ADR-188-a-defender-plays-for-a-team.md) /
[ADR-195](./ADR-195-team-defence-is-xgc-not-clean-sheets.md) with a **correction to their baseline**, not a
re-run — [ADR-370](./ADR-370-option-d-was-already-built-and-it-declines.md) declined the weight and this
proposes *why*. Answers the part of [ADR-320](./ADR-320-a-defender-rated-on-a-season-he-no-longer-plays.md)
§1 that four options never touched.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 What started it

Testers who own Konsa are being advised to sell him, and the owner's call is that the advice itself is the
risk: *"that's not a runner, it's one giant exposure to our credibility."*

The engine's view, verified:

| | rank | 1-GW xP | price | owned |
|---|---|---|---|---|
| Gabriel (ARS) | **DEF #3** of 217 | 5.1 | £7.9 | — |
| **Konsa (ARS)** | **DEF #50** of 217 | **2.70** | £4.7 | **19.8%** |

⭐⭐ **TWO CENTRE-BACKS, THE SAME BACK LINE, THE SAME CLEAN SHEETS — #3 AND #50.** Part of that is real
(Gabriel scores goals and Konsa does not). The rest is that Konsa's rate was earned at Aston Villa and
Gabriel's at Arsenal, and nothing in the model knows the difference.

⚠️ **And the crowd disagrees with us, loudly.** Recorded flow (ADR-210): GW9 **127,475 in against 4,869
out — net +122,606, a 26:1 ratio** — in the week our engine began recommending the sale.

---

### 🔴 The finding: the delta is measured against the wrong baseline

`clean_sheet_delta` prices a club's clean sheets as a **delta**, and its docstring says exactly why:

> *"the player's own historical pts/90 already contains the clean sheets he kept **at his old rate**. Adding
> an absolute clean-sheet term would double-count them… so only the difference is priced."*

**The reasoning is right and the baseline is wrong.** It subtracts the **league** rate, which removes the
*average* player's historical clean sheets — not **his**. League rate is 0.287; Arsenal's is 0.625:

| player | club now | his own history | delta today | delta, personal baseline | change |
|---|---|---|---|---|---|
| **Konsa** | 0.625 | **0.235** | +1.35 | **+1.56** | **+0.21** |
| White | 0.625 | 0.491 | +1.35 | +0.54 | **−0.81** |
| Gabriel | 0.625 | 0.478 | +1.35 | +0.59 | **−0.76** |
| Milenković | 0.125 | 0.297 | −0.65 | −0.69 | −0.04 |

⭐⭐⭐ **EVERY ARSENAL DEFENDER GETS THE IDENTICAL +1.35, BECAUSE THE TERM IS A PURE CLUB PROPERTY.** So the
double-count the docstring set out to avoid is still there, merely relocated: it **over-credits a player who
was already behind a good defence** (White needs +0.54 and gets +1.35) and **under-credits a genuine mover**
(Konsa needs +1.56 and gets +1.35, the same number as the teammates who need it least).

⭐ **This is a candidate explanation for ADR-370's decline, which is the point.** That sweep found the term
*right about Konsa* (2.98 → 3.90 against an actual 3.84) and ρ falling monotonically board-wide — exactly the
signature of a correct direction applied through a baseline that mis-prices everyone else. ⚠️ A mechanism, not
a proof. Proving it is the gate.

---

### ⚠️ Specifying it broke my first two attempts, and that is recorded on purpose

**Attempt 1 — detect the club change from xGC.** History carries `expected_goals_conceded` and the live row
carries `xgc`, so the defence behind his old rate is comparable with the one he is behind now. The idea needs
the ratio to be ≈1 for anyone who did **not** move. **It is not:** only **49%** of DEF/GK sit within ±15% of
1.00, and the largest "movers" include **Ben White at 0.52**, who has been at Arsenal for years. ⭐ *It
detects "my defence improved", not "I changed clubs"* — which is option D's job, already declined.

**Attempt 2 — a personal baseline, absolute.** `4 × (team_now − his_own_history)`. This introduces a
**systematic level shift**: across 187 DEF/GK it *raises* 124 and lowers 46, mean **+0.23 pts/match**. ⭐⭐ *A
term that moves one position's whole population in one direction is a level shift wearing a bias
correction's clothes* — and it would likely have failed the gate for that mundane reason while looking like
a failure of the idea.

**The cause is a scale mismatch**, so the fix is to make both deltas **era-relative** — each measured against
its own season's league average, which is derivable from the history table:

```
delta = CLEAN_SHEET_POINTS × [ (team_now − league_now) − (his_cs_rate − league_in_his_seasons) ]
```

The second bracket is *"how much better his old defence was than its own era"* — which is the part already
baked into his historical rate, and therefore the part to remove. ⭐ **For a player who stayed at an average
club the bracket is ~0 and the formula collapses to today's behaviour**, which is the self-nulling property
attempt 1 lacked.

| league baseline | mean correction | median |
|---|---|---|
| attempt 2, absolute | **+0.23** | +0.18 |
| era-relative, all positions | +0.176 | +0.139 |
| **era-relative, DEF/GK only** (position-matched) | **+0.135** | **+0.089** |

Per-season league rates, DEF/GK, start-weighted: 2022/23 **0.297** · 2023/24 **0.244** · 2024/25 **0.248** ·
2025/26 **0.280** · this season (observed, 8 GWs) **0.287**.

### 🎯 The open question, and it *is* the gate

🔴 **The level shift shrinks from +0.23 to +0.135 and does not vanish, and I do not know why.** Leading
candidate is selection — the 187 DEF/GK who have three seasons of starts *and* a place in this season's
squad lists may genuinely have come from slightly below-average defences. It could equally be residual bias.

⭐⭐ **The two effects are separable, and ρ is rank-based, which is what makes this gateable.** Spearman
cannot see a constant added to every DEF/GK's rate — it only sees the *differential* part. So:

1. **Variant A — era-relative, as specified above.**
2. **Variant B — demeaned:** the same correction minus its own population mean, so the level shift is zero
   by construction and only the differential survives.

If **B ≈ A**, the +0.135 was never doing anything and the term's value is its differential. If **B > A**, the
residual was bias and demeaning is part of the design. If **both decline**, the baseline was not ADR-370's
problem and this whole line closes with it. ⭐ *A gate that cannot come back "the premise was wrong" is not a
gate.*

---

### 📋 What is proposed

1. Add `league_cs_by_season` + `historical_cs_edge` to `src/analytics/cleansheet.py` (pure, from data already
   stored: `clean_sheets`, `starts`, `season_name`).
2. Change **only** `clean_sheet_delta`'s baseline. Its shape, its guards, its zero-for-outfield and its
   unknown-rate fallback all stay (ADR-172's lesson: *an unknown rate must never read as a bad one*).
3. **Re-sweep `CLEAN_SHEET_WEIGHT`** — variants A and B, scored **on DEF/GK** per
   [ADR-190](./ADR-190-the-gw4-sitting.md)'s rule, against the **post-ADR-372 baseline** (ρ 0.620, not
   ADR-367's 0.617).
4. §B0's bar unchanged: +1 SE on ρ across ≥2 adjacent weights, MAE and hit@20 not falling.

**Coverage:** 187 of 291 DEF/GK (**64%**) have a personal baseline; the other 104 fall back to the league
rate, which is today's behaviour. ⚠️ Promoted clubs and young players are most of the gap, and they are
disproportionately the players whose rate is *least* trustworthy — so the fix is weakest exactly where the
problem is worst.

---

### 📊 Consequences

**If it clears:** ADR-320 §1 — *"the rate cannot see he changed clubs"* — is finally priced, through the one
mechanism that does not need to know a transfer happened. Konsa moves without Gabriel and White being moved
the same amount.

**Costs / limits:**
- ⚠️ **8 gameweeks**, and `team_clean_sheet_rate` is an observed share over those 8 — Arsenal's 0.625 is 5 of
  8. A club rate on 8 matches is noisy and the term inherits that.
- ⚠️ 🔴 **The level shift is unexplained.** Gating A and B is how it gets resolved, not a way around it.
- ⚠️ **64% coverage, biased against the players who need it.**
- ⚠️ This is a **defender** fix. It does nothing for the MID/FWD half of ADR-320 §1.
- 🔴 **It does not help this week.** The credibility exposure is live now, and a gate takes a sprint — which
  is why the sell-side guard ([ADR-376](./ADR-376-not-on-a-number-we-know-is-biased.md)) ships separately and
  does not wait for this.

---

### 🔗 Links

- [ADR-320](./ADR-320-a-defender-rated-on-a-season-he-no-longer-plays.md) §1 — the complaint this aims at
- [ADR-188](./ADR-188-a-defender-plays-for-a-team.md) · [ADR-195](./ADR-195-team-defence-is-xgc-not-clean-sheets.md) — the term and its instrument
- [ADR-370](./ADR-370-option-d-was-already-built-and-it-declines.md) — the decline this proposes a cause for
- [ADR-190](./ADR-190-the-gw4-sitting.md) — score on the population the change touches
- [ADR-376](./ADR-376-not-on-a-number-we-know-is-biased.md) — the credibility guard that does not wait for this
