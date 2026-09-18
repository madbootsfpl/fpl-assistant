# Architectural Decision Record: The GW4 sitting — nothing ships, and one bar cannot be cleared

**Decision ID:** ADR-190
**Date:** 2026-09-13
**Status:** ✅ **Accepted — sitting held, results recorded.** **All four weights stay at 0.**
One constant re-measured and **shipped** (`CLEAR` 1.0 → 1.3); one re-measure found to be **impossible as
written**. 1762 tests, ruff clean.
**Superseded By / Replaces:** Executes [ADR-101](./ADR-101-calibration-methodology.md) / `GW1_RUNBOOK` §B0 at
its first checkpoint. Records a **limit of the harness** that §B0 did not anticipate. **No `decision_xp`
change** — the recipe is byte-identical.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The runbook has said since GW1 that **GW4 is the first honest attempt** at the dormant weights. Four rounds are
now in `player_history` and `calibrate` runs.

Two things made the sitting overdue in a way nobody would have noticed. The roadmap's *"blocked on
gameweeks"* section held **two different gates under one heading** — the 900-minute bar (still real: **0 of
657** clear it) and the ≥4-gameweek bar (lifted). When one of two gates lifts, nothing announces it; the row
still reads *blocked* and everything under it stays parked.

---

### 🎯 Decision & Justification

**Nothing ships. All four weights stay at 0.** But the four results are not the same result.

#### The sweeps

```
weight-0 baseline everywhere:  ρ 0.621 · MAE 1.22 · hit@20 0.19 · n=626 · 1 SE = 0.040

FORM_WEIGHT          0.0 → 0.5   ρ 0.621 → 0.626   ascending,   +0.005
SET_PIECE_WEIGHT     0.0 → 0.5   ρ 0.621 → 0.622   flat,        +0.001
DEFCON_MAGNIFIER     0.0 → 0.5   ρ 0.621 → 0.622   flat,        +0.001
CLEAN_SHEET_WEIGHT   0.0 → 0.3   ρ 0.621 → 0.614   DESCENDING,  −0.007   (ADR-188)
```

Criterion 1 asks for **+0.040**. The largest movement in any direction, across all four weights and every
swept value, is **0.007**.

#### ⚠️ The check that changes the reading: are the terms even live?

A flat curve means *"no signal"* only if the mechanism actually reaches the projection. This project has
shipped a guard that protected nothing four times, so the curve was not taken at face value. Measured against
the **same call the harness makes**:

| weight | players whose xP moves (of 657) | max Δ xP | **ρ(rank at 0, rank at w)** |
|---|---|---|---|
| `FORM_WEIGHT` @0.5 | **291** | 3.10 | **0.98716** |
| `CLEAN_SHEET_WEIGHT` @0.5 | **172** | 1.50 | **0.98095** |
| `DEFCON_MAGNIFIER_WEIGHT` @0.5 | 69 | 0.30 | **0.99977** |
| `SET_PIECE_WEIGHT` @0.5 | **5** | 0.20 | **0.99998** |

That last column is the finding. **A term that produces a ranking 0.99998 correlated with the one it is being
compared against cannot possibly change that ranking's correlation with reality by 0.040.** The bar is not
merely unmet for set-piece and DefCon — it is **unreachable**, and it would have stayed unreachable at GW6, at
GW10, and at any n.

The two terms that *do* re-rank the board (form and clean sheet, ρ≈0.98) are exactly the two whose ρ curve
actually moved. The measurement is internally consistent: **the harness sees what re-ranks and is blind to
what does not.**

#### Why set-piece in particular can never clear it — and it is by design, not a bug

`set_piece_bonus` is applied **only off the `hist` tier**: an established taker's ≥900-minute baseline already
prices his penalties, so adding the bonus on top would double-count (ADR-096, correctly).

```
players holding a #1 set-piece duty : 43
...the term can reach               :  9      (the rest are on the trusted 'hist' tier)
```

And the `hist` tier is decided by **completed past seasons** — `history_by_code` holds 2022/23 … 2025/26 and
nothing from the current one. So **the eligible population is fixed for the season at 9 of 657.** More
gameweeks add actuals; they do not add eligible players. Nine players cannot move a rank correlation over 626.

**`SET_PIECE_WEIGHT` is therefore not "failing on sample size". It is unmeasurable by a whole-board metric,
permanently.** Carrying it to GW6 and GW10 to fail twice more is precisely the furniture §B0's stopping rule
exists to prevent.

#### 📉 The constants re-measured in the same sitting

