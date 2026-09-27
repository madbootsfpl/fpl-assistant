# ADR-314 — Two sentences nobody could read

**Date:** 2026-09-27
**Status:** ✅ **Built.**
**From:** the owner's list — *"Confidence: 'Ceiling: your Captain's own number… not a different week' is a
bit cryptic — could you explain what it means at a more basic level so people will understand? The TIMING
statement is also a little unclear too."*

---

## The decision

**Both sentences were accurate and unreadable.** Neither was rewritten to say something different; each was
rewritten to say the same thing to someone who does not already know it.

⭐⭐⭐ *Copy written by the person who knows the answer is the copy most likely to assume it.* Both of these
were written by me, beside the arithmetic that produced them, where every term was obvious.

## 1 — The ceiling

**Was:**

> Ceiling this week is 64 — your captain's own number (64/100); lifting it means a different captain, not a
> different week.

⚠️⚠️ **Every clause is true and the sentence still cannot be used.** *"Your captain's own number"* asserts
that the ceiling and the captain's score are the same without saying **why**; *"lifting it means a different
captain"* then draws a conclusion from that unstated fact. ⭐ *A sentence that only makes sense to someone
who already knows the thing it explains is not an explanation.*

**Now:**

> The most it can reach is 64 — the same as your captain's confidence (64/100), because the week turns on
> that one pick. Clearing the flags above closes the gap; only a different captain raises the 64.

⭐⭐ **Three moves, in the order the reader asks them.** *What is the bar* → *how do I get to it* → *what
moves the bar.* The owner's original question behind this whole feature (ADR-198) was *"how can I move the
confidence to 80 or 90?"*, and the honest answer has two halves that the old sentence had collapsed into
one: **the flags close the gap, and nothing except the captain moves the number they are closing on.**

⚠️ The word is still **clearer**, never *more likely* — confidence is a heuristic, not a probability, and
that rule survives the rewrite intact.

## 2 — The timing statement

**Was:**

> It saves 1.9 (the hit avoided on a second move worth 2.4) and costs 2.8 by waiting a week.

⚠️ **Three numbers, no units, and a parenthetical carrying the only clause that explains where the first one
came from.** A reader has to hold *saves*, *avoided*, *worth* and *costs* in mind at once to see that two of
them are the same quantity seen from different ends.

**Now:**

> Next week you would have two free transfers, so a second move costs no −4 hit — worth 3.0 pts. Against
> that, making the move above a week later costs 0.4. Waiting comes out +2.6.

⭐ The mechanism first (*why would banking be worth anything?*), then the price, then the net.

⚠️⚠️ **And the reason no longer says what to do.** Every caller already states the verdict — the app prints
`BANK` / `USE` as the headline, the CLI prefixes *"Or bank it:"* — so a reason opening *"bank the
transfer"* said it twice. ⭐ *The headline is the decision; the reason is the arithmetic that makes it
checkable.*

## Where the words actually live

⭐ Three surfaces, one edit each time: the engine sentence (`explain.py`, `transfer_timing.py`), the line
that renders it (`ui/gameweek.py`), and the **glossary** — which the app mirrors through
`scripts/generate_glossary_dart.py`, so the phone's definition cannot drift from the web's. ⚠️ *The glossary
entry is the one a confused reader taps*, and it carried the same assumption as the sentence it explains.

## Guards

⚠️ **Pinned by property, not by wording** — ⭐ *a test that asserts a sentence verbatim turns every future
improvement into a failing test.* What is pinned:

- **No timing reason repeats the verdict** (all five shapes).
- **Every number in a timing reason says what it counts** — `pts`, or free transfers.
- **The ceiling clause carries a `because`**, names the captain, and states the number.
- **Closing the gap and raising the bar stay separate sentences.**
- **A week already at its ceiling gets no advice** — ⚠️ *a suggestion offered when nothing is wrong teaches
  people to stop reading the suggestions.*

Both rewrites mutation-tested by restoring the old copy: red, then green.

⚠️ One existing test asserted `"saves 3.0"`. Its claim was that the arithmetic is *shown*; the phrasing was
incidental, and it asserts `3.0 pts` and the word `hit` now — ⭐ *the number, and what the number is of.*

**2867 Python · 460 Dart.**
