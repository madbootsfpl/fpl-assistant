# Sprint 256: Spend the transfers you hold (ADR-191 §1)

**Dates:** 2026-09-14
**Status:** ✅ Complete — **ADR-191 §1 built.** **1758 → 1763 tests, ruff clean.**
§2 (joint pairs) and §3 (target-driven planning) remain gated.

> **Owner:** *"I have £1.0m in the bank, I have 2 free transfers… is this advice the best or most effective?"*

---

## The build was one line, because the planner already existed

`suggest_transfer_plan` has threaded the bank and priced true marginal gains since **ADR-035**. The CLI,
`ask`'s transfer intent and the Transfer tab all use it. **The week's answer was the one caller that didn't** —
it asked `suggest_transfers(limit=2)` for a *menu*, showed the top entry, and spent the second on answering
*"bank or use"*.

So §1 was never "build a planner". It was **call the planner we already have**.

That sharpens the diagnosis: the gap was not missing capability, it was **the most-read surface wired to the
older primitive**. Nothing surfaces that. Every other caller was correct, so a grep for `suggest_transfer_plan`
looked healthy — four call sites, all right, and the one that mattered most not among them.

## What fell out of the wiring

`free` **and `bank` did not reach the week's answer at all.** Both were hard-coded in `ask.py` (one transfer,
£0.0m) while the Transfer tab collected the real numbers three tabs away. The recommendation was being computed
for a position its reader was not in — and said nothing about it.

Both widgets are now keyed (`tr_free`, `tr_bank`) and are the app's single record of that position, so the two
tabs cannot disagree.

## Before and after, on a real squad

```
free=1  bank=£0.0m
  Transfer: Senesi → Ballard  (+10.0 XI xP over 5 GW)
            Worth saving for: £1.0m more makes this Ampadu → Rayan (+12.6, +2.6 on the move above)

free=2  bank=£0.0m
  Transfer: Senesi → Ballard  (+10.0 XI xP over 5 GW)
            then #2: Diop → Affengruber  (+9.3 XI xP over 5 GW)
            Using all 2 free transfers: +19.3 XI xP over 5 GW — each move priced after the one above it
```

The *"Worth saving for"* line disappears at two transfers, because its uplift (+2.6) loses to the second
transfer (+9.3). That is the owner's exact complaint, resolved: **two correct answers to competing questions,
made to compete.** Compared over the cliff's own five-gameweek window, never the page's — comparing those two
numbers would have repeated ADR-186's original mistake precisely.

## ⚠️ Two guards passed while the code was broken

Six mutants, **two survived the first sweep**, and both were fixture faults:

| mutant | first sweep | after |
|---|---|---|
| back to a **menu** (`suggest_transfers`) | ❌ **passed** | ✅ |
| extra-move lines render at `free=1` | ❌ **passed** | ✅ |
| ignore the transfers held, advise one move | ✅ | ✅ |
| the cliff shows even when it loses | ✅ | ✅ |
| the cliff suppressed at one transfer held | ✅ | ✅ |
| the total drops how it was computed | ✅ | ✅ |

**The menu one is the instructive failure.** The headline guard asserts *"the stated gains must sum to the real
XI lift"* — correct, and it could not fail, because the fixture used equal upgrades in **different positions**,
where a menu and a plan genuinely agree. ⭐ *A fixture that only exercises the lucky case will confirm a broken
mechanism.* Rebuilt around the one thing a menu cannot model — **the bank threading**: two £6.0m buys against
£5.0m players with £1.0m banked, where a menu offers both and a plan can afford exactly one.

The second was laziness of naming: the `free=1` guard checked for `"then #2"` and missed that the *total* line
still rendered. It now asserts the whole block is absent rather than the part that was easiest to name.

---

## 💡 The lesson

> **A primitive can be correct everywhere and still be missing from the one place people read.**

There was no bug in `suggest_transfer_plan` and no missing feature. Four callers used it correctly. The week's
answer — the single most-read surface in the app — used its older sibling, and the code around that call
explained *why it asked for two moves*, which reads as care rather than as a gap.

Auditing "is this function used?" would have said yes. The question that would have found it is **"what does
the surface a user actually reads call?"** — which is a different question, and one nothing in the test suite
or the ADR trail was asking.

---

## Definition of Done

1. **Tests: 1758 → 1763**, six mutants, all confirmed red after two fixtures were rebuilt.
2. **Manual smoke** — the week's answer on two real squads across `free` 1–3 and `bank` £0–2m; the plan grows,
   the gains add, and the cliff appears and disappears on the comparison.
3. **Docs** — ADR-191 (status, §🛠, action items), ADR-000 index, Roadmap, PROJECT_STATUS, this retro.