| constant | GW1 | GW4 (two seeds) | move | outcome |
|---|---|---|---|---|
| `WHISKER` (captain margin p25) | 0.20 | **0.30 · 0.30** | 0% | **keep 0.3** |
| `CLEAR` (captain margin p75) | 1.00 | **1.30 · 1.30** | **+30%** | ⚠️ **ship 1.3** |
| `CONCENTRATED` (p75) | 0.35 | **0.374 · 0.370** | +6% | keep 0.35 |
| `HEAVY` (p90) | 0.45 | **0.446 · 0.435** | −2% | keep 0.45 |
| `EXODUS_PRESSURE` (p10) | −7,996 | **−3,901** | **+51%** | ⚠️ **cannot be re-measured — see below** |

**`CLEAR` 1.0 → 1.3 shipped**, because §B0 pre-registered exactly that: *ship the new value if it moves ≥20%*.
The direction is the point — leads **widened** (max 2.80 → 4.30) as real returns replaced preseason
projections, so holding 1.0 would have kept the number and lost the meaning, quietly promoting the middle of
the distribution into *"a clear pick"*. A quartile is a claim about a distribution; when the distribution
moves, the constant moves with it or it stops being the thing it was defined as.

**`EXODUS_PRESSURE` could not be re-measured as the rule requires, and the rule cannot be executed at all.**
`price_pressure` is built from `transfers_in_event` / `transfers_out_event` — **current-event fields**, and
`player_history` stores no per-round transfer columns. So the app holds *one* week of this quantity at any
moment. The "re-measure on ≥4 gameweeks" instruction has no data to run on; what it actually produced was a
**second single-week sample**, from a different week, differing by 51%.

⚠️ **Two samples of a varying quantity that disagree by 51% do not establish a new value — they establish
that it varies.** Declaring −3,901 "the real p10" would repeat ADR-183 exactly. What the pair *does* establish
is that a **fixed constant is the wrong mechanism**: the threshold was defined as *"the worst tenth"*, and on
this week's distribution it flags **2 of 190** players rather than ~19. A percentile computed live would be
the worst tenth every week by construction. That is a design change and it is **out of scope here** — it wants
its own gate — but the measurement is recorded so the case does not have to be rebuilt.

---

### 💡 Options Considered

#### Option 1: Record the results, ship nothing, close set-piece as unmeasurable *(Chosen for the first two thirds)*
Honest to the pre-registered bar and cheap. Closing set-piece is proposed but **not executed here** — see
Consequences.

#### Option 2: Lower criterion 1 because nothing can clear it
Rejected, and it is worth naming why in writing, because the argument is seductive: *"the bar is unreachable,
so the bar is wrong."* The bar being unreachable for a term touching nine players is **the correct behaviour of
a bar** — it is the term's scope that is the problem, not the threshold. §B0 says amending a criterion is
legitimate in a commit that explains why, and silently amending it after seeing the result is not. Amending it
*to let something pass* is the thing it was written to stop.

#### Option 3: Measure a scoped term on the population it scopes to
The real fix, and the proposal §B0's methodology is missing: judge `SET_PIECE_WEIGHT` on the **9 eligible
players**, not diluted across 626. A term that touches 1.4% of the board is asked a question about the whole
board and answers "no" no matter what it does. **Not built** — it is a change to the calibration methodology
and wants its own gate.

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:** the first checkpoint was actually held rather than drifted past; four weights have
  recorded results instead of assumptions; one constant was corrected on evidence; and two of the four weights
  are now known to be **unmeasurable rather than unmeasured**, which is a different and more actionable fact.
* **Negative Impact / Trade-offs:** nothing got faster or more accurate today. `CLEAR` = 1.3 makes *"a clear
  pick"* rarer, which is the intended correction but will read as the app becoming less decisive.
* **Risks & Mitigations:**
  - **Risk:** `CLEAR` was re-measured on 300 random squads at two seeds — random squads are not real squads.
    **Mitigation:** two seeds agreed to 0.00, and the same sampler produced GW1's number, so the comparison is
    like-for-like even if the absolute level is not a population truth.
  - **Risk:** treating set-piece as unmeasurable could be wrong if the eligible population grows.
    **Mitigation:** checked — `history_by_code` holds only completed seasons, so the tier is fixed until
    rollover. If current-season minutes ever feed the baseline, this claim expires and the ADR says so.
  - **Risk:** the exodus finding is itself two samples. **Mitigation:** it is deliberately recorded as *"it
    varies"* and not as a new value; no constant changed.

---

