# Sprint 266: A doubt is a probability, not a verdict

**Dates:** 2026-09-17
**Status:** ✅ **ADR-206 §1 built — 1842 → 1849 tests, ruff clean, 5 mutants all red. §2/§3 proposed.**

---

## The report

> *"It's picking up that there is an issue with João Pedro, which is great. However we are coming into an
> international break, he is hot, so I would not sell him."*

The app wanted **João Pedro → Havertz, +4.7 XI xP, Confidence 95/100**, because *"higher projected points
(4.9 vs 0.0)"*.

João Pedro: **8.2 ppg — joint-highest forward in the game with Haaland** — four consecutive 90s, 11/9/1/12,
**74.5% owned**. Havertz: 4.2. The app had him at **0.0**.

**Not a judgement call the owner disagreed with. A mechanism fault.**

---

## What was wrong

`xp._status_is_active` was `p["status"] == "a"`. Every doubtful player scored **zero**, and a **75% doubt
priced identically to a 25% one** — 23 players that day.

`minutes.chance_factor` computed exactly the right number, 0.75, and deliberately kept `d` out of its
unavailable set. It never ran, because the binary gate returned False first.

⭐⭐ **Two mechanisms modelled the same thing and the cruder one ran first**, making the finer one dead code
for precisely the population it was written for.

### ADR-006's reasoning had expired, not been wrong

> *"`chance_of_playing` is barely populated, so `status` is the signal."*

True when written — preseason, the column was empty. FPL populates it now (25/50/75). Nothing re-checked.
⭐ *A constraint recorded in an ADR is a fact about a version, not a law* — ADR-180, and the second time that
lesson has cost something.

### ⚠️ And it had already been found, at one call site

```python
# captain.py
is_available=lambda p: not is_unavailable(p),   # count doubtful, not only 'a'
```

A local override, with a comment naming the exact bug — written for captaincy, left broken for transfers, the
lineup, the week's plan and every board.

⭐⭐ **A workaround at one call site is a bug report nobody filed.**

### Three definitions of "unavailable", disagreeing

`xp`: only `a` · `minutes`: `{i,s,u}` · `optimizer`: `{i,s,u,n}`. ⭐ *A fix in one of three definitions is a
fix in one third of the app.* Now one, in `minutes`, re-exported by `optimizer` so all **sixteen** call sites
are untouched.

⚠️ `"n"` added, closing a hole the fix would otherwise have **opened**: an unregistered player's `chance` is
None, which `chance_factor` reads as *"assume available"* → 1.0.

---

## What changed

| | before | after |
|---|---|---|
| doubtful projecting > 0 | **0 of 23** | **21 of 23** |
| João Pedro next GW | 0.0 | **4.3** |
| João Pedro 5 GWs | `{0, 0, 0, 0, 0}` | 21.1 |
| **the recommendation** | **+4.7** | **+0.6 — inside the noise floor** |

⭐ **Discounted, not deleted.** No doubtful player enters the board's top 10; João Pedro still sits below
Havertz. The risk is priced. It is no longer annihilation.

---

## ⚠️ The whole suite stayed green

**1842 tests, none red**, while 23 players moved off zero and the headline recommendation reversed. Nothing
had ever asserted what a *doubtful* player is worth — only that an unavailable one is worth nothing.

⭐ **"All tests pass" after a behavioural change is a statement about the tests.** Second time in two days,
after ADR-195's dormant term.

---

## 💡 The lesson, and its mirror

ADR-192 found *no opinion* implemented as **the most optimistic opinion available** — no history → multiplier
**1.0**, the maximum.

This is the same failure pointing the other way: *a doubt* implemented as **the most pessimistic verdict
available** — 75% likely to play, priced **0**, the minimum.

⭐⭐ **When a model expresses uncertainty as a number, check which extreme that number is.** It will be one of
them, in whichever direction nobody happened to be looking — because the neutral-seeming value of a multiplier
is never neutral.

---

## 📋 Not built, on purpose

**§2** — a flag is a fact about *now*, priced across the whole horizon: 0.75 still applies to GW9 in November.
**§3** — fixture gaps: GW5 kicks off tomorrow, **GW6 is 19 days later**.

