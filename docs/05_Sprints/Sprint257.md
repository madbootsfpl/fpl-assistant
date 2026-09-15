# Sprint 257: Score the term on the population it applies to (ADR-188 × ADR-190)

**Dates:** 2026-09-15
**Status:** ✅ Complete — a measurement, no behaviour change. **1770 tests, ruff clean.**
**`CLEAN_SHEET_WEIGHT` stays 0**, now for a stronger reason. Two ADR-191 tweaks shipped alongside.

> **Owner, on a recommended second transfer:** *"Not sure I'd make the Konsa call!!"* — and separately,
> *"I can't select £1.2m."*

---

## The hypothesis, and why it was worth testing

The owner has now distrusted a recommendation to sell his **cheap Arsenal defender twice**. That is what
prompted ADR-188 in the first place, and ADR-188's GW4 sweep said the clean-sheet term does not help.

But [ADR-190](../06_Decisions/ADR-190-the-gw4-sitting.md) then found that **a whole-board rank metric cannot
evaluate a term scoped to a sub-population**, and closed `SET_PIECE_WEIGHT` on exactly that. ADR-188's term
applies to **DEF/GK only** and was scored across all **626** players with actuals — three quarters of whom it
can never touch. So the decline might have been dilution, and the owner's instinct might have been right.

## It was not dilution

| | whole board (n=626) | **DEF/GK only (n=277)** |
|---|---|---|
| ρ at weight 0 | 0.619 | **0.546** |
| ρ at weight 0.50 | 0.605 | **0.520** |
| decline | −0.014 | **−0.026** |
| MAE | 1.22 → 1.24 | **1.33 → 1.38** |

Restricted to the players it was built for, the term looks **worse** — nearly twice the decline on half the
sample. That is ADR-188's own double-count reasoning confirmed from a second direction: a defender's
points-per-90 already contains the clean sheets he kept, so re-adding his club's rate does the most damage
precisely where it is applied.

⚠️ **One number moves the other way, and it is recorded rather than used.** `hit@10` among DEF/GK rises
**0.15 → 0.23** at weights 0.15–0.30 — the *top* of the defender board improving while the overall ordering
worsens. It is genuinely tempting: a transfer recommendation cares about the top of the board, not the rank
correlation of 277 defenders most of whom nobody owns.

It is **three players** — 6.0 → 9.2 correct picks out of 40 across four gameweeks — on a **secondary**
criterion, while the **primary** one declines on the same rows. ⭐ **Treating it as the answer would be
choosing the metric after seeing the curve**, which is the one thing §B0's pre-registration exists to stop. If
it survives GW6 on more data, the honest question is not *"does clean sheet work after all?"* but *"does a
top-of-board metric belong in §B0 at all?"* — argued on its own merits, in advance.

## So what was the Konsa call?

Not the missing term. **Adding it would have ranked defenders worse.**

The actual cause was already visible in the output: the second move was priced at **+1.4 XI xP over one
gameweek** and carried **no longer view at all**, on a page whose window is a single gameweek (ADR-179).
Against a per-player weekly sd of **3.51** (ADR-161) that margin is inside its own noise. Fixed under ADR-191
— every move now carries its five-gameweek figure.

## Also shipped

**The bank slider was on `step=0.5`**, so a real £1.2m bank could not be entered. FPL prices in tenths; a
control that cannot express the real value silently rounds the manager's position, and every answer below it
is computed from that number. ⭐ *A control's step is a claim about what values exist.*

⚠️ **Its first guard passed while the bug was in place** — `set_value(1.2)` and read it back works fine at
`step=0.5`, because `AppTest` writes into session state and never enforces the widget's granularity. The test
asserted something the harness cannot constrain. The constraint **is** the step, so that is what it asserts
now. Caught by mutation.

---

## 💡 The lesson

> **A refuted hypothesis is worth the measurement it cost, because a whole-board decline and a
> sub-population decline are different facts — and only one of them was on the record.**

Before today, ADR-188's evidence was *"the term does not help the board"*. Someone re-reading it in three
months — reasonably, having read ADR-190 — would have asked whether the board was the wrong place to look. The
answer is now written down, so that question is closed instead of open, and it cost one script.

And the narrower one, about my own instinct: **I went looking for a reason the owner was right, and the data
said he was right for a different reason.** He was right that the recommendation was poor; wrong about why,
and so was I. The fix was in the window the second move was priced over, not in the model's blind spot — and
if I had only looked where his explanation pointed, I would have shipped a weight that makes defender ranking
worse and still not fixed the call he objected to.

---

## Definition of Done

1. **Tests: 1770**, unchanged by the measurement; ADR-191's two tweaks carry three mutants, all red.
2. **Manual smoke** — the sweep run over 9 weights on both populations; deterministic (`decision_xp` is
   arithmetic, no solver, no sampling).
3. **Docs** — ADR-188 §🔬, ADR-190's Option 3 item ticked, ADR-000 index (188 + 190), this retro,
   `spikes/192-defender-only-calibration/`.
