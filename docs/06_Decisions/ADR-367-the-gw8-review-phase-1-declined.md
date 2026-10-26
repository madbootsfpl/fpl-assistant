# ADR-367 — The GW8 review: Phase 1 declined

**Date:** 2026-10-26
**Status:** ❌ **Declined for the season**, by the rule ADR-204 pre-registered on 2026-09-17.
**Decides:** [ADR-204](./ADR-204-the-phase-1-gate.md), which was HELD for this date.
**No production code changed.**

---

### 📌 The rule, as written before the data existed

> **Ship the blend if, on ≥8 gameweeks:**
> 1. **ρ gain ≥ +1 SE**, **or**
> 2. **hit@20 gain ≥ +2 SE *and* ρ does not fall**, with both holding across ≥2 adjacent values of `k`.
>
> ⚠️ `k` must be **re-fitted** on the 8 gameweeks, not carried over.
> **If neither clause is met at GW8, Phase 1 is declined for the season.**

GW8 completed 2026-10-25; all ten fixtures finished. Eight rounds of history backfilled locally.

### 🎯 `k`, re-fitted on the eight gameweeks

Board-wide MAE, the same criterion ADR-204 used:

| forecaster | board MAE | bias | start call | owned MAE |
|---|---|---|---|---|
| xMins v0 (live) | 25.7 | +11.5 | 72.4% | 22.0 |
| **blend, k=1** | **18.6** | **+1.0** | **81.8%** | 21.9 |
| blend, k=2 | 20.5 | +2.2 | 79.3% | 23.3 |
| blend, k=3 | 21.8 | +3.0 | 78.3% | 24.3 |

⭐ `k = 1` again, and **board-wide MAE improves 27.7%**. ⭐⭐ It is also **no longer worse on owned
players** — 21.9 against 22.0, where at GW4 it was 25.0 against 24.0. The objection that made ADR-204
uncomfortable has gone away on its own.

### 📊 The gate, scored

| weight | ρ | MAE | hit@20 | vs live |
|---|---|---|---|---|
| xMins v0 (live) | 0.617 | 1.26 | 0.19 | — |
| **blend, k=1** | 0.650 | 1.15 | 0.21 | **+0.033 = +0.9 SE** |
| blend, k=2 | 0.643 | 1.16 | 0.19 | +0.026 = +0.7 SE |
| blend, k=3 | 0.638 | 1.16 | 0.19 | +0.021 = +0.5 SE |

`1 SE = 0.039`.

**Clause 1 — ρ ≥ +1 SE: not met.** The best value is **+0.9 SE**.

**Clause 2 — hit@20 ≥ +2 SE: not met**, and not close:

```
hit@20: 0.188 -> 0.206  (+0.019)
160 slots -> 0.6 SE unpaired;  paired across 8 rounds: +0.4 hits/round, 1.0 SE
every round improved: False
```

⚠️ It also fails clause 2's **adjacency** requirement independently: at `k = 2` and `k = 3` hit@20 does not
move at all.

**Neither clause is met. Phase 1 is declined for the season.**

---

### ⭐⭐ The finding: the flattering number did not survive four more gameweeks

ADR-204's structural result was hit@20 **0.175 → 0.263**, *"+2.1 SE unpaired… improved in all three rounds
where the two forecasters differ"*, and it recorded that as the reason to pre-register clause 2.

On eight rounds the same measurement is **0.188 → 0.206, +0.6 SE, and three of eight rounds got worse.**

⭐⭐ **The secondary metric that nearly earned a widened bar was four rounds of noise.** ADR-204 declined to
act on it and wrote instead: *"a rule that only binds when it agrees with you is not a rule."* That
discipline is the only reason this is a decline and not a shipped regression dressed as a feature.

📌 Meanwhile the **primary** moved the right way — +0.4 SE → **+0.9 SE** — on the metric that was not
cherry-picked. ⚠️ *It still did not clear the bar*, and "nearly" is what the threshold exists to refuse.

### ⚠️ One thing the pre-registration did not anticipate

`k = 1` is the **edge of the grid** ADR-204 tested (1, 2, 3, 5, 8). A finer search below 1 might clear +1 SE.

🔴 **I have not run it, deliberately.** Widening the search *after* seeing the bar missed is choosing the
answer after seeing the curve — the exact failure ADR-190 and ADR-204 both name. ⭐ *If a finer grid was
the right re-fit, it was the right re-fit a month ago.* Recorded here as a gap in the pre-registration for
the owner to rule on, not as an argument against the outcome.

### Consequences

📌 ADR-173's all-or-nothing rule stands. ADR-192 stays Proposed. The ceiling is now a **measured fact for
this season** rather than an open question — which is what ADR-204 said a decline should buy.

⭐ The candidate is not deleted: `spikes/204-board-wide-minutes/` runs on current data in one command, and
`k` re-fits itself. A future season re-opens this with no archaeology.
