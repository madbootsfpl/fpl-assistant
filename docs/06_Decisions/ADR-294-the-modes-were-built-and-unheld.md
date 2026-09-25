# ADR-294 — The modes were built; nothing held them

**Date:** 2026-09-25
**Status:** Accepted
**From:** the owner — *"lets do the Lab's Free Hit and fresh-season modes next"*
**Corrects:** the roadmap, which listed them as unbuilt

---

## They already worked

The roadmap said *"the Lab's other two modes — Free Hit and a fresh-season build are the same solver with
different defaults, and `LabMode` already exists to hold them (ADR-272)."*

⭐ **ADR-272 shipped them.** That line was written while the enum existed and the screen did not use it,
and the commit that fixed it is the commit it cites. Run on the device, all three work:

| mode | budget | scored over |
|---|---|---|
| Wildcard | £100.8m — your team value | 5 gameweeks |
| Free Hit | £100.8m | **1 gameweek** — *"67.0 xP this GW"* |
| New season | **£100.0m**, keep-list hidden | 5 gameweeks |

⚠️ *A roadmap entry outlives the work it describes unless something closes it*, and nothing did.

## ⭐⭐ But nothing was holding them

The enum was tested — `LabMode.freeHit.horizon` is 1, only `freshSeason` is `fromScratch`, every mode has
a label. **The screen's use of it was not.** Two mutations proved it:

```
SURVIVED   horizon: _mode.horizon  →  horizon: 5
SURVIVED   _mode.fromScratch ? 100.0 : team.value  →  team.value
```

Both hardcode the Wildcard. **Free Hit and New season would have silently become Wildcard, and all 341
tests would have passed** — because they asserted what the constants *say* and never what the screen
*sends*.

⚠️⚠️ *A constant nobody reads is a constant that is correct and irrelevant.*

So six tests now pump the screen, tap the mode, press build, and read the body that went on the wire:
the horizon, the budget, and that a new season carries an empty keep-list — ⭐ *a hidden control whose
value still ships is a setting the reader cannot see and cannot change.*

5/5 mutations killed, including both that had survived.

## ⚠️ Two things the fixture taught

**The committed sample has no team value**, so the Lab shows *"your team value has not loaded"* and there
are no pills to tap. ⭐ *A fixture that cannot reach the button cannot test what the button sends* — the
sample documents the shape, and the test supplies the case.

**And `value` lives under `squad`, not at the top level.** Setting it at the top failed **silently**,
leaving a test that failed with *"found 0 widgets with text Free Hit"* — ⚠️ *a fixture that patches the
wrong key produces a failure unrelated to the thing being tested*, and the temptation then is to blame
the widget.

## What this changes

- **Nothing in the product.** The modes worked before this ADR and work after it.
- **The roadmap loses a line it should have lost in ADR-272.**
- ⭐ *"It works" and "it is held" are different claims, and only one of them survives the next refactor.*
