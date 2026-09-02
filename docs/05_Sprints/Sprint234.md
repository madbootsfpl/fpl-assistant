# Sprint 234: The minutes you have actually played (ADR-173)

**Dates:** 2026-09-02
**Status:** ✅ Complete — ADR-173. **1667 → 1679 tests, ruff clean.**

> **Owner, reading his own gameweek plan:** *"There is no chance I would transfer Calafiori… the transfer
> decision is being made based on next week's game… there is value in letting your transfers build up."*

---

### 🔧 What shipped

**1. The xMins weight uses minutes actually played** — but only for a player who appeared in **every
completed gameweek**, with minutes in each. **2. The week's answer calls `bank_or_use`** (ADR-132), which had
existed since Sprint 184 and been wired to the Transfer tab alone. **3. A transfer states its longer-run
value** beside its weekly one, and names the disagreement when there is one.

| player | before | after | |
|---|---|---|---|
| **Calafiori** | 2.00 | **4.50** | the case that prompted it |
| **Kinsky** | 0.50 | **2.60** | ⭐ reported **2026-08-18**, open ever since |
| **Mendy** | 2.80 | **1.90** | corrected *down* — 60 mins a game, modelled as nailed |
| **Haaland** | 6.30 | **7.60** | plays 90 every week, held below 1.0 by last season |

**Calafiori → Truffert: +2.30 → −0.10. The transfer disappears** — the owner's judgement, reached by
arithmetic.

---

### 💡 The lesson

> **Test the user's diagnosis, not just their complaint.**

He was right that the recommendation was wrong and wrong about why. His proposed fix — a 3-5 gameweek horizon
— was measured and **makes it worse**: the gain runs +2.30 at one gameweek to **+10.00 at five**, because a
longer window multiplies a suppressed rate rather than correcting it. Building what was asked for would have
sold Calafiori with *more* confidence and looked responsive doing it.

The real cause was minutes: rate 5.29 pp90 (sound), xMins **0.43** from last season's injury-hit minutes
against the **0.94** he had actually played.

**And the guard is the decision, not a caveat.** ADR-125 deferred this on sample size and that objection is
real — two gameweeks cannot tell a player rested once from one being phased out. So the rule refuses the
ambiguous case entirely: a 0-minute gameweek returns None and he keeps his historical share. What is left is
the case with no ambiguity at all. That is what let a decision deferred to GW4-6 ship at GW3 without lowering
the bar it was deferred against.

Worth noting what it does **not** fix: `FORM_WEIGHT` is still 0, so the model still cannot see that Calafiori
is *scoring* well — only that he is *playing*. The right answer, for a slightly different reason than the
owner would give.

---

### ⚠️ Three tests and a fake modelling less than reality

- `test_build_starts_the_bench_in_recommended_order` recomputed xP **without** `gw_history_by_code` and
  asserted the app's ordering matched. Harmless while that argument only fed the dormant form term; it now
  drives the minutes weight, so the test compared one ranking against a different one.
- Two `_FakeStore`s had no `get_gw_history_by_code`, which the real `Storage` has always had.
- A stubbed `suggest_transfers` returned `[{"out": {"id": 4}}]` — the real one never returns a move without
  `gain` and `in`.

> **Same species as ADR-172's `_worth_player` yesterday: a fixture modelling less than reality, which passes
> right up until the code reads the missing part.** Review does not catch these. The thing that catches them
> is a change that touches one more field — which is a poor early-warning system, and worth saying out loud
> rather than filing as four unrelated fixes.

---

### 🧪 Tests

**+12**, every guard mutation-checked in both directions: dropping the *played-every-gameweek* check fails ·
accepting rows without a scoreline fails · showing the banking line unconditionally fails · never naming the
longer-view disagreement fails · the plan dropping its timing verdict fails.
