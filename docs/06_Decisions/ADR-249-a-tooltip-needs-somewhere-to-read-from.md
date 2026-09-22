# ADR-249 — A tooltip needs somewhere to read from

**Date:** 2026-09-22
**Status:** Accepted
**From:** tester feedback — *"MADBOOTS — the BOOTS txt should be orange"*, *"Should we have an optimise
button on my squad OR review it in This week & then optimise?"*, *"We don't have any tool tip or info
pop-ups like we do in the web app"*
**Builds on:** ADR-103/114 (the brand is one source), ADR-244 (Field it)

---

## 1. BOOTS is orange, and it always was

`brand.py`'s `wordmark_html` says so in as many words: *"MAD purple · BOOTS orange, the colour split doing
the word-break."* The app rendered it **white**.

⭐⭐⭐ **Nobody decided that.** The palette is generated into `brand.dart`; the *wordmark* — which colour
goes on which half — was **retyped in Dart**, so it drifted from the one source of truth ADR-103/114 exists
to keep. ⚠️ **A generated palette does not stop a hand-written rule from disagreeing with it**, and the
owner spotted it on a phone screen before any test did.

There is a test now comparing both halves against `brand.py`.

## 2. Both, not either

The owner asked whether "optimise" belongs on My Team **or** in This Week. ⭐ **Both, because they are
different moments.** On the pitch it is a shortcut for someone who already trusts it. In This Week it sits
directly under the per-swap justification — *"higher projected xP: 4.8 vs 3.3"* — for someone who wants to
check first.

⚠️ *Making a reader remember a recommendation and walk to another screen to apply it is the transcription
problem ADR-244 removed, reintroduced one screen along.*

## 3. Tooltips, and the thing that had to exist first

⭐⭐ **A hover tooltip has no phone equivalent, and pretending otherwise is the trap.** The web's `?`
reveals on hover; a touch screen cannot hover, and a long-press is a gesture nobody discovers. So it is a
**tap that opens a sheet** — bigger than a tooltip, which is the right trade: there is room to say what a
number *is not*, and that is usually the honest half.

### ⚠️⚠️ The blocker was that there was nothing to read from

The web carries `help="…"` inline at roughly forty call sites. There was **no dictionary** to point a
second client at, so a phone tooltip meant retyping every explanation in Dart — ⭐ *which is precisely the
drift that put BOOTS in white.*

So `src/glossary.py` is the single source, generated into `mobile/lib/glossary.dart` by the same contract
as `brand.dart`: committed output compared against a fresh generation, hand-edits fail the next run.

⭐ **Definitions, not instructions**, and each says what a number **is not**:

> **Confidence** — how *clear* this week's plan is… It is a documented heuristic, **not a probability**.
> Raising it does not make you more likely to be right — it means the week is less ambiguous.

⚠️⚠️ **A test forbids the glossary from promising accuracy.** The words *probability*, *likelihood* and
*accurate* may appear only when **denied**. ⭐ *A tooltip is exactly where someone goes looking for
permission to believe a number*, and a glossary that granted it would undo the care taken everywhere else.

📌 The web's inline strings should migrate onto this module. Recorded so the next reader knows which way
the debt runs.

## What building it found

⚠️ **The first regeneration test `exec`-ed the generator's source with `__main__` swapped out** — clever,
fragile, and it failed for a reason that had nothing to do with the subject. It imports the module and
calls `render()` now. ⭐ *A test whose machinery is harder than its subject fails on its machinery.*

## Verification

* **19 tests** on the glossary crossing: the committed Dart matching a fresh generation, every key and
  label surviving, entries that would not compile, a missing term returning null rather than raising, and
  the accuracy ban.
* **4/4 mutations killed**: a term added to Python without regenerating; the Dart hand-edited; confidence
  sold as a probability; and a definition shrunk to a bare phrase.
* **3/3 mutations killed** on the wordmark: BOOTS in white, purple, or teal.

## Still open from this round

📌 **Player DNA** (the owner: *"there's real estate on the More tab"*) and **full Team DNA parity** — the
radar, the grade ring, club-vs-club compare, next-6 fixtures with form, and the key-players table. A
substantial piece, and the glossary above is what its eight axis labels will read from.
