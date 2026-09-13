# Architectural Decision Record: Bank to afford, not only to stack

**Decision ID:** ADR-186
**Date:** 2026-09-13
**Status:** ✅ **Accepted — built** (Sprint 248, 2026-09-13). **1746 → 1751 tests, ruff clean.**
**Superseded By / Replaces:** Extends [ADR-132](./ADR-132-transfer-timing.md)'s `bank_or_use`. **No
`decision_xp` change.** Second of three gaps from the owner's A/B; see ADR-185 and ADR-187.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner, on what the weekly answer misses:

> *"You are not suggesting to hold on making transfers for a couple of weeks to say buy a more expensive
> player than you can afford with current budget."*

#### The measurement

`RoboTS`, bank **£0.0m**, best available move as the affordability ceiling is raised:

| extra budget | best move | gain |
|---:|---|---:|
| **+£0.0m** | Watkins → Havertz | **7.40** |
| +£0.5m | Hume → Ballard | 7.90 |
| +£1.0m | Hume → Ballard | 7.90 |
| **+£1.5m** | **Watkins → Isak** | **13.80** |
| +£3.0m | Watkins → Isak | 13.80 |

**£1.5m is worth +6.4 xP.** There is a cliff, it is steep, and the app cannot see it: it evaluates every move
against today's bank and reports the best one as *the* answer, with no indication that a slightly larger
budget changes the answer entirely.

#### What `bank_or_use` actually asks

```
bank when   min(second_gain, hit_cost)  >  first_move_gain_next_gw
```

It weighs **banking a transfer to make a second move next week**. Useful, and shipped by ADR-132. But it has
**no concept of a price threshold** — nowhere does the codebase ask *"what could I afford if I waited?"* The
word "bank" in the app means *a spare transfer*, never *money*.

#### Decision Drivers

- **Driver 1 — the cliff is invisible, not merely unadvised.** A manager shown *"Watkins → Havertz +7.4"* has
  no way to know that £1.5m more nearly doubles it.
- **Driver 2 — it is a *reachable* £1.5m.** Not hypothetical: price rises accumulate, and a cheaper
  first sale frees it. Which is precisely the sequencing question ADR-187 covers — the two gaps meet here.
- **Driver 3 — recommending a move that forecloses a better one is worse than recommending nothing.** Spend
  the budget on Havertz and Isak is gone for weeks.

---

### 💡 Options Considered

#### Option 1: Report the affordability cliff alongside the move *(Chosen)*
* **Description:** sweep the best move at a few budget increments above the current bank. Where a materially
  better move sits within reach, say so.
* **Pros:**
  - ✅ **Pure arithmetic over an existing function** — `suggest_transfers` already takes `bank`. No model, no
    search, no new data.
  - ✅ Reports a fact rather than a strategy: *"£1.5m more and this becomes Watkins → Isak, +13.8."* The
    manager decides whether it is reachable; he knows his price rises and we do not.
  - ✅ Silent when there is no cliff, which is most weeks.
* **Cons:**
  - ❌ Several extra `suggest_transfers` calls. Bounded and cheap, but not free.
  - ❌ It says *"if you had the money"* without saying **how to get it**. Honest, and less than the owner
    asked for.

#### Option 2: Model the accumulation — predict price rises and time the move
* **Cons:** ❌ Depends on the price predictor (ADR-092), whose own accuracy is unverified in-season. ❌ It
  would turn a hard fact (*the cliff exists*) into a forecast about a forecast. **Two uncertain models
  multiplied is how a heuristic becomes a guess.**

#### Option 3: Search sell-combinations that free the money
* **Cons:** ❌ That is the multi-move path search of **ADR-187** and belongs there, gated on its own evidence.
  Building half of it here would pre-empt that decision without the measurement to justify it.

---

### 🎯 Decision & Justification

**Report the cliff; do not model the climb.**

> *"Watkins → Havertz **+7.4** now. With **£1.5m** more it is **Watkins → Isak, +13.8** — worth waiting for
> if you can raise it."*

The step from £0 to £1.5m is a *fact about today's market*, computed exactly. The step from *"you have £0"* to
*"you have £1.5m"* is a forecast about price movement we have not verified. **This ADR ships the half that is
arithmetic and refuses the half that is prediction** — which is the same line ADR-161 drew when it shipped the
head-to-head decomposition and gated the win-probability sim.

