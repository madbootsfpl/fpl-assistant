# ADR-225 — A plan that knows when it stopped being true

**Date:** 2026-09-22
**Status:** Accepted
**Builds on:** ADR-222 (the pitch), ADR-223 (the tabs)

---

## Context

The app could read a squad and rank transfers, and tapping a suggestion did nothing. Asked whether a
modified squad should survive closing the app, the owner was unambiguous:

> *"It needs too."*

That settles persistence. It also makes the harder question visible, which is **not** where to store a
squad — it is *what happens when the stored one and the real one disagree*.

⭐⭐ **A saved plan can become a lie while the app is shut.** You plan a transfer on Friday, make it for
real in the FPL app on Saturday, and reopen this on Sunday. A stored list of fifteen players would be shown
as *your team*, and a manager would act on it — the one failure here with a cost attached, because the
action it invites spends a transfer.

---

## Decision

### 1. Store what changed, not what you ended up with

A draft records the **squad it was made against** alongside the squad it produces:

```
{ manager_id, gameweek, base_player_ids, player_ids, bench_ids, saved_at }
```

⭐ **`base_player_ids` is the whole design.** A snapshot cannot tell you whether it is still relevant; a
draft that remembers its starting point can be checked against reality the moment the app reopens. The
swaps are then *derived* — two lists and a subtraction cannot disagree with each other, where a stored list
of swaps could drift from the squad it claims to describe.

### 2. Reality is fetched first, always

The real team is loaded, then the draft is checked against it. A draft is an **overlay on reality, never a
substitute for it**, and four outcomes get four different sentences:

| verdict | what it usually means | what the app says |
|---|---|---|
| `fresh` | nothing moved | restores the plan |
| `squadChanged` | ⭐ **you already made the move** | *"looks like you made the move. Plan cleared."* |
| `gameweekPassed` | the week was played | *"was for a gameweek that has been played"* |
| `otherManager` | a different id is loaded | *"belonged to a different manager id"* |

⚠️ **Dropped *and* reported.** Silently discarding a manager's plan is its own kind of lie, and *"your plan
is gone"* and *"your plan already happened"* mean opposite things.

⚠️ **Compared as sets, not as lists.** FPL returns picks in its own order, and that order moves when a
manager reorders the bench — which is not a squad change, and treating it as one would throw away a
perfectly good plan for no reason.

### 3. The server says whether this is the real team

`my-team` gained `draft_player_ids`, and every response now carries **`draft: bool`** and
**`fpl_player_ids`**.

⭐ **A client can forget to mention it; a field cannot.** And `fpl_player_ids` is what lets a saved plan
check itself against reality rather than trusting that nothing moved.

⚠️ **The draft replaces the fifteen and nothing else.** Name, bank, deadline and armbands still come from
FPL — *a draft that invented its own bank would let a manager plan a move he cannot pay for*, and one that
invented its own deadline would price the wrong gameweek. Kits and fixtures are derived from the squad
being **shown**, so a drafted-in player from a new club is not left shirtless.

### 4. `shared_preferences`, not Drift

⭐ **Storage was added the moment something needed it, and no earlier.** The audit's Phase 4 lists a Drift
cache; this is one small document, and a SQLite ORM with code generation is machinery for a relational
cache that does not exist. **Drift arrives when the board is cached for offline use** — a real trigger
rather than a plan.

---

## ⚠️ What a tap can honestly do

**Nothing in this app can change your FPL team.** FPL publishes no write API; the only route is
authenticating as the manager, which would mean holding his credentials.

⭐ **The web app is already honest about this** — `apply_transfer`'s docstring says *"No server write"*, and
its button changes a local session squad. The phone does the same thing: tapping a suggestion shows you
**your pitch with that move**, and an orange banner says *"A plan — not your FPL team. Make it for real in
the FPL app."*

⚠️ The banner is permanent while a draft is live and carries the way out. A plan shown as a squad is a lie
about something you can act on, so the label cannot be dismissible.

### One rule that is easy to get wrong

**A second swap is built from FPL's squad, never from what is on screen.** Compounding plans onto an
already-drafted squad would lose the thread back to reality — and the draft could then no longer tell
whether it was stale. **One base, one set of changes.**

---

## Verification

* **8/8 mutations killed**, including *the draft flag always says "real team"*, *kits derived from the FPL
  squad rather than the shown one*, and *a draft invents its own bank*.
* **10 Dart tests** on the staleness logic alone — including that reordering a bench is **not** a squad
  change, that an absent gameweek does not invalidate a plan (⭐ *absent is not "different"*), and that a
  same-sized squad with one player swapped is still caught.
* A draft of fourteen is refused: it analyses perfectly well and simply projects less — ⭐ *a wrong answer
  wearing the shape of a right one*, which is the check this codebase keeps having to add.

## Consequences

**Good:** a plan survives closing the app, and cannot outlive its truth. The *what if* the FPL app will not
give you is now one tap away.

**Costs:** ⚠️ the app now holds state that can be wrong, which it did not before. Every guard above exists
because of that, and the cost of a bug here is a manager spending a transfer on stale advice.

**Open:** manual transfers — tap a player on the pitch, choose from affordable same-position replacements —
use this same mechanism and are not yet built. Captain and subs write to a draft too, and are the next
thing that makes the bottom bar complete.
