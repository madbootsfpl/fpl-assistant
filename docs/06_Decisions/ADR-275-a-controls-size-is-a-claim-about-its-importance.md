# ADR-275 — A control's size is a claim about its importance

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner — *"can the Strong XI & Strong 15 be a toggle, doesn't need to be a large tab… also
use 11 & 15 or XI & XV your choice"*, with a screenshot
**Adjusts:** ADR-272 (the Lab)

---

## Context

The Lab shipped the build style as a **second full row of pills**, identical in weight to the mode row
above it. On the phone the two rows wrapped into each other.

⭐ **A control's size is a claim about its importance** — and two matching rows said *choosing a bench
weighting* mattered as much as *choosing a wildcard*. It does not: the build style **modifies** the mode.

## Decisions

**A `MiniToggle`** — a small two-option switch, labelled with what the choice is *about*. ⚠️ *A toggle
with no subject is two words a reader has to infer a question from*, so it reads **Bench: [Strong 11 |
Strong 15]**.

**One numbering.** *"Strong XI"* beside *"Strong 15"* mixed Roman and Arabic **inside a single control**,
which is what made the owner offer the choice. ⚠️ *Two ways of writing a number in one control reads as
two kinds of thing.* Arabic, because it is how FPL managers talk — *"all 15 score on a Bench Boost."*

**The keep instruction is orange.** In grey it sat directly under a card of grey explanatory text and
read as one more caption — ⚠️ *an instruction that looks like a footnote gets skipped*, and this one names
the only interaction on the screen that is not a button.

📌 The toggle keeps `Pill`'s rule: **both states coloured explicitly** (ADR-269), since the transparent
half is the one a framework default would ruin.

## Verification

* **6 Dart tests**; **4/4 mutations killed** — both halves filled, taps swallowed, mixed numbering
  restored, and the subject label dropped.
* ⭐ The numbering test checks the **labels do not mix** systems rather than asserting one particular
  spelling — *a test that pins the wording would fail on any rename, including a correct one.*
* 2,570 Python · 244 Dart.
