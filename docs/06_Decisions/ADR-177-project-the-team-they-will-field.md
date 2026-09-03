# Architectural Decision Record: Project the team they will field

**Decision ID:** ADR-177
**Date:** 2026-09-03
**Status:** ✅ **Accepted — built** (Sprint 238, 2026-09-03). **1706 → 1713 tests, ruff clean.**
**Superseded By / Replaces:** **Amends ADR-161 §3** (*"FPL's `multiplier` is taken at face value"*). That
paragraph is correct for the question it was written about and wrong for the one this module actually asks.
**No `decision_xp` change** — the projection recipe is untouched; only *whose minutes are counted* changes.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Owner-reported, from the live app on a phone. ⚔️ Head to head showed:

> **YOU 70.0 · MICKA 59.9 · GAP +10.1**
> *"6 shared starters cancel out (34.2 xP each way). 14 differentials decide it, and on projection you lead
> by 10.1."*

…directly beneath a league table in which **Micka is first on 188 and TS is second on 165**. The owner's
question was the right one: *"he is above me in the league?"*

Two separate faults were sitting on top of each other, and only one of them is a copy problem.

#### Fault 1 — the card looks like a scoreboard and is a forecast

The strip is projected points for the **next** gameweek. The table above it is points **already banked**.
Nothing on the card says so; the caveat underneath talks about stale picks and win probability but never
mentions that the season standing runs the other way. A reader comparing the two numbers on the same screen
is doing the obvious thing, and the surface is what made it obvious.

#### Fault 2 — a spent chip is being projected into next week (the real bug)

This was diagnosed from the arithmetic on the owner's screenshot alone, before any fetch:

- Their five listed differentials sum to **exactly 25.7** (7.6 + 4.9 + 4.8 + 4.5 + 3.9), and
  34.2 + 25.7 = **59.9** — their total. So that table is *complete* at five rows, and Micka is being
  projected on **11 players**.
- The caption says **14 differentials**. 14 − 5 = 9 on our side. With 6 shared, that puts TS on **15**.

Fifteen active players is a chip. The league table corroborates it independently: season totals minus the GW
column give GW1 scores of 60 · 38 · 59, so **the last completed gameweek is GW2**, in which TS scored **127
and climbed 14 places** — a Bench Boost week. `manager_projection` already returns `chip`; the view has never
read it.

The mechanism reproduces exactly, with synthetic payloads and a flat 4.0 xP for every player:

```
6 shared, mine bench-boosted (15 active), theirs a normal 11:
    shared: 6   my_edge: 9   their_edge: 5
    "6 shared starters cancel out (…). 14 differentials decide it…"

the SAME two squads, priced twice:
    without the chip -> mine: 48.0  theirs: 48.0  gap:   0.0
    with    the chip -> mine: 64.0  theirs: 48.0  gap: +16.0
```

Two identical squads, a sixteen-point lead. **The +10.1 is, to a first approximation, four bench players.**

#### Root cause: right reasoning, wrong question

`src/analytics/h2h.py::_starters` takes FPL's `multiplier` at face value, and ADR-161 §3 defends that
explicitly:

> *It already encodes the captain (2), the triple captain (3), a benched player (0) and — crucially — Bench
> Boost, which makes all fifteen count. Re-deriving it from `is_captain` and the 1-11/12-15 split would
> silently get every chipped gameweek wrong.*

Every word of that is true **for reconstructing what a squad scored in the gameweek that has finished**. This
module does not do that. It prices the picks payload with a `horizon=1` projection of the gameweek **still to
come** — in which the chip has been spent, the bench is a bench again, and a triple captain is a captain.

The failure is asymmetric and therefore invisible: it never looks like an error, it looks like a lead.

#### Decision Drivers

- **Driver 1 — the two sides must be counted the same way.** Eleven against fifteen is not a comparison. This
  is the same objection ADR-161 raised against writing a second projection recipe for a rival's squad: *"it
  would be measuring the two models against each other rather than the two squads."*
- **Driver 2 — it fires for everyone, in both directions.** Any manager in the league who chipped is
  over-projected; face a rival who bench-boosted and you are under-projected against them. Roughly one
  manager in a mini-league per chip week.
- **Driver 3 — the fault is silent.** Nothing about a +10.1 announces itself as wrong. It took the owner
  reading two surfaces against each other to find it, which is not a repeatable detection method.
