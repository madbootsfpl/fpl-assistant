# Sprint 246: The A/B audit — three product gaps

**Dates:** 2026-09-13
**Status:** 📋 **ADR-185/186/187 proposed** (gates, not builds). Two defects fixed en route.
**1740 → 1741 tests, ruff clean.**

> **Owner:** *"I am running 2 teams, one based entirely on your input and suggestions versus a team from my
> own knowledge. I am already 40 points ahead after 3.5 GWs, and I can't see you making up the ground using
> current tactics and strategy."*

**This is the most direct evidence of product quality the project has, and it is negative.** All three gaps
he named check out against the code.

---

### 🔴 The audit was nearly wrong

Per-GW player history stopped at **GW2** while fixtures said **GW5 next**. João Pedro had **13 points the
model could not see** (bootstrap 33, stored 20). Every minutes judgement — the input ADR-173 added — was two
gameweeks stale.

Backfilled to GW4 and re-ran everything. **One earlier finding did not survive**: I had reported the transfer
ranking leading with a marginal upgrade over repairing a certain zero. On correct data it leads with the dead
slot. **The symptom was the stale data, not the ranking**, and I said so.

### ⚠️ And the backfill did not run the first time

`python -m src.cli history --backfill` printed nothing, returned **0**, and changed nothing. `src/cli.py` had
no `if __name__ == "__main__"` block, so the module imported, every definition ran, and the process exited
cleanly without reaching `main()`.

> **A CLI that exits 0 and does nothing is the worst failure mode there is. It looks like success.**

I nearly concluded *"backfill complete, data unchanged, therefore the model is fine."* The exit code lied; the
data did not. Fixed, and guarded through a real subprocess — the only way to exercise a `__main__` block,
since importing the module is precisely the path that was broken.

---

### 📋 The three gaps

**ADR-185 — price the rebuild.** `RoboTS` overlaps a fresh £100m build by **3 of 15**; a wildcard is worth
**+102.3 xP**; **£14.1m of it cannot play**. The advisor says *"Wildcard GW5-7, your weakest stretch ·
Confidence 42/100 · Low"* — because `chips.py` picks the week by the **lowest rolling window of best-XI xP**
and nothing else. It never asks what a wildcard would *gain*, so it is least confident precisely when the
case is overwhelming.

> ⭐ **A recommendation that measures only *when* will present itself as an answer to *whether*.**

**ADR-186 — bank to afford.** At £0.0m bank the best move is Watkins → Havertz **+7.4**. With **£1.5m** more
it is Watkins → Isak **+13.8**. The cliff is steep and invisible: `bank_or_use` only ever weighs banking a
*transfer* to make a second move.

> ⭐ **"Bank" meant a spare transfer everywhere in the code, and money to the user.** A term that means one
> thing in the code and two things to the user hides the half you did not build.

Ships the arithmetic, refuses the forecast — modelling the accumulation would stack the unverified price
predictor on top of a heuristic. Same line ADR-161 drew when it gated the win-probability sim.

**ADR-187 — reopen multi-GW planning.** ADR-132 declined it on 24 August, having prototyped properly and
found *"one beneficial move — a tree with one branch."* Re-run today: **five**, and the ranking **reorders
with the horizon**.

Its evidence was measured **preseason**, on an xP model since corrected twice — ADR-172 (a shrink inert for
513 of 626 players) and ADR-173 (**186 players moved**). A search finds one branch when most players are
mispriced.

> ⭐⭐ **A decline needs a re-measure date, the same as a feature needs a review date.**

ADR-132 did everything right except leave a tripwire. **Record what would have to change for the answer to
change** — *"re-measure if `decision_xp` changes materially"* — and ADR-172 would have tripped it on day one.

---

### 🧭 What the owner has that the app does not

Worth stating plainly rather than promising to fix: **his newsfeed and past-season knowledge is a real,
durable edge.** Signals reads headlines but deliberately does not feed the recommendation — the moment it
does, the app is guessing.

The right ambition is not to replicate his judgement but to make it cheap to apply: *"I think Foden starts —
show me the plan that assumes it."* That is a different feature from any of the three above, and it is
probably the most valuable one on this page.

---

### 🔓 The backfill unblocked the calibration

With four gameweeks stored, `calibrate` runs. **`FORM_WEIGHT` has been waiting for this since early
September** — GW6 is still the real sitting (ADR-101's pre-registered criteria), but the harness is no longer
refusing.

Its test failed on the way there, and instructively: it asserted *"Not enough gameweeks"* against the **live
database**. It passed for a month and then broke — not because anything regressed, but because the milestone
it was waiting for arrived.

> **A test that asserts today's data reports a regression when the season moves on.**

Rewritten to stub the gameweek count and test the **refusal rule**, with a sibling asserting it evaluates
once the data is there.

---

### ⚠️ I broke an architecture guard while improving it

`test_core_never_imports_a_web_edge` is a substring scan, and it tripped on a **comment** in `cli.py` that
merely mentioned `src/web_streamlit`.

My first repair stripped comments by tokenising and re-joining with newlines — which split
`src.web_streamlit` into three separate lines, so the substring could never match again. **A real illegal
import passed.** It was caught only because I mutation-tested the repair.

> ⭐ **A guard you have just improved is exactly the guard you have to re-break.**

Now AST-based, checking real `Import`/`ImportFrom` nodes. Verified against all three import forms, and
confirmed to ignore comments.
