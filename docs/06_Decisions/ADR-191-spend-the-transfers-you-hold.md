# Architectural Decision Record: Spend the transfers you hold

**Decision ID:** ADR-191
**Date:** 2026-09-14
**Status:** 📋 **Proposed** — gate before building. **Three gaps, deliberately split**, because their evidence
is at very different strengths: §1 is measured and certain, §2 is measured and ambiguous, §3 is unmeasured.
**Superseded By / Replaces:** Extends [ADR-186](./ADR-186-bank-to-afford.md)'s affordability cliff and
[ADR-173](./ADR-173-minutes-you-have-actually-played.md)'s week-plan answer. **Does not reopen [ADR-187](./ADR-187-reopen-multi-gameweek-planning.md)**
— that measured planning *across gameweeks*; this is about the transfers you hold *this* gameweek. **No
`decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner, on an ADR-186 line reading *"Worth saving for: £1.0m more makes this M.Sangaré → Rayan (+12.2 XI xP
over 5 GWs, +3.3 on the move above)"*:

> *"Note that I have £1.0m in the bank, I have 2 free transfers for the next gameweek, so is this advice the
> best or most effective? … Should we not be triangulating number of available transfers, spending the money
> on the starting 11, looking at budget and then making a decision? Maybe a Grosz plus Palmer or Rogers. Or is
> Haaland a better option than Bruno and figure the moves needed to select him."*

#### The half of the worry that is unfounded, checked first

*"Bringing Rayan in provides a good 12th man"* — **it does not, and the app already prevents that.**
`suggest_transfers` runs `xi_aware=True`, so a move's gain **is** the lift to the best legal XI (ADR-046): a
buy who would sit on the bench scores +0.0 and never surfaces. Across 60 squad-runs the recommended buy made
the XI **60 out of 60 times**. The money does go into the starting eleven.

Worth saying because it changes where to look: the fault is not *which* player is recommended. It is **how
many**.

#### The measurement

`spikes/191-two-transfers/`. Three strategies, same squad, same bank (£1.0m), same 5-GW xP map, each scored
as the lift to the best legal XI:

* **A** — the single best move: what the app recommends today.
* **B** — A, then the best move from the *resulting* squad with the *remaining* money: following the app twice.
* **C** — the best **pair**, chosen together, sharing one budget.

| | 30 random squads (seed 5 / 11) | RoboTS | TS |
|---|---|---|---|
| **A** one move | +21.7 / +22.2 | +7.9 | +12.6 |
| **B** two moves, greedy | +40.1 / +40.6 | +12.4 | +22.6 |
| **C** two moves, planned | +40.6 / +40.9 | **+18.3** | +22.6 |
| *value of the 2nd transfer* | **+18.5 / +18.4** | +4.5 | +10.0 |
| *value of planning the pair* | +0.4 / +0.3 | **+5.9** | +0.0 |

**The second transfer is worth roughly as much again as the first.** And the app already computes it:
`gameweek.py` asks `suggest_transfers` for **two** moves, shows one, and uses the second only to answer
*"bank or use"* (ADR-173). The number is calculated, spent on a side-question, and never reaches the
recommendation.

#### Three distinct faults, not one

**1. The app does not know how many free transfers you hold.** There is a *"Free transfers you hold"*
`number_input` on the Transfer tab, default 1, and it feeds `bank_or_use` and nothing else. It does not change
how many moves are recommended, and it never reaches the week's answer at all.

**2. The cliff's "wait" is never weighed against "use your second transfer now".** ADR-186 asks *"is a better
player one price-rise away?"*; the second transfer asks *"is there another move worth making today?"* Both are
computed, **neither is compared to the other**, and the reader is handed the one that happens to render. On
the owner's squad, *"save £1.0m for +3.3"* is very probably dominated by a second transfer worth +4.5 to +10.0
— not wrong, just never put beside the thing that beats it.

**3. The shortlist is a menu, not a plan — and its gains do not add.** Both moves are priced against the
**same** starting squad and the **same** bank (`transfer.py`: `base_xi` and `budget = out["price"] + bank`,
computed once). They are disjoint *alternatives*, which is correct for a shortlist and wrong for a plan.
Printing *"+12.2 and +8.1"* would overstate what a manager actually gets, because the second move's real value
is its margin over the squad and the money the first one leaves.

#### And the owner's own example names a fourth thing

RoboTS shows the mechanism exactly. Greedy opens **Hume → Ballard** (+7.9). The best pair is **Mukiele →
Ballard + Watkins → Isak** (+18.3) — *the same incoming player, routed through a different sale*, because that
is the sale that leaves enough money for the second move. **Greedy spent Ballard on the wrong outgoing player
and blocked the better combination.**

Which is precisely *"is Haaland a better option than Bruno, and figure the moves needed to select him"*: a
**target-driven** question — start from the player you want and solve for the route — rather than the
squad-driven one the app asks. Nothing in the codebase answers it.

---

### 💡 Options Considered

#### Option 1: Recommend as many moves as the manager holds transfers, priced sequentially *(Chosen for §1)*
Use the free-transfer count we already collect, and return *N* moves where each is priced against the squad
and bank the previous one leaves. Fold the affordability cliff into the same comparison so *"save £1.0m"* must
beat *"use your second transfer"* rather than appearing beside it.

Cheap — mostly wiring plus an honest re-pricing loop — and the measurement says the number is large and
consistent. **This is the one to build.**

#### Option 2: Search the best *pair* jointly *(Gated)*
Measured, and the evidence is genuinely ambiguous: **+0.4 mean** across random squads (8/30 saw any gap, max
+3.4) against **+5.9** on RoboTS. Random squads have so much headroom that almost any two moves gain a lot, so
the *order* matters less — I believe they understate this, and believing is not measuring. **n=2 real squads
is a hint, not evidence.** Wants its own measurement on realistic squads before it justifies a search.

#### Option 3: Target-driven planning — *"what would it take to field Haaland?"* *(Gated)*
A new query shape, and the one that matches how the owner actually thinks. Also the one with no measurement at
all behind it yet. Named here so it does not get folded into Option 1's build and shipped unmeasured.

#### Option 4: Do nothing, on the grounds that ADR-187 closed multi-transfer planning
**Wrong, and worth recording so it is not raised again.** ADR-187 measured planning **across gameweeks** — one
transfer per gameweek, money carried, foresight worth +4%. This is a different question: **two transfers in
the same gameweek, both free, sharing one budget.** The first is about *when*; this is about *how many*.
⭐ Reusing a decline because the words overlap is how a measured "no" becomes an unexamined one.

---

### 🎯 Decision & Justification

**Build §1. Gate §2 and §3.**

1. **`week_plan` takes the free-transfer count and recommends that many moves**, each priced against what the
   previous one leaves — never a menu presented as a plan.
2. **The cliff competes rather than coexists.** *"Worth saving for"* renders only when its uplift beats the
   marginal gain of the next transfer the manager could make today.
3. **A move's stated gain is always its true marginal gain** in the sequence it is shown in. If two numbers
   appear, adding them must give the total.
4. **§2 and §3 are recorded with what would unblock them**, not deferred vaguely: §2 needs the pair
   measurement re-run on realistic squads (optimiser-built or imported, not random); §3 needs a design.

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:** the single largest gap between what the engine computes and what the reader is told —
  a number already in memory, discarded. The week's answer starts matching the manager's actual position
  (transfers held, money held) rather than a default of one.
* **Negative Impact / Trade-offs:** more moves means more screen and more ways to be wrong; a two-move
  recommendation that is half-right is harder to reject than a one-move one. And sequential pricing is
  strictly more computation on a page that is already solver-heavy.
* **Risks & Mitigations:**
  - **Risk:** the free-transfer count is **manager-entered**, so a wrong entry produces confident wrong
    advice. **Mitigation:** default 1 (today's behaviour), and the recommendation says how many transfers it
    assumes — a stated assumption is refutable, a silent one is not.
  - **Risk:** recommending two moves encourages churn against ADR-132's finding that the *gain* moves and the
    *decision* usually does not. **Mitigation:** the second move must clear the same positive-gain bar as the
    first; holding a transfer stays a legitimate output.
  - **Risk:** greedy sequencing is still not optimal (RoboTS +5.9). **Mitigation:** that is exactly §2, gated
    and named, so shipping §1 does not quietly claim to have solved it.

---

### 🛠 Implementation & Migration
* **Components Affected:** `analytics/gameweek.py`, `analytics/transfer.py` (sequential pricing),
  `analytics/transfer_timing.py` (the cliff comparison), `ui/gameweek.py`, `web_streamlit` squad views, Docs
* **Action Items (§1):**
  - [ ] `week_plan` recommends `free` moves, each priced against the squad + bank the previous one leaves
  - [ ] The affordability cliff renders only when it beats the next available transfer's marginal gain
  - [ ] The recommendation states how many free transfers it assumed
  - [ ] Guards: two moves' stated gains **sum to the stated total**; a second move is priced on the
        post-first squad (mutate the base and watch it fail); `free=1` reproduces today's answer byte-identically
  - [ ] Mutation-test every guard
* **Action Items (gated):**
  - [ ] **§2** re-measure joint pairs on realistic squads before building any search
  - [ ] **§3** design target-driven planning (*"what would it take to field X?"*)

#### ✅ Always
- [ ] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

---

### 💡 The lesson

> **A number computed for one question and discarded is invisible in a way a missing number is not.**

The second-best transfer has been in memory on every render since ADR-173. It was fetched deliberately, used
honestly to answer *"bank or use"*, and then dropped — and because the code plainly *does* ask for two moves,
nothing about reading `gameweek.py` suggests a gap. A feature that was never built leaves a hole someone
notices. A value that is computed and thrown away leaves a comment explaining why two were requested.

The narrower one, which ADR-186 nearly taught already: **two features that answer competing questions must be
made to compete.** *"Save your money"* and *"use your second transfer"* are both correct, and presenting the
one that happens to render is presenting an arbitrary choice as a recommendation. ADR-186 asked *"bank the
money?"* next to ADR-132's *"bank the transfer?"* and the pair was never wired to argue.

And the one the owner keeps supplying: **he found this by holding two free transfers and reading advice that
assumed one.** The gap between what a system knows about you and what it assumes about you is invisible from
inside the system — the same shape as ADR-188, four ADRs later.

---

### 🔗 References & Related Artifacts
- **The measurement:** `spikes/191-two-transfers/` (`measure.py`, `result-2026-09-14.txt`)
- **What it extends:** [ADR-186](./ADR-186-bank-to-afford.md) (the cliff) · [ADR-173](./ADR-173-minutes-you-have-actually-played.md)
  (where the week's answer gained `bank_or_use` — and with it the second move it has been
  discarding ever since) · ADR-046 (XI-aware transfer gain) · ADR-030/040
- **What it does NOT reopen:** [ADR-187](./ADR-187-reopen-multi-gameweek-planning.md) — planning *across*
  gameweeks, measured and closed. This is *within* one.
- **Found by:** the owner's two-team A/B, reading a recommendation against his actual bank and transfer count
