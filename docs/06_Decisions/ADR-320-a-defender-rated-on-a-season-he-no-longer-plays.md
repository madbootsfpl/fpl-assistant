# ADR-320 — A defender rated on a season he no longer plays

**Date:** 2026-09-27
**Status:** ⏳ **Gate — measured, not built.**
**From:** the owner — *"Why is Arsenal's Konsa so low rated on predicted points score? This has been
persistent over the last few weeks."*

---

## The short answer, first

**It is not a bug, and the "persistent" is the real finding.**

Konsa's projected rate is **2.98 per 90**. His record:

| | minutes | points | per 90 |
|---|---|---|---|
| 2023/24 | 3069 | 91 | 2.67 |
| 2024/25 | 2936 | 103 | 3.16 |
| 2025/26 | 3035 | 100 | **2.97** |
| **this season** | 281 | 12 | **3.84** |

⭐ **The model is reproducing his three-season average almost exactly**, because that is what it is built to
do. He is a centre-back who has scored around three points per ninety for three years running — clean
sheets and appearance points, almost no attacking returns. Against Gabriel (4.41 / 4.46 / 6.84) that is a
genuinely different player, not a mis-rating.

⚠️ So **no fix below makes Konsa a premium defender**, and the honest reply to the owner says so before it
says anything else.

## But three things do hold him down, and all three are real

### 1 — The rate cannot see that he changed clubs

⭐⭐ **2.98 is his *Aston Villa* rate, and he plays for Arsenal.** A defender's points are mostly his team's
clean sheets, so a move between clubs of different defensive strength changes his expected return in a way
`baseline_by_code` — keyed on the *player* — has no term for. ⚠️ *The most predictive single fact about a
defender's next fixture is which team he is in, and it is the one fact the rate ignores.*

This is the part that reads as "persistent": it will not correct itself, ever, because history does not
update.

### 2 — This season does not count

The in-season form blend exists and is **dormant**: `form_weight` defaults to **0** (ADR-060), so
`blend_form` never runs. ⭐ Konsa is playing at **3.84 per 90** this season — better than any of his three
historical seasons — and that number has **zero** influence on his projection after five gameweeks.

### 3 — His minutes weight is last season's

`in_season_share` returns a share **only** for a player who appeared in *every* completed gameweek with
minutes in each. Konsa's GW1 was 0 minutes, so he fails that test forever and falls back to last season's
`availability_weight` = **0.879**, while actually playing **1.00** of the last three gameweeks.

⚠️⚠️ **This is not about Konsa — it is 23 players**, and he is one of the mildest cases:

| player | weight used | last 3 GW | gap |
|---|---|---|---|
| Onyeka | 0.07 | 0.83 | **0.76** |
| Danso | 0.31 | 1.00 | 0.69 |
| Marmoush | 0.25 | 0.92 | 0.67 |
| Pinnock | 0.36 | 1.00 | 0.64 |
| Martinez | 0.38 | 1.00 | 0.62 |
| Mings | 0.30 | 0.91 | 0.60 |
| … | | | |
| Konsa | 0.879 | 1.00 | 0.12 |

⭐ **The guard is deliberate and its reasoning is sound** — its docstring is explicit that refusing the
ambiguous case beats guessing at it, *"a player who sat one out returns None and keeps his historical share,
and cannot be cratered by a single rest"* (ADR-173, deferring ADR-125 on sample size). ⚠️⚠️ But **"every
completed gameweek" is an all-or-nothing test that gets stricter every week it survives**: by GW20 a single
missed match — one rest, one knock, one suspension in August — permanently disqualifies a player who has
started nineteen games since. *A rule whose failure rate only ever rises is one that will eventually
disqualify everybody.*

## Why this is a gate and not a commit

🔴 **Every one of these changes every xP in the app**, and xP is what the captain pick, the transfer
suggestion, the Squad Lab fifteen and the confidence score are all computed from. ⭐ *A change to the
number underneath every other number is not a bug fix; it is a new model, and it gets a gate.*

⚠️ It also sits directly beside the **Phase 1 xMins gate (ADR-204)**, which is held on a date — re-decided
once **GW8 is played, on or after 2026-10-26**, against a rule written before the data existed. Deciding
this one on its own would pre-empt that, which is the thing ADR-204 exists to prevent.

## The options, for the gate

**A — Loosen the in-season guard** from *"every completed gameweek"* to a **rolling window** (say: started
≥ 4 of the last 5) or a **minimum-sample** rule. ⭐ Keeps ADR-173's refusal of the ambiguous case while
removing the ratchet. Fixes all 23, costs ~0.4/GW of accuracy on Konsa specifically.

**B — Blend the two** rather than choosing: weight in-season share against history by how much in-season
evidence there is, which is what `cold_start_rate` already does for the rate. ⭐ No cliff, no threshold to
argue about — the number moves as the evidence arrives.

**C — Turn on the in-season form blend** (`form_weight > 0`). Already built, already tested, dormant by
decision. ⚠️ Biggest single effect on Konsa and the widest blast radius of the three — and ⭐ *the reason
it is dormant is that nobody has measured what it does to the board*, which is the work, not the switch.

**D — A team-strength term for defenders**, so a club change moves the rate. ⭐ The only one that addresses
the actual complaint. ⚠️⚠️ Also the largest: it is a modelling change, not a parameter, and it needs a
backtest before anyone believes it.

**Recommendation: B, then measure D.** B is the smallest change that removes a rule which gets worse with
time; D is the one that answers the question the owner actually asked, and it should be measured against
`backtest.py` before it is proposed.

## What is *not* proposed

⚠️ **Special-casing Konsa, or any player.** The complaint arrived as one name and is 23 players and a
dormant blend; ⭐ *a fix shaped like the report rather than the cause is how a model acquires exceptions.*
