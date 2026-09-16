# Architectural Decision Record: "Why 73?" — invert the confidence, don't offer a dial

**Decision ID:** ADR-198
**Date:** 2026-09-16
**Status:** ✅ **Accepted — built for the week's plan** (2026-09-16). **1810 → 1815 tests, ruff clean.**
⏳ **The other four confidence surfaces are gated** — see §🛠.
**Superseded By / Replaces:** Extends [ADR-089](./ADR-089-explainability.md)'s Confidence · Edge · Risk.
**No `decision_xp` change** and no new number — the same heuristic, run backwards.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

> **Owner:** *"When the tool provides a confidence level, how can one interact with the tool to say — how can
> I move the confidence to 80 or 90? Would be great to have some sort of interaction medium."*

The week's answer showed **Confidence: 73/100 (Medium)** and no way to ask what that was made of.

#### ⭐ The score is a heuristic over known inputs, so it inverts exactly

```
gameweek_confidence = captain − 8 × flagged players

73  =  81 (captain Isak)  −  8 (one flagged player: Hume)
```

*"How do I get to 81?"* therefore has an **arithmetic** answer, not an opinion: resolve one flag. That matters
beyond neatness — it is the only way this feature could exist at all on a deployment with **no model**
(ADR-168). The same sum, run backwards.

---

### 🎯 Decision

**An explainer, never a dial.** Under the Confidence line:

```
Confidence: 78/100 (High)
  Why 78? 86 for your captain, minus 8 for 1 flagged player.
    · Worth 8: Senesi is flagged — bench or replace him
    Ceiling this week is 86 — your captain's own number (86/100); lifting it means a
    different captain, not a different week.
```

**1. Actionable and fixed are separated, and that is the whole point.** A flagged player is a *choice* —
bench him, sell him. An away fixture is not: it costs the captain term a flat 6 (`fixture` = 0.6 away against
1.0 at home) and no decision of yours changes it. A single list would read as *six things you could do*, four
of them facts about the week.

⭐ **Telling someone what they cannot change is as useful as telling them what they can — it is the difference
between a low number and a bad week.** On the owner's plan the honest answer to *"how do I get to 90?"* is
**you cannot, this week**: Isak is away, which caps the captain term at 91, and clearness saturates at a 0.8
xP lead. What he *can* do is worth exactly 8.

**2. No control to drag.** Someone who learns that benching a flagged player adds 8 will bench a player who is
fine, because the number went up. ⭐ *A visible score plus a way to move it is an invitation to game it* — the
heuristic would get optimised instead of the week. A test asserts the block renders text only.

**3. "Clearer", never "more likely".** Confidence is a heuristic, not a probability, and the `MODEL_NOTE`
already says so. Raising it does not make you more likely to be right; it means the week is **less
ambiguous**. A *"get to 90"* framing invites exactly that conflation, so a guard bans the vocabulary of
likelihood from this copy.

**4. It sits directly under the line it explains**, between Confidence and Edge — it first rendered after
Risk, three blocks below, where it read as a footnote to something else.

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:** confidence stops being a verdict and becomes a **diagnostic**; the honest extension of
  *Logic explains*; and it needs no model, so it is identical on Cloud and on a dev box.
* **Negative Impact / Trade-offs:** four more lines on the densest block in the app. Scoped to the week's plan
  for exactly that reason — if it earns its space there, it can travel.
* **Risks & Mitigations:**
  - **Risk:** Goodhart — the number gets optimised instead of the squad. **Mitigation:** no control, and the
    levers name *the player*, not *the points*, so acting on one is still a football decision.
  - **Risk:** it makes visible that confidence means different things on different surfaces — the chips page
    already needs a footnote saying the wildcard's is measured differently. **Mitigation:** that is a **good**
    exposure and the reason the roll-out is gated: an explainer on five surfaces would have to reconcile five
    definitions, which is a bigger job than one panel and should be taken deliberately.

---

### 🛠 Implementation & Migration
* **Components Affected:** `analytics/explain.py` (`confidence_levers`, `FLAG_COST`), `ui/gameweek.py`
  (`_levers_lines`), `tests/test_explain.py`
* **Action Items:**
  - [x] Invert `gameweek_confidence`; separate actionable levers from the fixed ceiling
  - [x] Render between Confidence and Edge; text only, no widget
  - [x] Guards: the sum inverts exactly · only actions are listed · no likelihood vocabulary · no widget ·
        placed under the line it explains
  - [x] Mutation-test every guard — four mutants, all red, including *a fixed fact dressed as an action*
  - [ ] **GATE:** the captain, transfer, chips and verdict surfaces. Each needs its own decomposition, and
        together they force the question below.
  - [ ] **GATE:** reconcile what *confidence* means across surfaces — the chips footnote is the existing
        evidence that it does not mean one thing today.

#### ✅ Always
- [ ] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

---

### 💡 The lesson

> **A transparent heuristic can answer "what would change this?" — a model cannot, and that is an argument
> for the heuristic.**

This project has repeatedly chosen documented arithmetic over a learned score: `decision_xp` is one recipe,
confidence is a stated blend, the weights are gated at zero until measured. Each time, the case was
*checkability*. This is a second dividend nobody costed: **because every input is named and the formula is
four terms, the tool can tell you exactly what is holding a number down, which parts are yours to move, and
what it would take.** A neural net with the same accuracy could not produce that paragraph.

⭐ The generalisable form: **an explanation you can invert is worth more than a score you can only read** —
and inversion is a property of the model, decided long before anyone asks for the feature.

---

### 🔗 References & Related Artifacts
- **The confidence blend:** [ADR-089](./ADR-089-explainability.md) · `MODEL_NOTE` (heuristic, not probability)
- **Why it needs no model:** [ADR-168](./ADR-168-retire-ask-and-the-promise-with-it.md)
- **The inconsistency it would expose:** the chips footer — *"the Wildcard's confidence is how far a rebuild
  beats your squad, not how clearly one week wins"* (ADR-185)
- **Asked for by:** the owner, reading his own week's plan
