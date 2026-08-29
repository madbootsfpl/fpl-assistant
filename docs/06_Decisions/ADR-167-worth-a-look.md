# Architectural Decision Record: Five boards become one shortlist — "worth a look", not "worth points"

**Decision ID:** ADR-167
**Date:** 2026-08-29
**Status:** ✅ **Accepted — owner's idea, gated in conversation, built** (Sprint 227, 2026-08-29).
**1569 → 1581 tests, ruff clean. Players: 10 views → 6.**
**Superseded By / Replaces:** Performs the merge ADR-134/138's ceiling note demanded, and so **unblocks
US-438** (Trending → Players). **No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner, reading the Players tab:

> *"When I look at the usefulness of Player Data — Set Pieces, Under/Over, DefCon, Clean Sheets & xG/xA, I see
> a similar table in each tab. I am getting weary as I tab through or scroll down. Could we merge these
> together and then call out a recommendation based on the data… rather than just showing multiple tables of
> fact which none will use."*

**Measured before answering, and the data made the case stronger than the complaint did:**

```
Over/under · DefCon · Clean sheets  → require 900 minutes (~10 matches)
most minutes played this season     → 180
players over 450 minutes            → 0 of 620
SET_PIECE_WEIGHT / DEFCON_MAGNIFIER_WEIGHT → 0.0  (dormant, pending GW4-6)
```

So three of the five boards were showing **last season** via ADR-126's fallback and will until ~GW10, and two
of the underlying signals are ones the engine has explicitly decided **not to price**. Five near-identical
tables, mostly of last year, about things xP deliberately ignores.

---

### ✅ Decision

**1. One `Scout` view, five boards behind a selector.** The tables are untouched — same columns, same help,
same caveats. What changed is that they stopped being five destinations. **Players goes 10 views → 6**, which
is the merge the page's own comment demanded before it could accept another view.

**2. The shortlist leads, and its claim is convergence.** `worth_a_look` returns players standing out on
**two or more** boards, each with its evidence attached. That is the one thing a single leaderboard cannot
say, it is cheap, and it is new information.

**3. "Worth a look", never "worth points" — and this is the whole design constraint.** Ranking players on
set-piece duty or DefCon while their weights are `0` would be the app asserting a confidence it has withheld,
and would put a **second opinion beside `decision_xp`** — exactly what ADR-041 exists to prevent. So there is
no score, no rank, and the ordering is by **how many boards agree**, never by any of the numbers, which are
on different scales measuring different things.

**4. Every reason carries its vintage.** *"DefCon +1.4/90 over the bar (2025/26)"*. A last-season fact stated
as a present one is the most misleading kind of true statement, and three of four signals are last season's.

**5. An over-performer is never a reason to look.** Points ahead of the underlying numbers regress — the board
calls that a *warning*, so counting it as a positive would invert the signal on the way into the shortlist.

**Live output today** — 8 players, mostly low-owned, e.g. *Mateta (CRY FWD, £6.5m, 5.1% owned) — first-choice
penalties · 14 pts below expected, due a bounce (2025/26)*.

### 🧪 Definition of Done

1. **Tests: +12.** One signal is not a reason; two carry their evidence; every last-season reason is dated and
   the current one is not; an over-performer never qualifies; ordering is by agreement, not by a stat; the
   duty-based signal survives an empty early season; the note says *not a points projection* and never *buy*;
   an empty shortlist is an answer; safe on an empty pool. Plus the view: the shortlist leads, all five boards
   are reachable, Players is back under its ceiling — **and a test that fails if `SET_PIECE_WEIGHT` or
   `DEFCON_MAGNIFIER_WEIGHT` is ever turned on**, because the copy would then be wrong.
2. **Manual smoke** — a preview built from the live pool.
3. **Docs** — this ADR, the feedback log, PROJECT_STATUS, a sprint retro.

---

### 💡 The lesson

**"None will use" was the useful half of the complaint.** The tables were correct, well-captioned and
carefully built; every one of them shipped as a deliberate feature. What they were not is *actionable* — and
five correct tables that nobody reads are worth less than one sentence naming three players and why. The
weariness was the symptom; the diagnosis was that the app had been publishing evidence and leaving the
inference to the reader.

The counterweight, and the reason this took a conversation rather than a commit: **the honest step up from a
fact is not always a recommendation.** Two of these signals are ones the engine has explicitly refused to
price. Turning them into "buy this player" would have been a confident answer built on numbers we had already
decided we did not trust. *"Worth a look, and here is why"* is the strongest claim the evidence actually
supports — and saying exactly that much is the difference between a useful feature and an authoritative-looking
one.
