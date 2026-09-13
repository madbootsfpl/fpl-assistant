# Architectural Decision Record: Price the rebuild, not just the fixtures

**Decision ID:** ADR-185
**Date:** 2026-09-13
**Status:** ✅ **Accepted — built & owner-verified** (Sprint 247, 2026-09-13; confirmed in the app
the same day — *"chips tab does say wildcard"*). **1742 → 1746 tests, ruff clean.**
**Superseded By / Replaces:** Extends [ADR-082](./ADR-082-chip-strategy-advisor.md)'s chip advisor. **No
`decision_xp` change.** One of three gaps opened by the owner's A/B experiment; see also ADR-186 and ADR-187.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner is running **two teams** — one following MADBOOTS, one on his own judgement — and is **40 points
ahead** after four gameweeks. That is the most direct evidence of product quality the project has ever had,
and it is negative.

Auditing the MADBOOTS squad (`RoboTS`) surfaced this:

```
overlap with a fresh £100m build : 3/15
RoboTS over the next 5 GWs       : 275.3 xP
a fresh build                    : 377.6 xP
                                   ─────────
wildcard value                   : +102.3 xP
```

**A wildcard is worth about 102 xP** — and free transfers recover only **31 of it (30%)**, taking six weeks
to do so, by which point the fixture window has moved.

Here is what the app actually advises:

> *Wildcard: GW5–GW7 — your weakest stretch (avg XI 48.8 xP); reset before it · **Confidence 42/100 · Low***

#### The gap

`chips.py` chooses the wildcard week as the **lowest rolling window of best-XI xP**:

```python
win_avgs = [sum(per_gw[gw]["xi_total"] for k in window) / window for s in starts]
best_start = min(starts, key=lambda s: win_avgs[s])
```

That is *"when are your fixtures worst"* and nothing else. **It never asks what a wildcard would gain.** It
cannot see two dead forwards, a 3/15 overlap with the optimum, or 102 xP on the table.

So it points at roughly the right window for entirely the wrong reason, and reports **42/100 — Low**, which
reads as *"we're not sure"* when the case is overwhelming. **The advisor is least confident exactly when it
should be most.**

#### Decision Drivers

- **Driver 1 — the two halves already exist.** The optimiser can build the replacement squad; the advisor
  knows the fixture run. Nothing joins them.
- **Driver 2 — a wildcard is a *squad* decision, not a *fixture* decision.** Fixtures say *when*; the state
  of your squad says *whether*. The advisor only answers the first and presents it as the whole answer.
- **Driver 3 — the confidence number is actively misleading here.** A low confidence on a 102-xP call is
  worse than no number.

---

### 💡 Options Considered

#### Option 1: Price the rebuild, and let it drive both *whether* and *when* *(Chosen)*
* **Description:** run the optimiser at the current budget, compare with the squad, and report the gap. Use
  it to answer *whether* to wildcard; keep the rolling-window minimum for *when*.
* **Pros:**
  - ✅ Answers the question the chip actually poses. *"A rebuild is worth 102 xP over five gameweeks; your
    weakest stretch is GW5-7, so play it before GW5."*
  - ✅ **Costs one solve (~0.08s measured, ADR-183).** The optimiser is already on the page.
  - ✅ Makes the confidence honest — it can key on the *size of the gap*, which is the thing that decides it.
  - ✅ Falls out naturally: a healthy squad shows a small gap and the advice correctly becomes *"don't"*.
* **Cons:**
  - ❌ The rebuild is unconstrained by transfers, so the number is an upper bound. It is the right upper
    bound — a wildcard **is** unconstrained — but it must be labelled as the wildcard's value, not a squad
    deficiency score.

#### Option 2: Flag dead slots only ("you have 2 players who can't play → consider a wildcard")
* **Pros:** ✅ Cheap; no solve.
* **Cons:** ❌ Dead slots are the *symptom*, not the measure. A squad with no dead slots can still be 60 xP
  behind through eleven mediocre picks — which is most of this case.

#### Option 3: Leave it; the fixture window is roughly right anyway
* **Cons:** ❌ It was right by coincidence here. ❌ And it cannot say *whether*, which is the question a
  manager sitting on a broken squad is actually asking.

---

### 🎯 Decision & Justification

**Compute the rebuild and lead with it.**

> *"A wildcard is worth **+102 xP** over the next 5 GWs — your squad overlaps a fresh £100m build by only
> **3 of 15**, and **£14.1m of it cannot play**. Your weakest stretch is GW5-7, so play it before GW5.
> Free transfers alone recover about 30% of that, over six weeks."*

