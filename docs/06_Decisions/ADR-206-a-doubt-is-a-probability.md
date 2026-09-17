# Architectural Decision Record: A doubt is a probability, not a verdict

**Decision ID:** ADR-206
**Date:** 2026-09-17
**Status:** ✅ **§1 Accepted — built. §2 and §3 Proposed, deliberately not built.**
**1842 → 1849 tests, ruff clean. 5 mutants, all red.**
**Superseded By / Replaces:** Replaces [ADR-006](./ADR-006-expected-points-v0.md)'s binary availability gate.
Completes [ADR-038](./ADR-038-expected-minutes-v0.md), whose chance factor has never once been applied.
Mirror image of [ADR-192](./ADR-192-no-opinion-is-not-full-confidence.md).
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner, on the week's plan for RoboTS:

> *"It's picking up that there is an issue with João Pedro, which is great. However we are coming into an
> international break, he is hot, so I would not sell him."*

The app was recommending **João Pedro → Havertz at +4.7 XI xP**, with Confidence 95/100 and the reason
*"Higher projected points (4.9 vs 0.0)"*.

João Pedro is **8.2 points per game — joint-highest of any forward in the game, level with Haaland** — with
four consecutive 90s and 11/9/1/12. He is **74.5% owned.** Havertz is 4.2 ppg. The app had him at **0.0**.

**That is not a judgement call the owner disagreed with. It is a mechanism fault.**

---

### 🔍 What was actually wrong

`xp._status_is_active` was:

```python
return p["status"] == "a"
```

Anything other than *available* scored **zero**. So every **doubtful** player was priced at 0 — and a 75%
doubt and a 25% doubt priced **identically**. On the day this was found: **23 players, at chance values of
25, 50 and 75, every one of them at 0.0.**

Meanwhile `minutes.chance_factor` (ADR-038) computed **exactly the right number** — 0.75 for João Pedro — and
deliberately excluded `d` from its unavailable set. It never got to apply it, because the binary gate ran
first and returned False.

⭐⭐ **TWO MECHANISMS MODELLED THE SAME THING AND THE CRUDER ONE RAN FIRST**, so the finer one was dead code
for precisely the population it was written for.

#### ⭐ ADR-006's reasoning had expired, not been wrong

It justified the binary explicitly:

> *"`chance_of_playing` is barely populated, so `status` is the [signal]."*

**True when it was written.** Preseason, the column was empty. FPL now populates it — 25/50/75 across 23
players — and nothing re-checked the premise. ⭐ *A constraint recorded in an ADR is a fact about a version,
not a law* ([ADR-180](./ADR-180-the-accent-belongs-to-the-theme.md)), and this is the second time that lesson has
cost something.

#### ⚠️ And someone had already found it, at one call site

`captain.py` carried:

```python
is_available=lambda p: not is_unavailable(p),   # count doubtful, not only 'a'
```

A local override, with a comment naming the exact bug — written for captaincy and left broken everywhere
else. Transfers, the lineup, the week's plan and every board all used the default.

⭐⭐ **A WORKAROUND AT ONE CALL SITE IS A BUG REPORT NOBODY FILED.** Same family as
[ADR-181](./ADR-181-one-recipe-means-every-caller.md): the fix existed, it just wasn't the default.

#### Three definitions of "unavailable", disagreeing

| where | set |
|---|---|
| `xp._status_is_active` | only `a` counts — everything else is out |
| `minutes._UNAVAILABLE` | `{i, s, u}` |
| `optimizer.UNAVAILABLE_STATUS` | `{i, s, u, n}` |

⭐ *A fix in one of three definitions is a fix in one third of the app.*

---

### 🎯 Decision — §1, built

**The gate answers "can he play at all?" The chance factor answers "how likely is he to?"** They were
collapsed into one binary, and the binary won.

- One definition of unavailable, in `minutes.py` — the module that already owns availability and imports
  nothing. `optimizer` re-exports it under its existing name, so **all sixteen call sites are untouched**;
  moving them would be a rename pretending to be a fix.
- `xp._status_is_active` → `not is_unavailable(p)`. Doubtful players pass and are priced by the multiplier
  that already existed.
- `captain.py`'s override **removed** — it now equals the default — with a test pinning the behaviour so its
  removal cannot silently regress.

