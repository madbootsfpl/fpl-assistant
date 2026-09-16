# Architectural Decision Record: A threshold needs a provenance

**Decision ID:** ADR-199
**Date:** 2026-09-16
**Status:** ✅ **Accepted — two thresholds set from measurement, two gated** (2026-09-16).
**1815 → 1818 tests, ruff clean.**
**Superseded By / Replaces:** Calibrates constants introduced by [ADR-089](./ADR-089-explainability.md) and
ADR-185. Applies [ADR-144](./ADR-144-captain-margin.md)'s p75 rule. **No `decision_xp` change** — confidence
is a display heuristic.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner, on the *"Why 73?"* explainer shipped hours earlier:

> *"Is this more of a discussion rather than an empirical result? I nearly see this as a chatbot-like Maddie
> assist — let's have a discussion on how can we raise confidence. But they're more like hunches or punts —
> tell me if I'm wrong."*

**He was right about the layer and wrong about the level, and the audit is the answer.**

The *formulas* are empirical: `73 = 81 − 8` is checkable arithmetic, and three confidence functions turned out
to be literally the same expression. **The constants those formulas invert over were mostly typed.**

| constant | provenance |
|---|---|
| `WHISKER 0.3` · `CLEAR 1.3` (captain margin) | ✅ 300 squads (ADR-144), re-measured at GW4 (ADR-190) |
| `LINEUP_TOO_CLOSE 1.0` · `LINEUP_CLEAR 2.8` | ✅ 500 squads, two seeds (ADR-194) |
| `_CLEAR_LEAD 0.8` | ❌ chosen |
| `_CLEAR_GAIN 3.0` | ❌ chosen |
| `_CLEAR_CHIP_MARGIN 0.15` | ❌ chosen |
| `_CLEAR_REBUILD 0.25` | ❌ chosen — *"Provisional — re-measure"*, in its own comment |
| `FLAG_COST 8` | ❌ chosen |

⚠️ **Two of seven, and both exist because the owner pushed back on them.**

---

### 📊 The measurement (`spikes/199-confidence-thresholds/`)

200 random legal squads per seed, two seeds (ADR-183):

| quantity | p25 | median | **p75** | chosen |
|---|---|---|---|---|
| captain lead, next GW | 0.30 | 0.65–0.80 | **1.30–1.42** | 0.8 |
| transfer gain, 1 GW | 3.08 | 3.50 | **3.80–3.90** | 3.0 |
| chip margin, relative | 0.00 | 0.01–0.02 | **0.04** | 0.15 |
| wildcard gain ÷ own projection | 1.10 | 1.30–1.34 | **1.78–1.80** | 0.25 |

---

### 🎯 Decision

#### ✅ Set: `_CLEAR_LEAD` 0.8 → **1.3** — and it needed no new measurement

`_CLEAR_LEAD` and `captain.CLEAR` are **the same quantity on the same distribution**: how clear a captain's
lead over the runner-up is. One was measured twice. The other was typed — and the typed one is the copy
*inside the confidence score*.

The consequence was concrete: **42–47% of captain calls sat at or above 0.8**, so clearness saturated at the
*median* lead.

| lead | before | after |
|---|---|---|
| 0.65 (median) | 83 | **71** |
| 0.80 | **91** | 75 |
| 1.30 (measured p75) | **91** | 91 |

A middling lead and a genuinely clear one scored identically. ⭐ **Two constants describing one quantity is
one constant and a bug waiting for someone to notice** — the fix is `_CLEAR_LEAD = CAPTAIN_CLEAR`, an
identity rather than a copied value, so they cannot diverge again.

#### ✅ Set: `_CLEAR_CHIP_MARGIN` 0.15 → **0.04** (the measured p75)

Roughly 4× too high, so *"clear"* was unreachable: a typical margin scored **55** where the house rule puts it
at **95**. The page already explained that chips *"honestly read Low/Medium and sharpen in-season"* — true,
and incomplete. ⭐ **Some of the Low was the threshold, not the football.**

The random-squad population is valid here in a way it is not below: a chip margin is a property of the
**fixture list**, not of how good the squad is.

#### ⏳ Gated: `_CLEAR_GAIN` and `_CLEAR_REBUILD` — **wrong population**

