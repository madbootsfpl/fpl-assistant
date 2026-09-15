# Architectural Decision Record: "No opinion" is not full confidence

**Decision ID:** ADR-192
**Date:** 2026-09-15
**Status:** 📋 **Proposed** — gate before building. The **direction** is the decision; the **constant** is a
measurement and is deliberately not chosen here.
**Superseded By / Replaces:** Fills the crater [ADR-173](./ADR-173-minutes-you-have-actually-played.md) named
and left open, and revisits the zero-evidence end of [ADR-104](./ADR-104-cold-start-xp-floor.md). Same family as
[ADR-172](./ADR-172-a-shrink-needs-something-to-shrink-toward.md) (the rate half) and
[ADR-185](./ADR-185-price-the-rebuild.md)'s A/B finding.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner, on the second move in his week's plan — **Konsa (ARS) → Affengruber (FUL)**, +9.3 xP over five
gameweeks:

> *"Not sure on Konsa — more likely to be a higher performer than a Fulham back!!"*

He is right, and the histories say so plainly:

| | **Affengruber** (FUL) | **Konsa** (ARS) |
|---|---|---|
| this season | GW3 **0 mins** · GW4 **90 mins, 8 pts** | GW1 0 · GW2 11 · GW3 **90** (4) · GW4 **90** (6) |
| past seasons on record | **0** | **7** |
| rate source | `cold_start` | `hist` |
| rate | **4.40** | 2.98 |
| **expected minutes** | **1.00** | **0.88** |
| 5-GW projection | **22.4** | 13.1 |

**A player with one appearance in his career outprojects one with seven seasons and two consecutive full
games, by 9.3 points.** Two faults compound:

**1. `points_per_game` on n=1 is an anecdote, not a rate.** Affengruber's 8.0 is one haul divided by one game,
and it drives the cold-start blend.

**2. His expected minutes are 1.00** — the most optimistic value available — on a record of one start in two.
Konsa, who has actually started the last two, sits at 0.88.

#### The shape of it, measured

| cold-start · xMins **1.0** · ≤1 full appearance | count |
|---|---|
| projecting **12+ xP** over 5 GWs | **1** (Affengruber, 22.4) |
| projecting 8–12 | 15 |
| projecting under 8 | 108 |
| **total** | **124** |

⚠️ **The mechanism is broad and the damage is rare.** 124 players are modelled as nailed 90-minute starters on
no evidence; 108 of them project low enough to never surface. It bites only when one of them hauls once, because
`points_per_game` then leaps. Affengruber is the one that did — and he landed in the **headline
recommendation** on a real squad.

Worth seeing the floor it implies: **Gboho projects 10.6 xP over five gameweeks having never played a
minute** — zero appearances, zero minutes, 0.0 points per game. The blend leans on `ep_next`, and expected
minutes of 1.0 carries it the rest of the way.

---

### 🎯 The finding

> **`no opinion` is implemented as the most optimistic opinion available.**

ADR-173 rejected *"lower the bar to played in at least one gameweek"* with: **"that is the crater case. One
appearance says nothing about the next."** It was right, and it refused to **promote** such players into the
trusted set.

But it never **demoted** them — because the default was already **1.0** (ADR-104, *"1.0 at zero evidence"*).
So ADR-173's own principle, *"full weight where there is no doubt, no opinion where there is"*, has **both
branches landing on the same number**. The sentence describes two treatments; the code has one.

⭐ **Uncertainty should discount, not inflate.** That is the whole of this ADR; everything below is how far.

---

### 💡 Options Considered

#### Option 1: Discount expected minutes by the evidence behind them *(Chosen in direction)*
Scale the zero/low-evidence end down instead of leaving it at 1.0 — a player with one appearance in four
gameweeks is not a nailed starter, and the model should say so. **The shape is agreed here; the constant is
not** — see below.

#### Option 2: Cap the cold-start *rate* instead
Attacks fault 1 (ppg on n=1) and leaves fault 2 standing, so a no-minutes player still projects on full
minutes. Rejected as a whole answer, though a rate cap may fall out of the same measurement.

