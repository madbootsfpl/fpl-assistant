# ADR-240 — A risk you have already handled is not a risk

**Date:** 2026-09-22
**Status:** Accepted
**From:** tester feedback on the phone build, item 2 — *"confidence is not bounded correctly"*
**Builds on:** ADR-089 (plan confidence), ADR-198 (levers), ADR-208 (what benching him actually fields)

---

## Context

The owner's own This Week card, read on his phone:

```
51/100  Low
− 8   M.Sangaré is flagged — already on your bench
− 8   João Pedro is flagged — bench or replace him — benching him fields Calvert-Lewin (2.3 xP)
− 8   Hume is flagged — bench or replace him — benching him fields Egan (2.6 xP)
Ceiling: your captain's own number (75/100)
```

⚠️⚠️ **The first line charges 8 for a risk he had already mitigated, and then tells him to mitigate it.**
The score could not be improved by the action it was asking for, because he had already taken it.

### ⭐⭐⭐ The first diagnosis was wrong, and measuring is what corrected it

I read the formula — `gameweek_confidence = captain − 8 × flags`, banded High ≥75 — and concluded the top
band was structurally unreachable: *"a manager whose captain scores 60 can never see High."*

Then I measured, because ADR-210 says to:

| the 40 most-captainable players | |
|---|---|
| captain score, median | **89** |
| reach the "High" threshold of 75 | **39 / 40** |
| same players **away to a tough side** | **39 / 40** |

⚠️ **The claim was true and vacuous.** Almost nobody's best captain scores 60; they cluster at 86–91. The
band is reachable in practice, and I had reasoned from an equation about a population I had not looked at —
⭐ *the exact failure ADR-210 exists to prevent, committed in the paragraph that cited ADR-210.*

⭐ **It is the same species as ADR-238's payload size and ADR-183's timing run**: a confident number derived
from the wrong thing. The instrument here was an algebraic worst case standing in for a distribution.

## Decision

**`gameweek_confidence` counts flagged players in the XI, not in the squad.**

⭐⭐ **The information was never missing.** `gameweek.py` has computed `"starting": p["id"] in optimal`
since ADR-208, under a comment that says it outright — *"a flagged player already on the bench costs the XI
nothing"* — while the scoring counted all fifteen regardless. ⚠️ *A fact computed and then not used reads,
from the outside, exactly like a fact nobody knew.*

The owner's week: **51 Low → 59 Medium.**

**The benched flag stays on the card**, worth `0` and `kind: "noted"` rather than `"action"`. It is a real
thing about his squad; it is simply not costing him. ⭐ *Hiding it would answer the complaint by removing
the information, which is not the same as fixing it.*

**Both renderers had to change too.** The phone printed `− 0` beside *"already on your bench"*, which is the
bug's own wording surviving the fix; it now reads `✓`. The CLI said *"minus 24 for 3 flagged players"*
against a score docked 16 — ⚠️ **a card arguing with itself, in the half written in words**, which is the
half a reader trusts.

## Consequences

⭐ Every squad carrying a benched flag gains up to 8 points of weekly confidence, and some cross a band.
That is the correction, not a side effect.

⚠️ **`starting` defaults to `True` when a flag cannot say.** An older payload is charged rather than
excused: undercounting silently inflates the score, and an inflated confidence reads as a healthy week
rather than as missing data.

📌 **Not changed: the bands themselves.** `confidence_band` is one function shared by eight different
scores with eight different ranges, which is a real smell — but the measurement above says it is not
currently misfiring for the gameweek, and ⭐ *a threshold should be moved because the distribution says so,
never because a formula looked suspicious.* Left open, with the numbers recorded here for whoever opens it.

## Verification

* **10 tests**, including the owner's exact card — a 75 captain with one benched and two starting flags,
  asserting **59 / Medium**.
* **5/5 mutations killed**: the whole squad charged again; nothing charged at all; a flag with no
  `starting` key silently excused; the benched line hidden rather than freed; and the prose reverting to
  counting every flag.
* ⚠️⚠️ **All 2,331 existing tests passed both before and after the fix.** Not one distinguished a benched
  flag from a starting one, so the suite was green across a change that moved the owner's headline number
  by eight points and a whole band. ⭐ *Passing tests measure what was asked, not what is true* — and this
  one was found by a person looking at his own screen.
