# Sprint 242: One recipe means every caller (ADR-181)

**Dates:** 2026-09-07
**Status:** ✅ Complete — ADR-181. **1731 → 1733 tests, ruff clean.**

> **Owner:** *"Bug: different recommendations from My Squad 'what should I do this week' and captaincy."*

Two surfaces, on the same page, for the same squad, in the same gameweek, naming different captains.

---

### 🔴 The bug

```
Captain tab      B.Fernandes 4.8 · Virgil 4.5 · João Pedro 4.3
This week        João Pedro  6.3 · B.Fernandes 5.4 · Mbeumo 5.1
```

Not a rounding difference — a different captain, and the same player priced 4.8 against 5.4.

**One argument, one call site:**

```python
minutes_weight = minutes_weight_from_history(history)      # ← no gw_history
```

ADR-173 made the minutes weight prefer the minutes a player has **actually played this season**. It reads
that from the per-gameweek history, passed as a second argument. `ask` passes it twice, the CLI passes it,
`decision_xp` passes it. **The Captain tab never did** — and its caller never handed it the data to pass.

So one surface had been running the pre-ADR-173 model since 2026-09-02, through a change that moved 186
players, and nothing said so.

---

### 💡 The lesson

> **"One recipe" is a claim about every call site, not about the function.**

ADR-041 says the whole app decides on one xP recipe. `decision_xp` has been correct throughout — the bug
lived in an argument list. A shared primitive with an **optional** refinement hands every caller a silent
opt-out, and the caller that takes it does not look broken: it looks like an older, plausible answer, which
is far harder to spot than a crash.

The mechanical form, now a guard: **when a correction lands in a shared helper behind an optional argument,
the argument stops being optional.** Any single-argument `minutes_weight_from_history(...)` anywhere in
`src/` fails the suite, by filename.

⚠️ **This is the same shape as ADR-151→156** — the reported-departure signal needed teaching to six surfaces
one at a time, every one found by the owner using the product. A new fact reaching some call sites and not
others is this project's recurring failure, not a one-off.

---

### 🔬 The guard was testing itself

The cross-surface test, as first written, **recomputed** the Captain tab's picks with the right arguments and
compared them to the week's answer. Mutation-testing killed it: with the bug restored, it **passed**.

> **A test that rebuilds the thing under test is testing the test.**

It never called `render_captain`, so the code that was wrong was not in the path. Rewritten to drive the page
through `AppTest` and read the **rendered captain card**, it now fails on both layers — the view dropping the
argument, and the page failing to pass it.

**Fifth guard in six sprints to pass while protecting nothing**, and a new member of the family. The others
were a word blacklist, a source scan, a silent skip and a `or True` hedge. This one is subtler than all of
them: **a faithful re-implementation of the correct behaviour, standing in for the code that was wrong.**

The generalisable check: *if I deleted the module under test, would this still pass?* For the first version,
yes.

---

### 🧪 Tests

**+2**, both mutation-checked at both layers: the view dropping `gw_history`, and the page not passing it.
The sweep also verified every other call site — `ask` ×2, the CLI, `decision_xp` — all correct.
