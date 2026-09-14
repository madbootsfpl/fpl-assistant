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

## ⚠️ Reported broken the same hour, and fixed

The owner rebooted and got a **one-move** answer with the cliff still showing, while holding two transfers.
The wiring could never have worked, and the tests could never have caught it:

**The control was behind the selector it was meant to inform.** `tr_free`/`tr_bank` were widgets on the
**Transfer** panel, read from session state by **This week**. Those panels are a `segmented_control`, not tabs
— **only the chosen one executes**, and Streamlit discards state for widgets a run does not render. They are
mutually exclusive by construction (ADR-175/176), so the week's answer read the defaults every single time.

⭐ **Session state between two branches of a selector is not shared state, it is no state.** Both panels were
individually correct; the bug lived entirely in the fact that they never coexist, which is not a place a unit
test looks. Fixed by hoisting both inputs **above** the selector — they describe *the manager*, not a panel —
and passing them down as arguments, so there is no session-state round-trip left to break.

**And the assumption was stated only when it was not a guess.** The extra-move lines returned nothing at
`free=1`. But `free` **defaults to 1**, so the plan announced its assumption precisely when the manager had
already corrected it, and went quiet the one time the number was invented. ⭐ *An assumption is worth stating
in inverse proportion to how sure of it you are.*

Re-sweeping the mutants afterwards caught a third: `free = len(moves)` survived, because **every fixture had
as many worthwhile moves as transfers held**. They differ constantly on a real squad, and reporting one as the
other redefines *"all your transfers"* as *"the ones we found"*. Now: *"Using 2 of your 3 free transfers … so
the rest keeps"* — an unspent transfer is information. ⭐ *Two variables that are equal in every fixture are
one variable as far as the suite is concerned.*

### …and reported again after that

The control appeared and the **assumption line** appeared — but the answer still read *"Assumes 1 free
transfer"*. Three things came out of chasing it, none of which is yet confirmed as the owner's cause:

1. **One of the two routes to the week's answer dropped both arguments.** `render_this_week` renders eagerly
   with no model attached and behind a button with one; both end at `render_ai_tips`, and only the eager path
   was passing `free`/`bank`. ⭐ *A parameter added to a function with two call sites is added to one of them
   by default.* Guarded now by an AST check that **every** call inside `render_this_week` carries both —
   deliberately a claim about all of them, not about one (ADR-178's union-vs-all trap).
2. **The line named only the transfer count**, so a reader could not tell *which* number had failed to
   arrive. It now names both: *"Assumes 1 free transfer and £0.0m in the bank"*. ⭐ *A stated assumption should
   let a reader debug it, not just confirm that one was made.*
3. **`int(_free or 1)` turned a real 0 into 1.** The control's minimum is 0 and holding no free transfer is a
   real position — the move still exists, it costs a 4-point hit. The count is now reported as given and
   planned as at-least-one, and the line says so.

⚠️ **The owner's symptom is not reproduced.** The analytics path is verified correct at `free` 1–3 and `bank`
£0–2.5m, and the chain from widget to answer has one call site each with no cache and no fragment between
them. The diagnostic line is what will settle it: the next report says which number arrived.

### …and still reported, so the page now states what it read

The next report came back **`Assumes 1 free transfer and £0.0m in the bank`** with the Bank slider visibly on
£1.00m — the two ends of the chain disagreeing, which is more information than either end alone.

Source was verified correct at every hop (one call site each, no cache, no fragment between widget and
answer), and `AppTest` proves the widget propagates: `set_value(2)` flips the page's own statement of what it
read. So rather than keep deducing, the page now **says what it read, where it read it**:

```
Every answer below uses **2 free transfers** and **£1.5m** in the bank.
```

⚠️ **This is not debug output, and it is not temporary.** It earns its place twice over: these controls sit
*above* a selector and feed **every** panel below it, which a reader otherwise has to take on trust — and two
statements of the same fact at opposite ends of the chain turn *"it doesn't work"* into *"it breaks between
here and there"*. ⭐ **A value that travels through four layers should be stated at both ends, not just at the
end that consumes it.**

A test now drives the real widget and asserts that statement changes — the one step no amount of reading the
source could confirm, and the step **both** bugs lived in.

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
