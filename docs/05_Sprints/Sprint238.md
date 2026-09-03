# Sprint 238: Project the team they will field (ADR-177)

**Dates:** 2026-09-03
**Status:** ✅ Complete — ADR-177. **1706 → 1713 tests, ruff clean.**

> **Owner**, on ⚔️ Head to head, reading it against the league table directly above it:
> *"You are showing MICKA score at 59.9 and TS (i.e. my score) at 70 — he is above me in the league?"*

He was. By **23 points**.

---

### 🔧 What shipped

Two faults were sitting on top of each other, and only one was a copy problem.

**1. The card looked like a scoreboard and was a forecast.** The strip projects the *next* gameweek; the table
above it is points *already banked*. Nothing said so. The season standing now sits above the projection —
*"On the season so far, Micka is 23 points ahead (188 v 165). Everything below is GW3 only."*

**2. A spent chip was being projected into next week.** `_starters` read FPL's `multiplier` at face value, so
a bench-boosted manager was priced on **fifteen** players against a rival's **eleven**. The eleven is now
derived from `position` (1-11) and `is_captain` (×2). The chip is named on the card. **Free Hit is the one
chip a different count cannot repair** — that squad is discarded at the deadline and the previous one returns,
so GW−1's picks are read instead, and where GW−1 is unavailable the comparison is declined rather than faked.

---

### 🔬 How it was found — and the part worth keeping

**The diagnosis came out of the screenshot's own arithmetic, before a single fetch.**

- The five listed differentials summed to **exactly 25.7**, and 34.2 + 25.7 = **59.9** — their total. So that
  table was *complete* at five rows, and the rival was on **eleven** players.
- The caption said **14 differentials**. 14 − 5 = 9 on our side. With 6 shared, that put us on **fifteen**.

Fifteen active players is a chip. The league table then corroborated it independently: season totals minus the
GW column give GW1 scores of 60 · 38 · 59, so GW2 was the last completed week — the one in which TS scored
**127 and climbed 14 places**.

Then it was reproduced with synthetic payloads on a flat 4.0 xP map, which is what turned a hypothesis into a
finding: **two identical squads, one bench-boosted, projected 16 points apart.**

---

### 💡 The lesson

> **Right reasoning, wrong question.**

ADR-161 §3 explicitly defended reading the multiplier at face value: *"re-deriving it from `is_captain` and
the 1-11/12-15 split would silently get every chipped gameweek wrong."* Every word of that is **true** — of
the question it was written about, which is *what did this squad **score** last week*. The module asks a
different one: *what will it score **next** week*, when the chip is spent.

Nothing was sloppy. A correct justification was carried into a new question, where it stopped being correct
and kept looking authoritative. **When code moves to a new question, its justifications do not move with it —
and a comment explaining why something is right is the last place anyone looks for a bug.**

The corollary that made the fix safe: deriving the XI **reproduces FPL's multipliers exactly for an unchipped
squad**. That no-op is why it could be applied unconditionally rather than behind a chip check — a fix that
provably cannot touch the common path needs far less nerve than one that might.

---

### 🔬 A fixture modelling less than reality — again

The test helper handed every pick `position = i`, so a "benched" player sat at **position 4** and was benched
*only* because the fixture also wrote `multiplier = 0`. The payload it produced **could not tell a bench from
an XI by the field FPL actually uses for it.**

So no test could have caught this bug, however many had been written. That is the fourth time this pattern has
been the root cause (`_worth_player` with minutes = 0 · a test recomputing xP without `gw_history_by_code` ·
two `_FakeStore`s missing a method). Bench players now sit at 12+, the way FPL numbers them.

**The check it earns: when a fixture is simpler than the payload, ask which field the code under test
actually reads — and whether the fixture can distinguish it at all.**

---

### 🧪 Tests

**+7, −1.** The removed one is the point:
`test_the_multiplier_is_taken_at_face_value_so_chips_are_not_re_derived` asserted the defect. It was right
about ADR-161's question and defended the bug the moment the same code was pointed at a new one. **A test that
fails when you fix a bug is defending the error** — it now asserts the requirement (*a chip played last week
does not change next week's projection*) rather than the mechanism.

Every guard mutation-checked, reverted one at a time and confirmed red:

| mutation | caught by |
|---|---|
| the old behaviour (multiplier at face value) | 3 tests |
| no bench cut — everyone in the payload starts | 2 tests |
| captain not doubled | 4 tests |
| Free Hit never detected | 1 test |
| an unknown chip code hidden rather than shown | 1 test |

---

### ✅ Verified against live data, not the schema

A real bench-boosted entry, GW2: all fifteen carry `position` and `is_captain`; **positions 12-15 carry
multiplier 1** — exactly the input that broke it — while `position` still says they are the bench. Priced
through `decision_xp` at `horizon=1`: **67.6 → 58.9 xP**, four bench players.

**Negative result, recorded so nobody re-runs it:** the sweep for the same fault class elsewhere came back
clean. `effective_ownership` already reads `position < _BENCH_FROM`; `captain_split` reads `is_captain`, which
a triple captain does not change.

---

### ✅ Owner-verified, same day

> *"Rebooted, gap is now +1.4."*

```
before:  you 70.0  ·  Micka 59.9  ·  gap +10.1
after :  you 61.3  ·  Micka 59.9  ·  gap  +1.4
correction: -8.7 xP — four bench players
```

The expectation was **pre-registered in the ADR before the code was written** — *"a dead heat or a small
deficit"* — then narrowed to *"a point or two"* once the live analogue was measured. It came in at a point or
two, and the fix is confirmed on the data that reported the fault.

⚠️ **The decimal match is a coincidence, and saying so is the point.** The analogue's −8.7 came from a
*different* manager's bench; two benches happening to be worth the same is luck. **The band was the
prediction. Claiming the decimal would be reading precision into a method that has none** — and this project
has been caught once already pitching a sprint on a remembered number that turned out to be wrong (ADR-157).