#### Option 3: Exclude cold-start players from recommendations entirely
Rejected. It would have hidden Affengruber, and it would also hide a genuine new signing who *is* nailed —
the January arrival and the academy cameo are indistinguishable to this rule. ⭐ *A filter that removes the
false positives by removing the category is not a model, it is an abstention.*

#### Option 4: Keep deferring
Rejected, and the reason has changed since ADR-173. That deferral was justified on sample size *and no known
harm*. There are now **four gameweeks** and **four sightings** of this family — ADR-172 (the rate half),
ADR-173 (the minutes half, unambiguous cases only), ADR-185's A/B (*"2 weak, non-playing forwards"* in a Lab
build), and this one, in a headline recommendation the owner acted on. ⭐ *A deferral survives on the absence
of harm, and that absence has now expired.*

---

### ⚖️ Consequences & Trade-offs

* **Positive:** removes the only class of player that can outrank seven seasons of evidence on one cameo, and
  closes a crater the trail has been circling for three ADRs.
* **Negative:** a genuinely nailed new signing will be under-rated for a few gameweeks. That is the correct
  direction to be wrong in — ⭐ *a missed buy costs a transfer; a phantom buy costs a transfer and a squad
  slot.*
* **Risks & Mitigations:**
  - **Risk:** over-correcting into ADR-172's failure, where no history read as *never plays* and zeroed seven
    players who had played every game. **Mitigation:** discount, never zero — and ADR-172's guards stay.
  - **Risk:** the constant is picked to fix Affengruber. **Mitigation:** it is **not picked here**. It goes
    through §B0's harness like every other weight, on the whole board and on the affected sub-population
    (ADR-190's Option 3, which is now a method this repo has used).

---

### 🛠 Implementation & Migration
* **Components Affected:** `analytics/xp.py` (the cold-start branch), `analytics/minutes.py`, Docs
* **Action Items:**
  - [ ] Measure: sweep the low-evidence minutes discount, scored **whole-board and on cold-start players
        alone** — a term scoped to 124 of 657 is exactly what ADR-190 says a whole-board metric cannot see
  - [ ] Choose the constant from that sweep, pre-registering the expectation first (§B0)
  - [ ] Guards: a one-appearance player must not outproject an established regular **on the same price and
        fixtures**; a zero-minute player must not project a positive floor; ADR-172's no-history guards stay green
  - [ ] Mutation-test every guard
  - [ ] Re-run the Konsa/Affengruber case and record the new numbers in this ADR, either way

#### ✅ Always
- [ ] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

---

### 💡 The lesson

> **A default is an opinion, and the safest-looking default is usually the most confident one.**

Nobody chose to rate Affengruber as a nailed starter. `1.0` was the value that meant *"we have nothing to say
about this player's minutes"*, and on a multiplier, saying nothing is saying **full confidence**. The neutral
value of a scaling factor is not neutral — it is the maximum.

That is why this survived three ADRs that were all looking straight at it. ADR-104 chose 1.0 deliberately and
correctly *for the case it was solving*. ADR-172 fixed the rate. ADR-173 named this exact crater, refused to
make it worse, and left the default alone — because the default looked like an absence rather than a claim.

⭐ **The generalisable form: when a model expresses "unknown" as a number, check which direction that number
points.** Ours pointed up, on a multiplier, for four hundred players a season.

---

### 🔗 References & Related Artifacts
- **The crater, named and left:** [ADR-173](./ADR-173-minutes-you-have-actually-played.md) — *"that is the
  crater case. One appearance says nothing about the next."*
- **The default it inherited:** [ADR-104](./ADR-104-cold-start-xp-floor.md) — 1.0 at zero evidence
- **The same error inverted:** [ADR-172](./ADR-172-a-shrink-needs-something-to-shrink-toward.md)
- **The A/B sighting:** [ADR-185](./ADR-185-price-the-rebuild.md) — *"2 weak, non-playing forwards"*
- **How to score it:** [ADR-190](./ADR-190-the-gw4-sitting.md) Option 3 · `GW1_RUNBOOK` §B0
- **Found by:** the owner, on his own squad, for the fourth time in this family