The numbers are in the table and they are **not** being used. Spike 191 already found why: random squads have
far more headroom than real ones. The owner's actual squad's best move was **+1.8** against a random squad's
**+3.5**; his real wildcard read **0.40** of his own projection against a random squad's **1.30**.

⚠️ **Setting either from this distribution would repeat the clean-sheet-rate mistake exactly** (ADR-188/195):
a confident number produced by an instrument pointed at the wrong thing. They need a realistic-squad
population — optimiser-built or imported — which is its own measurement.

#### ⏳ Gated: `FLAG_COST` — **not a margin**

The p75 rule does not apply. *What a flagged player actually costs a gameweek* is a backtest against real
outcomes, not a distribution of margins, and belongs with §B0's machinery.

---

### 🛡️ The guard that would have caught all of this

Changing both constants **broke no test whatsoever.** The two numbers most responsible for what a reader sees
had nothing pinning them — which is precisely how one drifted from its measured twin unnoticed.

So a threshold must now either be **measured** or be **declared unmeasured with the reason**, in a
`UNMEASURED` map the test reads. It may not simply exist. A new constant with no provenance fails.

⭐ **A calibration constant with no provenance is an opinion wearing a number** — and a number is believed in
a way an opinion is not, which is the entire problem.

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:** two user-visible numbers stop being invented; the captain's confidence starts
  distinguishing clear picks from middling ones; chips can now reach *High* when a week genuinely stands out;
  and every future threshold has to declare itself.
* **Negative Impact / Trade-offs:** **captain confidence will drop on many picks** — a 0.65 lead goes 83 → 71.
  That is the correction, not a regression, but it will look like one. Chip confidence will rise, which will
  look like enthusiasm and is arithmetic.
* **Risks & Mitigations:**
  - **Risk:** the p75 rule is itself a convention. **Mitigation:** true, and it is *stated* and used
    consistently three times now (ADR-144, ADR-194, here) rather than chosen per-constant.
  - **Risk:** measuring on random squads is wrong for the two gated ones — and might be wrong for these two
    as well. **Mitigation:** argued explicitly above for each, rather than assumed: a chip margin is a
    fixture-list property, and the captain lead reuses the population ADR-144 already accepted for that exact
    quantity.

---

### 🛠 Implementation & Migration
* **Components Affected:** `analytics/explain.py` (two constants + the import), `tests/test_explain.py`
* **Action Items:**
  - [x] Audit every confidence constant's provenance
  - [x] Measure all four at two seeds; record the distributions
  - [x] Set the two whose population is valid; **gate the two whose is not, with the reason**
  - [x] `UNMEASURED` + a guard that no threshold exists without a provenance
  - [x] Mutation-test — three mutants, all red, including a new constant with no provenance
  - [ ] **GATE:** re-measure `_CLEAR_GAIN` / `_CLEAR_REBUILD` on realistic squads
  - [ ] **GATE:** `FLAG_COST` as a backtest against outcomes

#### ✅ Always
- [ ] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

---

### 💡 The lesson

> **The owner asked whether the explanation was empirical. The right answer was to go and check, and the
> check found that the thing being explained was not.**

*"Why 73?"* inverts its formula exactly. It was faithfully explaining a number partly made of guesses — which
is not an argument against the explainer, but arguably its best property: **it is the first thing that made
those guesses visible.** An invented constant is invisible until something has to justify itself with it.

And the narrower one, on the chatbot he was imagining: a conversational layer over these constants would have
produced fluent, confident discussion about four numbers, **three of which were wrong** — one by 4×, one
saturating at the median, two measured against the wrong population entirely. It would have sounded exactly as
persuasive before this audit as after. ⭐ *Fluency is not evidence, and the more transparent the underlying
model, the more tempting it is to trust talk about it.*

---

### 🔗 References & Related Artifacts
- **The p75 rule:** [ADR-144](./ADR-144-captain-margin.md) · [ADR-194](./ADR-194-a-start-bench-call-gets-a-margin.md)
- **The explainer that exposed it:** [ADR-198](./ADR-198-why-73.md)
- **The population trap, found twice before:** `spikes/191-two-transfers/` · [ADR-195](./ADR-195-team-defence-is-xgc-not-clean-sheets.md)
- **The measurement:** `spikes/199-confidence-thresholds/`
- **Prompted by:** the owner asking whether any of it was empirical
