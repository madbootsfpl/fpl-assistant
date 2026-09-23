# ADR-257 — Which of these two?

**Date:** 2026-09-23
**Status:** Accepted
**Completes:** the mobile audit's §6 — *search, compare, the card*
**Builds on:** ADR-236 (Boot Battle in the transfer flow), ADR-237 (the expanding row), ADR-238 (filters)

---

## Context

The owner: *"we never did the boot battle on the app either."* He was right about the part that mattered.

Boot Battle has existed on the phone since ADR-236, reachable only from the **transfer flow** — which
answers *"who should replace him?"* ⭐⭐ **That is a different question from *"which of these two?"***, and
the second one is what a browse list is for. §6 has owed *compare* since the audit.

## Decision

**The expanded player card gains "Compare with one of N", and the N is the filtered list.**

⭐⭐ **That the filters narrow it is the point.** `MID · under £8.0m · BHA` is how you find the two players
worth putting side by side — so the filter row earns its keep twice, and the picker is short because you
already said what you were looking for.

⚠️ **Same position only, and that is the engine's rule surfaced rather than a simplification.** `compare`
refuses a cross-position pairing because it *"ranks them on stats that do not mean the same thing"* —
⭐ *offering one in the picker would be offering an error, and the reader would read the refusal as a bug.*

⭐ **On the expanded card, not on every row.** A compare button on 481 closed rows is noise; on the card, a
reader has already said they are interested in this player.

⭐ **The picker says why the list is what it is** — *"Other MIDs in the list you are looking at."* Otherwise
*"where is everyone?"* is the first thought, and the answer — your filters, and his position — is invisible.

## What building it found

⚠️⚠️ **Two mutations walked straight through the first test file**: offering other positions, and offering
a player against himself. The test had **recomputed the same-position filter in Dart** and checked its own
answer.

⭐⭐⭐ *A test that re-describes the logic guards the description* — the ADR-241 lesson, arriving again in a
different costume. It now reads the count off the **button's own label**, which is the one place the widget
states its answer out loud, and both mutations die.

⚠️ **And the first test asserted an absence.** *"No compare button on a closed list"* passes on a build
where the button never exists at all — ⭐ *asserting an absence proves nothing about a presence.* Expanding
a row needed a real card response, so `player` joined the committed samples, where the contract test now
guards it too.

⚠️ A smaller one worth keeping: the mock router tested `endsWith('/player')` before `endsWith('/players')`
and would have answered the wrong call. ⭐ *A router that tests the shorter prefix first answers the wrong
question.*

## Verification

* **4 Dart tests**: no button on a closed list, a button on an expanded card, the picker explaining its own
  contents, and the offered count matching the board minus himself.
* **4/4 mutations killed**: the button never appearing; rivals crossing positions; a player offered against
  himself; and the picker dropping the line that explains its length.