Four numbers, each already computable: the gap, the overlap, the idle money, the transfer alternative.

**Confidence keys on the gap, not on the fixture margin.** Today it measures *how clearly one window beats
another* — which is genuinely low here, because the weeks are close. But the *decision* is not close at all.
Two different questions were sharing one number.

⚠️ **State the upper bound honestly.** The rebuild assumes a wildcard's freedom. Called *"what a wildcard is
worth"* it is exactly right; called *"how bad your squad is"* it would overstate, because most squads cannot
reach it by any other route. **The label is the honesty.**

---

### 🔬 Built — what it says now

On the owner's squad, the same call that read *"Confidence 42/100 · Low"*:

```
Wildcard: worth +99.6 xP — a fresh build beats your squad over this window;
          you keep only 3 of 15; £14.1m of your squad cannot play.
          Your weakest stretch GW5–GW7 (avg XI 48.8 xP) — reset before it
          · Confidence 95/100 · High
```

**42 → 95.** The fixture window survives and is demoted: it answers a real question, just not the first one.
A closing line says the wildcard's confidence measures a different thing from the other three chips'.

**`rebuild=None` leaves every existing caller byte-identical** — a squad that cannot be priced (a fixture
without `price`, a partial snapshot) takes that path rather than failing the whole chip answer. The
enhancement degrades; the answer does not.

#### ⚠️ Two guards tested components and not the wiring

Both survived their first mutation, and both for the same reason:

| mutation | why it passed |
|---|---|
| confidence falls back to the fixture margin | the test called `rebuild_confidence` **directly**, so the branch in `explain_chips` that *selects* it was never executed |
| `idle_spend` is never computed | the renderer test passed `idle_spend` as a **literal** in a hand-built dict, so `rebuild_value` never computed it |

> ⭐ **Testing a component is not testing that anything uses it.**

The same shape as ADR-181's *"a test that rebuilds the thing under test is testing the test"*, one level out:
there the substitute was a re-implementation, here it is a hand-supplied input. Both leave the production
path unexecuted while reading like coverage.

Repaired by driving `explain_chips` end-to-end (with near-flat weeks, so the fixture margin *would* read Low
if it were still in charge) and by computing `idle_spend` from data with two deliberately dead forwards.
**Six mutations, all caught**, including a no-op control to prove the harness itself was live.

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:** the biggest call available to a manager stops being invisible; the advisor answers
  *whether* as well as *when*; a healthy squad gets a confident *"don't"*, which is equally useful.
* **Negative Impact / Trade-offs:** one solve per chip render; one more number on a card that already
  carries four chips.
* **Risks & Mitigations:**
  - **Risk:** a big number every week trains people to ignore it. **Mitigation:** it is only big when it is
    true — a well-kept squad measures a handful of xP, and the advice then says so.
  - **Risk:** it reads as *"rebuild constantly"*. **Mitigation:** pair it with the transfer alternative, as
    in the copy above — *30% over six weeks* is the honest comparison and often the right answer.

---

### 🛠 Implementation & Migration
* **Components Affected:** Code (`analytics/chips.py`, the chip surfaces), Tests, Docs
* **Action Items:**
  - [x] `chips.py` computes the rebuild gap at the current budget
  - [x] The wildcard entry reports gap · overlap · idle money · the transfer alternative
  - [x] Confidence keys on the **gap**, not the fixture margin
  - [x] Guard: a squad with two dead slots produces a **high**-confidence wildcard call
  - [x] Guard: a freshly-optimal squad produces a small gap and advises against
  - [x] Guard: the number is labelled as the wildcard's value, never as a squad score
  - [x] **Mutation-test every guard**; clean suite re-run between mutants
  - [x] Built directly on the owner's *"build ADR-185"* — the ADR carried the measurements a preview would have shown

#### ✅ Always
- [x] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

---

### 💡 The lesson

> **A recommendation that measures only *when* will present itself as an answer to *whether*.**

The advisor was never wrong about fixtures. It was answering a smaller question than the one on the card, and
nothing in its output said so — the reader supplies the missing half without noticing.

---

### 🔗 References & Related Artifacts
- **Extends:** [ADR-082](./ADR-082-chip-strategy-advisor.md) · uses [ADR-183](./ADR-183-the-same-build-twice.md)'s
  now-deterministic optimiser (a nondeterministic one would have made the gap flicker)
- **Sibling gaps:** ADR-186 (banking) · ADR-187 (multi-GW planning)
- **Found by:** the owner's two-team A/B — 40 points behind after four gameweeks
