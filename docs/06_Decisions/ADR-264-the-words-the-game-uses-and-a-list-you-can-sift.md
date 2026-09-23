# ADR-264 — The words the game uses, and a list you can sift

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner's third round of phone feedback — items on wording, and on lists too long to use
**Follows:** ADR-258 (the filter chips), ADR-257 (Boot Battle from the list)

---

## 1. The words

Three renames, all the same principle ⭐ *the manager is thinking in the vocabulary of the game he is
playing, and an app that renames his moves makes him translate* — first applied when *"Replace him"*
became *"Transfer"*.

| Was | Now |
|---|---|
| `Bring him on…` | **`Substitute…`** — FPL's word. ⚠️ The bench direction keeps its own words, because *"Substitute"* does not say which way he is going. |
| `1 move` · `2 moves` | **`1 transfer` · `2 transfers`**, matching the sheet. ⚠️ `FittedBox`, because *a rename can overflow a layout that fitted the old word* — "3 transfers" is materially wider in a third of a phone. |
| `Field it` | **`Play Him`** … and **`Play Them`**. |

### ⚠️ The third one could not be done as asked

*"Play Him"* was requested by name, and the strip beside that button reads **"start Salah and Saka"** — the
plan can field more than one player. A flat rename would have read *"Play Him"* over a two-player change.

⭐ **A label is part of the sentence the screen is saying, not a word on its own.** So it counts: one
incoming player reads *"Play Him"*, more than one reads *"Play Them"*.

## 2. A list you can sift

Two screens offered long lists as flat, unsorted, unsearchable scrolls:

* **Boot Battle** — *"one of 214"*, every same-position player in the list.
* **The transfer flow** — every candidate, which for a midfielder is most of the market.

⚠️ *A list nobody can sift is a list nobody reads to the bottom of* — so both were really offering their
top, while appearing to offer everything.

Both now carry **search, a sort, a club filter and a way back**:

* **Search matches name *or* club** — ⭐ *"ars" is how someone looks for a player whose name they cannot
  spell*, and matching only the name would answer *"no such player"*.
* **Sort defaults to xP** (the reason to be there); price sorts **cheapest first**, because the question a
  price sort asks is *"what can I afford?"*
* **A back control.** ⚠️ A sheet dismisses by swiping down, which is discoverable only to people who
  already know it — ⭐ *a gesture is not an affordance*, and changing your mind is the commonest thing a
  reader does here. The transfer list replaces the actions **in place**, so without one the only way out
  was closing the sheet and finding the player again.
* **A count**, so an empty list reads as *"your filters"* rather than *"nobody is available"*.

### ⚠️ Shared logic, not a shared screen

`siftPlayers` and the controls are shared, because ⭐ *two hand-built pickers drift apart* (ADR-184). The
**chrome is not**: Boot Battle gets a modal; the transfer list stays inline and keeps its **over-budget
flag**, which the owner asked for specifically and which a generic row does not carry. ⚠️ *The
presentation was not the thing that was wrong.*

📌 And deliberately **not** the Players tab's filter row (ADR-258): that row is for **browsing** a market;
this is for **finding** someone in a list already narrowed by the question you asked.

## Verification

* **13 tests on `siftPlayers`**, the pure half — **6/6 mutations killed** (club search disabled, both sort
  directions reversed, the club filter ignored, trimming dropped, de-duplication removed).
* **3 new label tests**, including that the old wording is gone.
* ⚠️ An existing test tapped `'Field it'` by name and broke — now taps **by type**, since *a test that
  hard-codes one form of a count-dependent label breaks on the next sample regeneration*.
* 146 Dart tests.
