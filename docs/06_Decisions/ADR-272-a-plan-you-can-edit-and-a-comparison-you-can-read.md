# ADR-272 — A plan you can edit, and a comparison you can read

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner — Lab: *apply · edit · build mode · naming*; Mini-leagues: *side by side, and clarify
the xP*
**Builds on:** ADR-268 (the Lab), ADR-267 (H2H), ADR-225/260 (drafts)

---

## 1. The Lab

**Three modes, and they differ only in a budget and a horizon.** ⭐ *A free hit is played for **one
week***, and asking the solver for a run would give a different fifteen. A new season starts from
£100.0m and nothing owned — *that is the whole point of the mode*.

**Two build styles, and they are not a preference.** `0.1` spends on the eleven and buys a cheap bench
that plays; `1.0` values all fifteen equally, which is what a **Bench Boost** week actually asks for.

**⭐⭐ Editing is done by the solver, not by the screen.** Tapping a player sends him away and forces the
other fourteen back in, so exactly one changes — ⚠️ *and the budget stays honest without the screen doing
any arithmetic*, which a hand-rolled swap list would have had to get right on its own.

**A name, because a draft stopped being two moves.** ⚠️ *"Wildcard" and "Free Hit" are different plans
for the same fifteen*, and a screen showing one of them with no name cannot say which.

### ⚠️⚠️ "Apply" makes a plan, and cannot make a transfer

FPL has no write API. Applying writes the draft this app already draws on its own pitch (ADR-225) — and
the screen says so in as many words. ⭐ *Pretending otherwise would be the worst lie this screen could
tell.*

The base stays the **real** fifteen, so the draft can still tell it has gone stale, and `signalKeys` is
carried so coming back to it can say what changed. ⚠️ **No armbands are carried**: the captain you had may
not be in this squad at all, and ⭐ *a captain silently reassigned to whoever inherited the position is
worse than none.*

### 📌 No pitch in the Lab, and the reason is not effort

`PitchView` needs a real `MyTeam` — kits, fixtures, price moves, a deadline — and a built squad has none
of them. ⭐ *A second pitch drawn from thinner data would be a worse pitch.* Applying puts these fifteen
on the **real** one, which is also the answer to *"what does it look like?"* The list gains the
**formation** instead, because that is the thing a list genuinely cannot show and a wildcard often
changes.

## 2. ⚠️ A live defect found on the way

`Draft.copyWith` rebuilt the draft **without its signal keys**, so `_applyPlan` — the *"Play Them"*
button — silently emptied the record of what was known when the plan was made, and the screen then
reported everything as new.

⭐⭐ **The exact defect ADR-260 was written to prevent**, guarded in `swap` and `substitute` and then
reintroduced by the one path that looked too small to matter.

## 3. Mini-leagues

**Side by side.** ⚠️ Stacked, the two lists were *two lists*; beside each other they are **one
comparison** — *the question is "who is stronger where?", and an answer you have to scroll between cannot
be read as a comparison at all.*

**⭐⭐ And the number says what it measures.** Sitting under a league table, *"−1.6 behind"* reads as
**league points**, and it is not: it is projected points for the coming gameweek, **from each squad as it
finished the last one**. ⚠️ *A number that could be either of two things is read as whichever the reader
already had in mind.*

📌 Transfers, Rank and Chips parked at the owner's request.

## 4. ⚠️⚠️ The route rejected a board the service accepted

`watch` was added to `TrendingRequest.validate` and **not** to the endpoint's Pydantic `pattern`. The
service answered; FastAPI returned **422**. Every test here calls the service function — ⭐ *tests that
call the service never cross the route, and the route keeps its own copy of the rule.*

Found by **calling the deployed API**, not by the suite. A new test now derives the accepted boards from
the service, so a board added to one and not the other fails — ⭐ *the only way two copies of a rule stay
in step.*

## Verification

* **14 Dart tests** on modes, styles, formation, the diff, and what applying stores; **5/5 mutations
  killed**.
* **4 Dart tests** pinning `copyWith`, including the one that was live.
* **2 Python tests** over HTTP, one of them **proved** to catch the 422 by re-breaking the pattern.
* 2,562 Python · 234 Dart.