- **Driver 4 — the honest limit stays stated.** ADR-161's real caveat (these are last gameweek's picks; they
  can still transfer) is unaffected and must survive intact.

---

### 💡 Options Considered

#### Option 1: Derive next week's eleven from `position` + `is_captain` *(Chosen)*
* **Description:** Stop asking the payload *"what did this player score last week?"* and ask *"will he start
  next week?"* — positions 1-11 start, the captain doubles, the bench sits. The stored `multiplier` is no
  longer consulted for who plays.
* **Pros:**
  - ✅ **A no-op in the ordinary week.** For an unchipped squad, positions 1-11 plus `is_captain` reproduce
    FPL's multipliers exactly — so this changes nothing for the ~95% case and only corrects the chipped one.
  - ✅ Symmetric by construction: both sides are counted by the same rule, and neither can be counted twice.
  - ✅ ADR-161 §3's objection **dissolves rather than being overruled** — it warned against re-deriving *last
    week's score*. We are not deriving last week's score.
  - ✅ No new data and no extra network call.
* **Cons:**
  - ❌ Depends on `position` being present. Payloads carry it, but a fallback is still needed.
  - ❌ Silently assumes the bench order and the XI carry over, which is exactly what the existing "they can
    still transfer" caveat already concedes.

#### Option 2: Keep the face-value multiplier, add a caption saying they chipped
* **Description:** Leave the number alone; print *"you played Bench Boost"* beside it.
* **Pros:**
  - ✅ Smallest possible change; ADR-161 stands untouched.
* **Cons:**
  - ❌ **The headline number stays wrong**, and the headline number is the feature. A caveat under a wrong
    number is not a correction.
  - ❌ The differential table keeps listing four bench players as "what you have that they don't", which is
    the part a reader would act on.

#### Option 3: De-chip only when `active_chip` says a chip was played
* **Description:** Branch on the chip code and repair the multipliers for that case only.
* **Pros:**
  - ✅ Surgical; leaves the common path byte-identical.
* **Cons:**
  - ❌ Two code paths for one question, and the rarely-taken one is the one that has to be right.
  - ❌ Trusts `active_chip` to be present, when Option 1 gets the same answer without needing it.

---

### 🎯 Decision & Justification

**Chosen Option:** Option 1 — derive the eleven, and say what the numbers are.

**Reasoning.** The bug is not that the multiplier was read wrongly; it is that it answers a different
question. Deriving the XI asks the question this module actually has, and the reason ADR-161 gave for not
deriving it does not apply to a forward projection. That it is provably a no-op for an unchipped squad is
what makes it safe to apply unconditionally rather than behind a chip check.

**Four changes:**

**1. Project the eleven they will field.** `_starters` derives from `position` (1-11) and `is_captain` (×2),
not the stored multiplier. Where `position` is missing, fall back to the multiplier and carry on — a slightly
wrong comparison beats no comparison, and the fallback is already the code that exists today.

**2. Name the chip on the card.** `manager_projection` has returned `chip` since ADR-161 and no surface has
ever shown it. *"You played Bench Boost in GW2 — that is spent, so this projects your eleven."* This is
useful in its own right and it is also the thing that would have made Fault 2 self-reporting.

**3. Free Hit reverts, so read the squad it reverts to.** A Free Hit squad is the one case Option 1 cannot
fix by counting differently: the whole fifteen disappears at the deadline and the previous squad comes back.
FPL does not publish the reverted team — but it published it the week before. So for a side whose
`active_chip` is `freehit`, read **GW−1's** picks for that manager (one extra call, only in that case) and
project those. If GW−1 is unavailable, **decline the comparison and say why** rather than project a squad
that will not exist.

**4. Put the season standing next to the projection.** The gap that started this. The standings row already
carries `total` for both entries, so it costs nothing: *"Micka is 23 points ahead on the season. This is next
gameweek only."* Fault 1 is fixed by the sentence the owner had to work out for himself.

#### ⚠️ One existing test pins the defect and must be rewritten

`tests/test_h2h.py::test_the_multiplier_is_taken_at_face_value_so_chips_are_not_re_derived` asserts a
bench-boosted projection counts all fifteen. It will fail, and it **should** — this project's standing rule is
that *a test which fails when you fix the bug is defending the error*. It gets rewritten to assert the
requirement rather than the mechanism: **last week's chip does not change next week's projection**, i.e. the
same fifteen players project identically whether or not a chip was active. The ADR-161 case it was really
protecting — that a captain's extra copy is priced as its own differential — is already covered by
`test_identical_elevens_with_different_captains_are_not_identical` and is untouched by this change.