⭐ **§3 falls out of §2 for free if the decay is measured in *days until kickoff* rather than *gameweeks
ahead*** — then an international break needs no concept of its own. Both gated on the owner, and on a decay
shape that must be **measured, not invented**.

---

## Definition of Done

- ✅ **Tests** — 7 new (`tests/test_doubtful_is_priced.py`); 1849 passed, ruff clean; 5 mutants, all red
- ✅ **Manual smoke** — whole board off the live cache: 21/23 doubtful now carry value, none in the top 10,
  `i`/`s`/`u` all still zero
- ✅ **Docs** — ADR-206 + index row, PROJECT_STATUS, this sprint doc

**Next:** the owner's call on §2/§3.

---

# Part 2: §2 and §3, same day — and the curve was never needed

**1849 → 1857 tests. 12 mutants, 11 red + 1 recorded equivalent.**

## The approach changed, and that is the useful part

The plan was a **measured decay curve**. It could not be measured: that needs a history of flags against what
players went on to do, and ADR-203 only began recording it **on the day this was written**. Waiting meant a
month of projections known to be wrong.

⭐⭐ **The question was not "how fast does a doubt decay" but "what is a doubt evidence about".** The second
needs no curve at all. FPL publishes `chance_of_playing` about the **upcoming** match — a *now* field with no
"as of". Applying it five weeks out **states something the source never said.**

So the discount holds inside the window the flag is evidence for, and beyond it the player reverts to his
ordinary minutes weight. **A declared scope, not an invented decay.**

## §3 then costs nothing

⭐ **Because the reach is measured in days rather than gameweeks, an international break needs no concept of
its own.** GW6 kicks off **19 days** after GW5, so a flag raised today cannot reach it. The same mechanism
handles a cup week, a postponement or a rescheduled fixture — none of which anyone has to enumerate.

⭐ *A rule expressed in the unit the world actually varies in needs no special case for each way it varies.*

`FLAG_HORIZON_DAYS = 8` — one fixture cycle, **declared not measured** (ADR-199's rule), **with a re-measure
date at the GW8 review** when the availability log has a month in it.

## ⚠️ Why the rate tier is computed twice rather than the answer divided

The obvious implementation scales the finished gameweek by `1 / chance`. It is **wrong for the `cold_start`
tier**, which carries the minutes weight *inside* its rate and non-linearly (ADR-124) — so the naive rescale
would be wrong for exactly the players with the least evidence to spare. `_rate_tier` was extracted and is
evaluated under both regimes, and a guard pins the non-linearity by asserting the far gameweek is **not** the
rescale.

⚠️ A first version of the headline guard asserted the exact `1 / 0.75` ratio and **failed** — because it had
landed in `cold_start` by default. The failure was correct behaviour. It now asserts against an **unflagged
twin**, which says what was actually meant.

## What it does

| João Pedro, 5 gameweeks | |
|---|---|
| before §1 | `{0.0, 0.0, 0.0, 0.0, 0.0}` |
| after §1 | `{4.3, 4.3, 4.3, 4.3, 3.9}` |
| **after §2/§3** | **`{4.3, 5.7, 5.7, 5.7, 5.2}`** |

**The recommendation now reads honestly in both directions: +0.6 over one gameweek, −2.4 over five.** Selling
him gains a rounding error this week and costs real points across the horizon — which is what the owner said,
and what the model can now say for itself.

Unflagged control untouched: Havertz `{4.9, 5.3, 4.9, 4.9, 4.4}`, identical before and after.

⚪ One mutant **recorded as equivalent**: widening the flag test from `< 1.0` to `<= 1.0` gives unflagged
players a "far" regime too, but `weight / 1.0` is byte-identical — a wasted computation for 636 players and
no changed number.

## Definition of Done

- ✅ **Tests** — 8 more (`tests/test_flag_horizon.py`); **1857 passed**, ruff clean; 12 mutants, 11 red
- ✅ **Manual smoke** — live cache at a fixed clock: the discount holds for GW5 (kickoff tomorrow) and lifts
  for GW6–9 (past the 19-day break); unflagged players byte-identical
- ✅ **Docs** — ADR-206 updated, index row, `config.py`, PROJECT_STATUS, this sprint doc

**Still open, deliberately:** the *gate* is undecayed — an injured player stays 0 across the horizon, since
FPL's return dates live only in free-text `news`. Guarded so the lift cannot leak to him.