### 🛠 Implementation & Migration
* **Components Affected:** `analytics/captain.py` (`CLEAR` 1.0 → 1.3), `tests/test_captain.py`,
  `spikes/190-gw4-sitting/`, `GW1_RUNBOOK` §B0, Docs
* **Action Items:**
  - [x] Sweep all four weights; record every curve in this ADR
  - [x] Verify each term is live before reading its curve (the rank-correlation column)
  - [x] Re-measure the quartile constants at **two seeds**, ship `CLEAR` = 1.3 with a guard on the new band
  - [x] Record why `EXODUS_PRESSURE` cannot be re-measured as §B0 instructs
  - [x] **CLOSED 2026-09-13 (owner's call): `SET_PIECE_WEIGHT` removed, not left at 0.** The weight, the
        `player_xp` parameter, the rate branch, the `set_piece_xp` output, the `explain.py` clause, the
        `_CALIBRATE_WEIGHTS` entry and `src/analytics/setpieces.py` are all gone. Verified byte-identical on
        live data (**657 players, 0 projections changed**). ADR-096 carries the closure note. **Duty is still
        shown** — the price went, the signal did not.
  - [x] **Option 3 tried once (2026-09-15):** re-scored ADR-188's clean-sheet term on **DEF/GK only**
        (`spikes/192-defender-only-calibration/`). **The hypothesis was refuted** — restricted to the 277 rows
        it applies to the term declines *more* steeply (ρ −0.026 vs −0.014 whole-board, MAE 1.33 → 1.38).
        ⭐ Worth doing anyway: *a whole-board decline and a sub-population decline are different facts, and
        only one of them was on the record.* Option 3 remains the right method; it just does not rescue this
        term.
  - [x] **GATE CLOSED 2026-09-18 — [ADR-210](./ADR-210-a-threshold-reads-the-distribution-it-describes.md).**
        A live percentile replaces the fixed constant. ⭐ And it supplies the mechanism this ADR stopped one
        line short of: the two samples 51% apart are not noise, they are **two points on a ramp** —
        `transfers_*_event` is a counter that resets at each deadline and fills up across the week, so the
        reading is a function of how far into the cycle you look (−3,901 at ~1 day, −14,992 at ~5 days).
        ⭐ *Before concluding a quantity is noisy, check whether the two samples sit at the same point in
        whatever cycle it lives in.*
  - [ ] At GW6: re-sweep `FORM_WEIGHT` only — it is the one term that both re-ranks the board and points the
        right way. The other three have their answers.

#### ✅ Always
- [ ] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

---

### 💡 The lesson

> **A measurement can fail because the thing is absent, or because the instrument cannot see it — and a flat
> curve looks identical either way.**

Four weights produced four nearly-identical flat lines. Read at face value they say the same thing: *no
signal, wait for more data.* One column — how much each weight changes the ranking **at all** — splits them
into two kinds. Form and clean sheet genuinely re-rank the board, so their curves are evidence about football.
Set-piece and DefCon barely move it, so their curves are evidence about **the harness**, and waiting for more
gameweeks would have produced the same flat line at GW6 and GW10 while looking like patience.

The narrower version, which is the one that will recur: **a whole-board metric cannot evaluate a term scoped
to a sub-population.** `SET_PIECE_WEIGHT` applies to nine players by design, and was being asked to prove
itself in a statistic computed over 626. It was never going to pass, and nothing in the pre-registered
criteria would have revealed that — because §B0 checked whether the bar was *strict enough* and never whether
it was *reachable*.

**Pre-registering a criterion protects you from choosing the answer afterwards. It does not protect you from
asking a question the instrument cannot answer.** Both checks are needed, and this sitting only had one.

---

### 🔗 References & Related Artifacts
- **The methodology executed:** [ADR-101](./ADR-101-calibration-methodology.md) · `docs/GW1_RUNBOOK.md` §B0
- **The weights:** ADR-028/124 (form) · [ADR-096](./ADR-096-gated-set-piece-xp-term.md) (set-piece, and the `hist`-tier
  exclusion that makes it unmeasurable) · ADR-097 (DefCon) · [ADR-188](./ADR-188-a-defender-plays-for-a-team.md)
- **The constants:** ADR-144 (captain margin) · ADR-145 (concentration) · ADR-146/150 (exodus)
- **The sampling discipline:** [ADR-183](./ADR-183-the-same-build-twice.md) — one sample of a varying
  process is not a measurement; two seeds, every time
- **The measurement:** `spikes/190-gw4-sitting/constants.py`
