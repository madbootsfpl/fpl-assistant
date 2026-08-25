# Sprint 191: Two build modes, not three — and they were named backwards (ADR-137)

**Dates:** 2026-08-25
**Status:** ✅ Complete — ADR-137. 1329 → 1331 tests, ruff clean.

> **Owner:** reported both oddities on 2026-08-19 and framed the standard exactly right — *"a
> correctness-of-labelling issue, not a polish one."*

---

### 🔍 Why this sprint exists

Squad Lab offered three build modes. Two of them were the same squad, and the two that were genuinely
different were named backwards. Measured on live data before a word was changed (£100m, 5-GW horizon, xP):

| radio option | `bench_weight` | 15-man xP | **XI xP** | bench spend | worst bench player |
|---|---|---:|---:|---:|---|
| Balanced | `None` | 303.7 | 231.7 | £23.5m | Thiaw, 17.2 xP |
| Bench Boost | `None` | 303.7 | 231.7 | £23.5m | Thiaw, 17.2 xP |
| Strong XI (weaker bench) | `0.1` | 289.2 | **238.9** | £19.0m | Walle Egeli, **4.9 xP** |

### 🔬 The measurement that changed the answer

The report said Bench Boost was wired wrong — it passed `bench_weight=None` instead of something distinct. So
the obvious fix was to pass `1.0` and let it be its own build. **Running that returned the same fifteen
again**, and the algebra says why:

```
maximise  Σ score·start + 1·score·(pick − start)   ≡   maximise  Σ score·pick
```

The `start` terms cancel exactly. **Bench Boost could never have been a distinct build, however it was
wired** — it was not a bug to fix but a promise the optimiser has no way to keep. That is the difference
between "merge these two options" and "this third option was always fiction", and it is only visible if you
try the fix before shipping the rename.

**And the surviving two were backwards.** "Balanced" is the max-15 build: £23.5m of bench where the *worst*
player is worth 17.2 xP. That is the **strong-bench** build. A user reading the radio got the opposite of the
truth in both directions.

---

### 🔧 What shipped

**All-round (strong bench)** and **Strong XI (cheap bench)**. *"Cheap"* rather than *"weaker"* because weak was
the misleading word — that bench is not worse by accident, it is deliberately cheaper so the money can go into
the XI. Naming the mechanism instead of the outcome is what makes the trade visible.

Bench Boost is now **answered where the question is asked** — a caption under the radio, saying that under the
chip all 15 score, so "maximise the XI" and "maximise all 15" become the same question and the all-round build
already is the answer. The Roadmap left merge-or-keep-with-a-note open; the measurement above decided it.

**The default was checked, not assumed, and does not change.** The XI-first build is **+7.2 XI xP** over five
gameweeks, which reads like a free win until you look at what it buys: a bench containing a 4.9-xP player —
a near-dead slot of exactly the kind ADR-136 taught the app to warn about the day before. That is a real
trade, so it stays the manager's call, now honestly enough labelled that they can make it.

The CLI's `--bench-boost` stays (removing a flag breaks scripts, and the note is useful) with help text that
no longer claims to change the build.

---

### 🐛 The bug the smoke found

`squad --full --bench-boost` printed:

```
Bench Boost: all 15 score this week — your total is the whole squad's xP.
Note: Starters (11) is your XI — the bench won't score.
```

Both cannot be true, and nothing tells a reader which to believe.

**This is the same species as ADR-136's bug, one day apart** — there, a *"hold your transfer"* line printed
underneath a dead-slot warning. Both times: a new line added correctly, while an older line that assumed it
didn't exist kept printing beside it.

> **When you add a line that changes what an existing line means, the existing line is part of the change.
> Adding is never only adding.**

Twice in two sprints is a pattern, not a coincidence, and it is now written where both ADRs can point at it.

---

### 💡 A second lesson: where the regression test lives

The obvious test is *"the radio offers two options"*. That test is worthless as a guard, because anyone adding
a third option edits it in the same commit and it passes.

So the load-bearing test sits at the **optimiser** level: a full-weight bench and no bench weight produce the
same objective value. It asserts the **value**, not the id list — where several squads tie, which one the
solver returns is arbitrary, and pinning an arbitrary choice makes a test fail for a reason it isn't about
(this happened: the synthetic pool in `test_optimizer.py` gives every legal 15 the same total, so the first
version of the test failed on a tie rather than on anything meaningful).

**A test guarding a decision should sit at the level the decision is true at** — here, algebra, not UI copy.

### 🧪 Tests

**+2 (1329 → 1331).** `test_a_full_weight_bench_cannot_build_a_different_squad_than_no_bench_weight` (the
algebra), `test_the_bench_boost_note_does_not_argue_with_the_bench_wont_score_note` (the contradiction), plus
an updated web test pinning the two options *and* that the chip question is still answered in the caption.