#### 📐 Pre-registered expectation (recorded before building)

On the owner's live data, de-chipping removes four bench players from the TS side. **The +10.1 lead is
expected to shrink to roughly a dead heat or a small deficit.** Writing the expected direction *and rough
size* down now is the point: it is checkable at build time, and a result that lands far from it means the
diagnosis is incomplete rather than the fix being finished.

---

### 🔬 Verified at build time

**1. The payload shape the whole fix rests on — confirmed against the live API**, not against the schema.
A real bench-boosted entry, GW2:

```
picks: 15 | active_chip: bboost
all have position: True     all have is_captain: True
position -> multiplier: (1,1) (2,1) … (11,1) (12,1) (13,1) (14,1) (15,1)
automatic_subs: 0
```

**Positions survive the chip; the multiplier does not.** Twelve to fifteen carry a multiplier of 1 — that is
precisely the input that broke the head-to-head — while `position` still says they are the bench. So the
derivation path is the one that runs on live data, and the multiplier fallback is genuinely a fallback.

**2. The correction, priced on real xP.** The same live payload, through `decision_xp` at `horizon=1`:

```
old (face-value multiplier): 15 players -> 67.6 xP
new (ADR-177, the XI)      : 11 players -> 58.9 xP        chip still reported: bboost
```

**−8.7 xP**, which is four bench players. Against the pre-registered expectation: it lands at the **shallow
end** of the predicted band — enough to turn the owner's +10.1 into roughly a **point or two**, so a near
dead heat rather than the small deficit that was also allowed for. ⚠️ **This is an analogous squad, not his**
— his own number is confirmed at the manual smoke test, and the prediction stands or falls on that.

**3. ✅ CONFIRMED ON THE OWNER'S OWN DATA (2026-09-03, post-reboot).** *"Gap is now +1.4."*

```
before:  you 70.0  ·  Micka 59.9  ·  gap +10.1
after :  you 61.3  ·  Micka 59.9  ·  gap  +1.4        (Micka did not chip, so 59.9 is unchanged)
correction: -8.7 xP — four bench players
```

The pre-registration held: *"a dead heat or a small deficit"*, narrowed after the live analogue to *"a point
or two"*. It came in at a point or two.

⚠️ **The decimal match is luck, not precision.** The analogue measured −8.7 on a **different** manager's
bench-boosted squad; landing on −8.7 again here is a coincidence of two benches being worth the same. What
was predicted, and what should be read as confirmed, is the **band** — nothing in the method supports
forecasting a specific squad's bench to 0.1 xP.

**4. The sweep came back clean.** The risk register asked whether any other surface prices a completed
gameweek's picks forward. It does not: `effective_ownership` already reads `position < _BENCH_FROM` and never
touches the multiplier, and `captain_split` reads `is_captain`, which a triple captain does not change.
**Recorded as a negative result** — the next person to ask this question should not have to re-run it.

**5. Every new guard was mutation-tested** — reverted one at a time, confirmed red:

| Mutation | Caught by |
|---|---|
| the old behaviour (multiplier at face value) | 3 tests |
| no bench cut — everyone in the payload starts | 2 tests |
| captain not doubled | 4 tests |
| Free Hit never detected | 1 test |
| an unknown chip code hidden rather than shown | 1 test |
| the season-gap caption removed | the page test |
| the chip note not printed | the page test |

**The page test earns its own line.** The unit tests pin the projection; the two faults actually lived on the
**surface**, in control flow a pure-function test cannot reach — so one AppTest drives the real path (manager
id → league → the N-calls button → the rival picker) with two managers holding the **identical fifteen**, one
of them bench-boosted. Under the old code it reports *"on projection you lead by **18.1**"* between two
identical squads, which is the bug in one sentence.

**And it caught a copy fault in this ADR's own work**: the season line first read *"Micka is 23 points ahead
(165 v 188)"* — the sentence names Micka and the bracket leads with **my** total. Both are labelled by name
now. The mutation output is what surfaced it; nothing asserted it.