**Thresholds, chosen to avoid crying wolf:** report only when the better move gains **≥2.0 xP more** and sits
within **£2.0m**. Both are provisional and should be re-measured once there is a season of squads to check
against — recorded here so the next person tunes them against data rather than taste.

---

### 🔬 Built — what the answer says now

On the owner's squad, beneath the recommended transfer:

```
Transfer: Watkins (AVL) → Havertz (ARS)  (+7.4 XI xP over 5 GW)  · Confidence 95/100 · High
          Worth saving for: £1.5m more makes this Watkins → Isak (+13.8 XI xP, +6.4 on the move above)
```

The move you can make today stays the headline. The cliff is a reason you *might* wait, placed after it and
never instead of it — a manager who cannot raise the money must still be told what to do now.

`gameweek_plan` gains a `cliff` key, always present, `None` when there is nothing worth saying — which is
most weeks, and the reason this is safe to add to a page ADR-180 has just been decluttering.

#### ⚠️ The wiring test skipped instead of failing — twice over

The first attempt at a wiring guard asserted `"cliff" in plan` and then **returned early when the value was
`None`** — which is precisely what the mutation produces. It skipped exactly when it should have failed.

> **A test that skips is not a test that passes** (ADR-178), and this is the third sprint running in which
> the guard I wrote for a new feature protected nothing on its first attempt.

Rewritten to assert **the call**: `gameweek_plan` must ask `affordability_cliff`, with this squad, this
market and **this bank** — which holds whether or not today's data happens to contain a cliff. Two mutations
now die there: dropping the call, and passing a hard-coded `bank=0.0` instead of the squad's real bank.

#### 🔬 And the fixture had to grow twice

It reached `affordability_cliff` fine, then failed on `team` (the renderer prints it), then on `status`,
then on `points_per_game` — because `gameweek_plan` also picks a captain, which prices players through
`decision_xp`.

> **A fixture aimed at one function has to satisfy every function on the path to it.** Each failure was the
> same shape: modelling less than the payload, which is this repo's most persistent test defect.

**Five mutations, all caught.**

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:** the answer stops silently foreclosing better moves; a real lever the owner uses by
  instinct becomes visible; no new model.
* **Negative Impact / Trade-offs:** a line that sometimes says *"wait"* without saying *how* — genuinely less
  useful than the owner's own judgement, and it should not pretend otherwise.
* **Risks & Mitigations:**
  - **Risk:** managers hold transfers chasing a cliff they never reach. **Mitigation:** the copy says *"if you
    can raise it"*, and the immediate move stays the headline.
  - **Risk:** threshold-tuning by taste. **Mitigation:** flagged above as provisional, with a re-measure.

---

### 🛠 Implementation & Migration
* **Components Affected:** Code (`analytics/transfer_timing.py`, the gameweek answer), Tests, Docs
* **Action Items:**
  - [x] `affordability_cliff(owned, market, xp, bank, *, steps, min_gain)` — pure, no I/O
  - [x] Surface it on the week's answer, beneath the recommended transfer
  - [x] Guard: RoboTS's £0 → £1.5m case reports the Isak cliff
  - [x] Guard: a squad with no cliff reports **nothing** — silence is the common case
  - [x] Guard: the immediate move remains the headline; the cliff never replaces it
  - [x] **Mutation-test every guard**; clean suite re-run between mutants
  - [x] Record the two thresholds as provisional, with a GW10 re-measure

#### ✅ Always
- [x] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

---

### 💡 The lesson

> **"Bank" meant a spare transfer everywhere in the codebase, and a manager means money.**

The feature was not missing because it was hard — it is a loop over `suggest_transfers` with a bigger number.
It was missing because the word had been claimed by a different concept, and nobody noticed the other meaning
was unimplemented. **A term that means one thing in the code and two things to the user hides the half you
did not build.**

---

### 🔗 References & Related Artifacts
- **Extends:** [ADR-132](./ADR-132-transfer-timing.md) (`bank_or_use`)
- **Line-drawing precedent:** [ADR-161](./ADR-161-head-to-head.md) — ship the arithmetic, gate the forecast
- **Sibling gaps:** ADR-185 (wildcard) · ADR-187 (multi-GW planning)
- **Found by:** the owner's two-team A/B