⚠️ **`"n"` added to the shared set, closing a hole the fix would otherwise have opened.** An unregistered
player's `chance` is None, which `chance_factor` reads as *"no news, assume available"* → **1.0**. Letting
non-`a` statuses through the gate without this would have priced a player who is not in the squad at full
value. No `n` rows exist today, so it closes a hole rather than changing a number.

**`--no-xmins` now scores a doubtful player at his full rate, deliberately.** That view is documented as
*"assumes they play"*; for `i`/`s`/`u`/`n` the assumption is not counterfactual but meaningless, so they stay
zeroed in both views.

---

### 📊 What changed

| | before | after |
|---|---|---|
| doubtful players projecting > 0 | **0 of 23** | **21 of 23** |
| João Pedro, next GW | 0.0 | **4.3** (5.7 if fit, × 0.75) |
| João Pedro, 5 GWs | `{0.0, 0.0, 0.0, 0.0, 0.0}` | 21.1 |
| **the recommendation** | **João Pedro → Havertz, +4.7** | **+0.6 — inside the noise floor** |

⭐ **Discounted, not deleted**: no doubtful player enters the top 10 of the board, and João Pedro still sits
*below* Havertz. The risk is still priced. It is no longer annihilation.

---

### ⚠️ The whole suite stayed green

**1842 tests, not one red**, while 23 players moved from 0.0 to real projections and the headline
recommendation reversed. Nothing had ever asserted what a *doubtful* player is worth — only that an
unavailable one is worth nothing.

⭐ **"All tests pass" after a behavioural change is a statement about the tests.** Second time in two days,
after ADR-195's dormant term. Seven guards added, five mutants, all red.

---

### ⭐⭐ The lesson, and its mirror

[ADR-192](./ADR-192-no-opinion-is-not-full-confidence.md) found that *no opinion* was implemented as **the
most optimistic opinion available**: a player with no history got a minutes multiplier of **1.0**, the maximum.

This is the same failure pointing the other way: *a doubt* was implemented as **the most pessimistic verdict
available** — 75% likely to play, priced at **0**, the minimum.

⭐⭐ **WHEN A MODEL EXPRESSES UNCERTAINTY AS A NUMBER, CHECK WHICH EXTREME THAT NUMBER IS.** It will be one of
them, in whichever direction nobody happened to be looking — because the neutral-seeming value of a multiplier
is never neutral.

---

### 📋 §2 and §3 — Proposed, and not built

**§2 — a flag is a fact about now, priced as a fact about the whole horizon.** Even corrected, João Pedro's
0.75 applies to **GW9 in November**. A doubt about tomorrow should decay toward fit as the horizon extends.
⚠️ Needs a decay shape **measured, not invented** — ADR-199's rule, and there is no measurement yet.

**§3 — fixture gaps are information.** The owner's own point: GW5 kicks off tomorrow and **GW6 is 19 days
later** (2026-10-10). A knock before a three-week break is a different thing from a knock before a Saturday.

⭐ **§3 falls out of §2 for free, if the decay is measured in *days until kickoff* rather than *gameweeks
ahead*.** Then an international break needs no concept of its own — a 19-day gap simply gives the flag 19 days
to decay. **Gated on the owner's call**, and on a measurement that does not exist yet.

---

### 📊 Consequences

**Good:** the most-owned forward in the game stops being priced at zero; 23 players are ranked by how likely
they are to play rather than by a binary; the captain picker's workaround becomes the rule; three definitions
of one concept become one.

**Costs / limits:**
- ⚠️ **This corrects the level and not the shape.** A doubt still applies flatly across five gameweeks, which
  is §2, and is left visibly open rather than half-solved.
- FPL's `chance_of_playing` is a coarse signal (25/50/75) refreshed at the provider's discretion, and
  ADR-203's log only started today — so its own accuracy is unmeasured. It is better than a binary, which is
  a different claim from being right.
- Every surface that reads "flagged → bench or replace" now rests on a real number and should eventually say
  *how* doubtful. Not changed here.

---

### 🔗 Links

- [ADR-006](./ADR-006-expected-points-v0.md) — the binary this replaces, and the expired premise
- [ADR-038](./ADR-038-expected-minutes-v0.md) — `chance_factor`, finally reachable
- [ADR-192](./ADR-192-no-opinion-is-not-full-confidence.md) — the same failure, opposite extreme
- [ADR-203](./ADR-203-availability-is-recorded-as-it-passes.md) — which will eventually let §2 be measured
