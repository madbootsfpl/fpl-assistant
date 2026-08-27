# Architectural Decision Record: The transfer ranking values a leaver at zero — and a dead slot takes the free transfer

**Decision ID:** ADR-156
**Date:** 2026-08-27
**Status:** ✅ **Accepted — owner-reported, built** (Sprint 211, 2026-08-27). **1476 → 1485 tests, ruff clean.**
**Superseded By / Replaces:** Sixth and last surface of the ADR-151→155 arc. **No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Still testing, the owner found the sixth:

> Transfer doesn't pick up Watkins, he is not recommended to transfer.
> *"Use your free transfer on Gibbs-White → Cunha (+1.4 next gameweek)."*

Two separate faults, on one page:

**1. The ranking asked the wrong question.** `suggest_transfers` ranks on `xp_by_id`, where Watkins is worth
4.3 — points he will not score. So it was asking *"how much better is his replacement than the 4.3 he'll
score?"* instead of *"…than nothing?"*. ADR-154 fixed exactly this for the **lineup** and stopped there.

**2. The page contradicted itself.** The ⛔ dead-slot banner and the ADR-132 timing line are computed
independently. Even once the banner knew about Watkins, the line beneath it still said *"use your free
transfer on Gibbs-White"*. Both numbers were right; neither knew the other existed.

The web view also called `replace_dead` **without** `reported_out` — so the banner never fired there at all,
which is why the owner saw no mention of him anywhere on the page.

---

### ✅ Decision

**1. `suggest_transfers` / `suggest_transfer_plan` take `reported_out`.** `_selection_xp` builds a **local
copy** of the xP map with leavers zeroed — the same idiom ADR-154 used for `best_legal_xi`, reused rather than
reinvented. `decision_xp` is untouched; the map lives for the length of one ranking. A test asserts the
caller's dict is not mutated.

**2. A departing player is never a suggested signing.** He was already excluded from *your* XI; buying him
would have been the same mistake with your own money.

**3. A dead slot takes the free transfer — on kind, not on number.** `transfer_timing(…, dead=…)`: when any
slot cannot score, the answer is **use**, the headline names that swap, and the best ordinary upgrade drops to
being the hit question behind it.

The two gains are still **never compared**, which is ADR-136's rule: `replace_dead`'s gain means *points
recovered from zero*, an upgrade's means *XI improvement*. A test pins this by giving the dead slot the
**smaller** number (1.1 vs 9.9) and asserting it still goes first.

**4. Banking against a dead slot is never right.** Banking buys a second free transfer next week; a hole in
the squad costs the same every week it stays, and costs everything the week a starter is knocked. The test
takes a textbook bank-it case and shows it stops being one the moment part of the squad cannot play.

**Verified on the live squad:**

```
BEFORE  Use your free transfer on Gibbs-White → Cunha (+1.4 next gameweek).
AFTER   Use your free transfer on Watkins → Welbeck — Watkins can't play (per Romano),
        so that slot recovers 3.4 xP next gameweek. A dead slot comes before any upgrade.
        Don't take a hit: the next-best move gains 1.2, less than the 4 points it costs.
```

### 🧪 Definition of Done

1. **Tests: +9.** The leaver valued at zero and shown as zero; he is never a signing; the caller's xP map is
   not mutated; the fact threads through every step of a plan; a dead slot takes the free transfer ahead of a
   bigger-looking upgrade; it is never banked against; the upgrade becomes the hit question (and the wording
   when there is no upgrade at all); the two gains are never compared; and a headless Transfer render that
   asserts the view **asks** — the stub must be called.
2. **Manual smoke** — the live squad, CLI and the numbers above.
3. **Docs** — this ADR, PROJECT_STATUS, the sprint retro.

---

### 💡 The lesson

**ADR-155 gave the fact one owner; it did not give it one *reader*.** Deleting the four hand-written lookups
was right and did not prevent this, because a pure analytics function cannot fetch anything — someone has to
pass it in, and a caller that never learned to pass it is indistinguishable from one that had nothing to pass.
`reported_out=None` defaults to "no departures", which is the safe default *and* the silent one.

So the honest version of ADR-155's lesson is narrower than I wrote it: **one owner stops surfaces
*disagreeing*; it does not stop them *not asking*.** What actually finds a surface that isn't asking is a
person using the product — six times out of six here, including this one.

The second lesson is about pages, not functions. **Two correct answers on one screen can still be a wrong
page.** The banner and the timing line were each right in isolation; the reader met them together and got two
plans. Anything that renders side by side has to be computed from the same inputs, or it will eventually be
computed from different ones.
