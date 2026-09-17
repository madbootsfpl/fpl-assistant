# Sprint 267: "What would it take to field X?"

**Dates:** 2026-09-17
**Status:** ✅ **ADR-207 — 1857 → 1867 tests, ruff clean, 7 mutants all red. Closes ADR-191 §3.**

---

## The ask, twice

> *"Or is Haaland a better option than Bruno and figure the moves needed to select him."* — 2026-09-14
>
> *"I would use my transfers to see if I can get another forward in that is scoring rather than replacing with
> Havertz."* — 2026-09-17

⭐ **In this project a repeated unprompted request has been a reliable signal.** The reported-departure fact
needed teaching on six separate surfaces (ADR-151→156), every one found by the owner using the product.

The app answers a **squad-driven** question — *for each player I own, what is the best replacement?*
`suggest_transfers` iterates the **outgoing** players, so a *named* incoming player can only appear by luck,
and the shortlist is deliberately **disjoint** (ADR-040): showing up against one sale removes him from
consideration against the others.

---

## Built: fix the player, search the route

FPL transfers are one-for-one and same-position, so the candidates are your fifteen in the target's position.
They differ in two ways that both matter: **what they were contributing**, and **what selling them leaves in
the bank**.

**Three design decisions, each a refusal to do the obvious thing:**

1. ⭐ **Ranked by the effect on the starting XI, never by which sale frees the most money.** ADR-191 §2
   measured that failure from the other direction: on a real squad the best pair routed *the same incoming
   player through a different sale*, because that was the sale that left enough for a second move.
2. ⭐ **A blocked route is information, not an absence.** *"Sell João Pedro — short by £0.6m"* is exactly
   ADR-186's **worth saving for**.
3. ⭐⭐ **Negative routes are returned, least-bad first, never suppressed.** **A target-driven question is one
   the reader has already half-answered — the job is to price the wish, not to grant or refuse it.**
   Suppressing them answers *"is this wise?"*, which nobody asked. Same posture as ADR-194 handing the lineup
   call back.

---

## 📊 Verified on a real squad first — and the run changed the design

```
▸ Isak (£9.1m, LIV, xP 30.7 over 5 GWs)
    sell Haaland        £15.5  →  gains  1.7 XI xP · £7.1m left
    ✗    João Pedro     £7.8   —  short by £0.6m
    ✗    Calvert-Lewin  £6.0   —  short by £2.4m
```

**The first version printed only the Haaland route.** The £0.6m near-miss was invisible — and it is the most
actionable line in the output, because the squad-driven view never asks about Isak at all.

⭐ **Verifying a design on real data is how you find the output you did not know you wanted.** Blocked-route
reporting was added because of this run, not designed in.

---

## Scope, stated up front rather than discovered later

- **One transfer.** The two-transfer form overlaps **ADR-191 §2**, still gated on its own measurement. The
  shortfall answers the money form of the question without pretending to search pairs.
- **CLI only** — `python app.py route "Isak" --squad RoboTS --bank 1.2`. A web surface is a separate decision
  about where the question belongs.
- ⭐ **Testing a component is not testing that anything uses it**: all eight function guards passed while
  `route_to_player` had **no caller at all**. The wiring carries its own test.

---

## 💡 The lesson

⭐⭐ **The engine already had every primitive this needed** — `best_xi_points`, `is_unavailable`,
`_selection_xp`, the club and position rules. What was missing was not capability but a **question shape**.
Nothing had to be measured or modelled; the same numbers were simply never asked in this order.

⭐ *When a request keeps coming back, check whether it needs new machinery or only a new way in.*

---

## Definition of Done

- ✅ **Tests** — 10 new (`tests/test_route_to_player.py`), 8 on the function and 2 on the CLI wiring;
  **1867 passed**, ruff clean; 7 mutants, all red
- ✅ **Manual smoke** — end to end through the real CLI on a template squad off the live cache, in a temp
  squad file so nothing of the owner's was touched
- ✅ **Docs** — ADR-207 + index row, ADR-191 §3 ticked, PROJECT_STATUS (including the commands line), this
  sprint doc

**Next:** ADR-191 §2 (joint pairs) is the remaining gate, and it is unblocked — ADR-200 built `population.py`
for exactly that measurement.