**6. One fixture was found modelling less than reality**, and it is the reason the bug could hide. The test
helper handed every pick `position = i`, so a "benched" player sat at position 4 and was benched *only*
because the fixture also wrote `multiplier = 0`. The payload it produced could not tell a bench from an XI by
the field FPL actually uses for it — so no test could have caught this, however many were written. Bench
players now sit at 12+, the way FPL numbers them.

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:**
  - The two totals become comparable, which is the only claim the card makes.
  - The differential tables stop listing bench players as an edge — the part a reader would have acted on.
  - Every chipped head-to-head in the league is corrected at once, in both directions.
  - The card stops contradicting the table above it without explanation.
* **Negative Impact / Trade-offs:**
  - The projection now assumes next week's XI is this week's XI. That is a real assumption and it is a
    **weaker** one than the assumption already conceded in the existing caveat (that they will not transfer).
  - Free Hit costs one extra network call in the rare week it applies.
  - A visible number moves, on a surface testers have seen. It moves *toward* the truth and the ADR says by
    how much.
* **Risks & Mitigations:**
  - **Risk:** a payload without `position` degrades to today's behaviour, silently. **Mitigation:** the
    fallback is explicit in the code and tested, and it is strictly no worse than what ships today.
  - **Risk:** auto-substitutions. FPL reports these in `automatic_subs` and leaves `position`/`multiplier` as
    they stood at the deadline, so the derived XI is the XI the manager *chose* — which is the right input
    for projecting the XI they will choose next. **To confirm against a live payload at build time.**
  - **Risk:** the same fault class elsewhere — any other surface that prices a completed gameweek's picks
    forward. `effective_ownership` and `captain_split` (ADR-141) read the same payloads. **Sweep them
    during the build and record the finding either way.**

---

### 🛠 Implementation & Migration
* **Components Affected:** Code (`src/analytics/h2h.py`, `src/web_streamlit/views/leagues.py`), Tests, Docs
* **Action Items:**
  - [x] `_starters` derives the XI from `position` + `is_captain`; multiplier fallback kept and tested
  - [x] Rewrite `test_the_multiplier_is_taken_at_face_value_so_chips_are_not_re_derived` to assert the
        requirement (a spent chip does not change next week's projection)
  - [x] Guard: an unchipped squad projects **byte-identically** before and after — the no-op claim, pinned
  - [x] Guard: bench-boosted and normal payloads for the same fifteen project the same number
  - [x] Guard: triple captain projects as a captain (×2), not ×3
  - [x] Free Hit: read GW−1 picks for that side; decline with a reason when unavailable
  - [x] Surface the chip on the card, and the season gap beside the projection
  - [x] Sweep `effective_ownership` / `captain_split` for the same forward-projection assumption
  - [x] Page-level guard: the real path, two identical fifteens, one bench-boosted
  - [x] **Mutation-test every new guard** — revert each one at a time, confirm red
  - [x] Manual smoke on the owner's own league — **done 2026-09-03, outcome below**
  - [x] Update ADR-161 with a pointer to this amendment; update PROJECT_STATUS and the Roadmap

#### ✅ Always
- [x] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

#### 🧭 If this ADR renames/moves/merges/retires a user-facing surface
**Not applicable** — no surface is renamed, moved or retired. ⚔️ Head to head stays where it is, on the
My Squad ▸ Leagues tab, with the same name. Copy is *added* (the chip, the season gap); none is retired, so
nothing goes into `RETIRED`.

---

### 🔄 Review & Reconsideration
* **Review Date:** 2026-10 (after a full chip-heavy gameweek has passed through the card)
* **Triggers for Reconsideration:**
  - [ ] FPL begins publishing a Free Hit manager's reverted squad — change 3 becomes a direct read
  - [ ] A payload is found without usable `position` data in the wild — the fallback stops being theoretical
  - [ ] The win-probability half of ADR-161 is ever ungated — it would consume these projections and inherit
        this assumption

---

### 🔗 References & Related Artifacts
- **Amends:** [ADR-161](./ADR-161-head-to-head.md) §3
- **Related:** [ADR-141](./ADR-141-league-import-and-elite-comparison.md) (Leagues, and the picks payloads this shares),
  [ADR-041](./ADR-041-one-xp-metric-and-squad-build-intent.md) (one projection recipe — the reason a rival is priced exactly as you
  are)
- **Found by:** the owner, reading the head-to-head card against the league table above it — the fourth
  consecutive analytics fault found by using the product rather than by a test (ADR-172, ADR-173, ADR-157).
