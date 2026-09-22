# ADR-244 — The gap and the missing button were one thing

**Date:** 2026-09-22
**Status:** Accepted
**From:** tester feedback — *"Optimise My Squad — can we do that based on This Week?"* and *"real estate is
not maximised… see gap at bottom"*
**Builds on:** ADR-225 (drafts), ADR-235 (the pitch), ADR-241 (`Draft.swap`)

---

## Context

Two separate notes on the same list, and they answer each other.

**The app could already tell you your lineup was wrong and gave you no way to fix it.** This Week said *"3
changes"* and named them; acting on it meant reading three lines, remembering them, and tapping four shirts
on a different screen. ⭐ *An app that can compute the answer and makes you transcribe it has stopped
halfway.*

**And the bottom of My Team was dead space** — roughly 14% of the screen between the bench and the tab bar.

⭐⭐⭐ **The action belongs in the gap.** The most useful thing on the screen, put where the screen had
nothing. The alternative fix for the gap — stretching the pitch to fill it — would have risked the layout
the owner had already said was good, to solve a problem that had a better answer.

## Decision

**`my-team` carries `suggested_lineup`**: `{start, bench, bring_in, drop, gain}`, or **null** when your XI
is already the best one.

⭐ Null rather than an empty plan, because *the absence of a suggestion is the answer* — and the strip says
so once, quietly (`✓ Your XI is already the best eleven you own this week`) rather than vanishing. ⚠️
*Silence and reassurance are different answers and both are sometimes right*: a strip that disappeared
would leave a reader wondering whether the app had checked.

⚠️⚠️ **Lineup only — never transfers.** Starting a player you already own is free and reversible; a
transfer costs points and cannot be undone. ⭐ *One button must not do both, whatever the xP says.* The
Transfers tab stays a deliberate second decision, not friction to be smoothed away.

**It is computed, not fetched.** Putting it on `my-team` rather than making the pitch call
`gameweek-plan` saves a round trip on the app's landing screen.

⭐⭐ **It reuses `best_legal_xi` on the same `lineup_xp` convention as `gameweek_plan`** — including
ADR-154's rule that a player reported to be leaving ranks as if he scores nothing *for selection only*.
⚠️ **Deriving a second, subtly different optimum is how two screens start recommending different teams**,
and there is a test that fails when they disagree.

**The gain is scored on the real xP**, never on the zeroed map. The zeroing is a selection device; quoting
a gain computed from it would credit the manager with points a fiction created. ⭐ *The number on the button
has to be one he can actually get.*

**Applying goes through the same `Draft`** as everything else, so it inherits the banner, the staleness
check and the way out. A second mechanism for *"the squad you are looking at is not your FPL squad"* is how
one of them ends up not saying so.

## What building it found

⚠️⚠️ **Three of five mutations survived, and two of them were no-ops.** The ADR-154 branch — a reported
leaver kept out of the XI — could not be exercised, because **there are zero reported leavers on the entire
board today**, measured rather than assumed. ⭐ *A mutation that survives because the population contains
no instance of the thing under test says nothing about the test, and reporting it as coverage would be a
lie.*

The fix was to call `_suggested_lineup` directly with a constructed leaver. ⭐ **Building an input is the
wrong move when live data can reach the branch and the right one when it cannot.**

⚠️ The first attempt built the whole squad by hand, and `best_legal_xi` returned an **empty XI** from it —
the optimiser needs fields a hand-written dict does not carry. *A fixture the code under test cannot consume
is not a simpler test, it is a different one.* It now uses real players with one constructed fact.

⚠️ **The third survivor was a genuinely weak assertion**: the bench-order test checked only that the bench
held exactly one keeper, which is true of *every* permutation. ⭐ *An assertion that every ordering
satisfies is not testing order.*

⚠️ And three Dart tests **skipped themselves** when the sample squad had no changes to suggest — which
would have quietly emptied the file the first week the fixture happened to be optimal. There is now a test
asserting the sample carries a suggestion at all.

## Verification

* **7 Python tests**, including one that fails when `my_team` and `gameweek_plan` field different elevens.
* **4 Dart tests**, including one that the button hands the plan back **unchanged** — the bench order is
  FPL's substitution order and must survive the handover verbatim.
* **5/5 mutations killed** after the two no-ops were made reachable: suggesting when there is nothing to
  do; scoring the gain on the selection fiction; an unordered bench; introducing a player you do not own;
  and ignoring ADR-154 entirely.
