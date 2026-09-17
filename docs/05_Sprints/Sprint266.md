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
