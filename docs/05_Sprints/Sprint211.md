# Sprint 211: A dead slot takes the free transfer (ADR-156)

**Dates:** 2026-08-27
**Status:** ✅ Complete — ADR-156. 1476 → 1485 tests, ruff clean.

> **Owner:** *"Transfer doesn't pick up Watkins, he is not recommended to transfer."*

---

### 🔧 What shipped

Two faults on one page.

**The ranking asked the wrong question.** `suggest_transfers` ranked on Watkins's stored 4.3 xP — points he
will never score — so it compared a replacement against them instead of against nothing. Now it takes
`reported_out` and zeroes leavers in a **local copy** of the xP map (ADR-154's idiom, reused). He is also
barred from the incoming shortlist: buying a departing player is the same mistake with your own money.

**The page contradicted itself.** The ⛔ banner and the ADR-132 timing line were computed independently, so
one said "Watkins can't score" while the other said "use your free transfer on Gibbs-White". `transfer_timing`
now takes the same `dead` list the banner is built from.

```
BEFORE  Use your free transfer on Gibbs-White → Cunha (+1.4 next gameweek).
AFTER   Use your free transfer on Watkins → Welbeck — Watkins can't play (per Romano),
        so that slot recovers 3.4 xP next gameweek. A dead slot comes before any upgrade.
```

The two gains are still never compared — ADR-136's rule, since they measure different things. The dead slot
wins on **kind**, and a test pins that by giving it the *smaller* number and asserting it still goes first.

---

### 💡 The lesson

> **One owner stops surfaces disagreeing. It does not stop them not asking.**

ADR-155 deleted four hand-written copies of "who is leaving?" and I wrote that this closed the class of bug.
It didn't, and couldn't: a pure analytics function can't fetch anything, so a caller still has to pass the
fact in — and `reported_out=None` means "no departures", which is the safe default *and* the silent one. A
surface that never learned to ask looks exactly like one with nothing to report.

Six surfaces, six times found by the owner using the product. That is the actual detector here, and it is
worth being straight about rather than claiming the last fix generalised.

And a second one, about pages rather than functions: **two correct answers on one screen can still be a wrong
page.** The banner and the timing line were each right alone. Read together they were two plans.

### 🧪 Tests

**+9.** The leaver valued at zero and shown as zero; never a suggested signing; the caller's xP map unmutated;
the fact threaded through every step of a plan; a dead slot taking the free transfer ahead of a bigger-looking
upgrade; never banked against (a textbook bank-it case that stops being one); the upgrade demoted to the hit
question, plus the wording when there is no upgrade at all; the two gains never compared; and a headless
Transfer render asserting the view actually asks.
