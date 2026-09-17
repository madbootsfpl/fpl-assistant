# Architectural Decision Record: "What would it take to field X?"

**Decision ID:** ADR-207
**Date:** 2026-09-17
**Status:** ✅ **Accepted — built. Closes [ADR-191](./ADR-191-spend-the-transfers-you-hold.md) §3.**
**1857 → 1867 tests, ruff clean. 7 mutants, all red.**
**Superseded By / Replaces:** Builds ADR-191's Option 3, gated there as *"a new query shape… the one with no
measurement at all behind it yet."* **No `decision_xp` change** — same xP, asked a different question.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The app answers a **squad-driven** question: *for each player I own, what is the best replacement?* The owner
kept asking a **target-driven** one — twice, unprompted, three days apart:

> *"Or is Haaland a better option than Bruno and figure the moves needed to select him."* (2026-09-14)
>
> *"I would use my transfers to see if I can get another forward in that is scoring rather than replacing with
> Havertz."* (2026-09-17)

⭐ **In this project a repeated unprompted request has been a reliable signal.** The reported-departure fact
needed teaching on six separate surfaces (ADR-151→156), every one found by the owner using the product.

Nothing in the codebase answered it. `suggest_transfers` iterates the **outgoing** players and finds each one's
best replacement, so a *named* incoming player can only appear by luck — and the shortlist is deliberately
disjoint (ADR-040), so if he shows up against one sale he is removed from consideration against the others.

---

### 🎯 Decision

**`route_to_player(target, owned, xp_by_id, bank=…)` — fix the incoming player, search the route.**

FPL transfers are one-for-one and same-position, so the candidates are your players in the target's position.
They differ in two ways that both matter: **what they were contributing**, and **what selling them leaves in
the bank**.

**Three design decisions, each one a refusal to do the obvious thing:**

**1. Ranked by the effect on the starting XI, never by which sale frees the most money.** The obvious
implementation sells whoever can afford him. ADR-191 §2 measured the cost of getting this wrong from the other
direction: on a real squad the best pair routed **the same incoming player through a different sale**, because
that was the sale that left enough for a second move.

**2. A blocked route is reported, not dropped.** ⭐ *A blocked route is information, not an absence.* On the
test squad, *"sell Isak's way in by selling João Pedro — short by £0.6m"* is exactly ADR-186's **worth saving
for**. Printing only what cleared tells the reader about one option and silently hides the near-misses.

**3. Negative routes are returned, least-bad first, and never suppressed.** ⭐⭐ **A TARGET-DRIVEN QUESTION IS
ONE THE READER HAS ALREADY HALF-ANSWERED — THE JOB IS TO PRICE THE WISH, NOT TO GRANT OR REFUSE IT.**
Suppressing them would answer a question nobody asked (*"is this wise?"*) instead of the one they did
(*"what would it take?"*). When every route loses points the CLI says so in as many words: *"you can field
him, and this is the price."* Same posture as ADR-194's handing the lineup call back, in a new place.

---

### 📊 Verified on a real squad before building

Run against a template squad off the live cache (ADR-200's `population.py`, built for exactly this):

```
▸ Isak (£9.1m, LIV, xP 30.7 over 5 GWs)
    sell Haaland        £15.5  →  gains  1.7 XI xP · £7.1m left
    ✗    João Pedro     £7.8   —  short by £0.6m
    ✗    Calvert-Lewin  £6.0   —  short by £2.4m

▸ Emersonn (£5.5m, IPS, xP 10.1)
    sell Calvert-Lewin  £6.0   →  costs  3.3 XI xP · £1.2m left
    sell João Pedro     £7.8   →  costs 16.5 XI xP
    sell Haaland        £15.5  →  costs 18.8 XI xP
    Every route costs you points. That is the answer to the question, not a refusal.
```

⭐ **The Isak line is the case for the feature.** One route clears, two are near-misses, and the near-miss is
**£0.6m** — a number the squad-driven view would never have surfaced, because it never asks about Isak at all.

**The blocked-route reporting was added because of this run**, not designed in: the first version printed only
the Haaland route and the £0.6m was invisible. ⭐ *Verifying a design on real data is how you find the output
you did not know you wanted.*

---

### ⚠️ Scope, stated rather than discovered later

- **One transfer.** *"What would it take"* has a two-transfer answer too — sell two, buy the target plus a
  cheaper filler — and that overlaps **ADR-191 §2**, which is still gated on its own measurement. The
  shortfall answers the money form of the question (*"£0.6m more"*) without pretending to search pairs.
- **CLI only** (`python app.py route "Isak" --squad RoboTS --bank 1.2`). ⭐ *Testing a component is not testing
  that anything uses it* — every guard here passed while the function had no caller at all, so the wiring is
  pinned by its own test. A web surface is a separate decision about where the question belongs.
- A player **reported to be leaving** is valued at zero when ranking routes (ADR-153/156), so selling him
  correctly looks attractive — the same `_selection_xp` the shortlist uses.

---

### 📊 Consequences

**Good:** the shape the owner actually thinks in is now answerable, and it composes with what exists — same
`decision_xp`, same `best_xi_points`, same club and position rules.

**Costs / limits:**
- ⚠️ It prices the route **as things stand today**, with today's flags and today's prices. A route that clears
  by £0.1m does not clear after a price change.
- The XI effect is measured over the chosen horizon, so a target with a good next fixture and a bad run reads
  differently at `--next 1` and `--next 5`. That is correct and it is also a way to be misled by your own
  question.
- No two-transfer search, above.

---

### 🔗 Links

- [ADR-191](./ADR-191-spend-the-transfers-you-hold.md) §3 — the gate this closes; §2 still open
- [ADR-186](./ADR-186-bank-to-afford.md) — the affordability cliff the blocked routes reuse
- [ADR-194](./ADR-194-a-start-bench-call-gets-a-margin.md) — pricing rather than instructing
- `src/analytics/transfer.py` · `src/cli.py` · `tests/test_route_to_player.py` · `spikes/207-target-driven/`
