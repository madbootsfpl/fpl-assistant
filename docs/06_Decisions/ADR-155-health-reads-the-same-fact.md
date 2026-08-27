# Architectural Decision Record: Health reads the same departure fact as everything else

**Decision ID:** ADR-155
**Date:** 2026-08-27
**Status:** ✅ **Accepted — owner-reported, built** (Sprint 210, 2026-08-27). **1466 → 1476 tests, ruff clean.**
**Superseded By / Replaces:** Completes ADR-153/154 by reaching the **fifth** surface. **No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner checked the window-gated build on Cloud and found the hole:

> Works well on AI Tips and in Risk Monitor. Where it does **not** show is **Health**.

```
Squad value : £100.0m   Availability issues: 1
Bench: 1  Watkins  AVL  FWD  7.9  4.3  …
Availability : Gibbs-White.
```

A squad holding a player with an agreed move to Al-Hilal, described as having **one** availability issue —
and it isn't him. Health said so because it asks FPL's `status` field, which still reads `a`.

**This is the third time the same fact has had to be taught to another surface.** ADR-153's own stated lesson
was *"when you add a new fact to the system, list every decision that would change if it were true"*. That
list had two entries (the flag, the transfer); ADR-154 added two more (the lineup, the captain); Health is a
fifth. The lesson was written down and then under-applied twice in a row, which says the problem is not
memory — it is that **each surface was free to derive the fact for itself, so "teach the app" meant "find
every place that asks".**

---

### ✅ Decision

**1. One implementation of the question.** `headlines.leavers(owned, store_events, exodus_for, today=…)`
returns `{id: event}` for a whole squad, and `Storage.headline_events_by_id()` returns the grouping every
caller was writing by hand. Four copies of the same three-line loop existed — in `ask`, `cli`, the Risk
Monitor and Signals — which is three chances to disagree about a table they all read. Now there is one.

**2. `analyse_squad` takes `reported_out`.** A reported leaver becomes an **availability issue**, because an
availability count that misses the most consequential unavailability on the page is worse than no count. The
event rides on the summary (`"leaving"`), so every consumer inherits it instead of learning separately.

**3. …but his xP is untouched.** Deliberately unlike the gameweek plan, which zeroes him. **Health describes
the squad you have; the plan recommends the one you should field.** Until you transfer him he is in your
squad, and the totals should say so. What changes is that the description stops implying he will play.

**4. The captain lead does obey ADR-154** — it is a recommendation, so it never names a departing player.
`weakest` deliberately does *not* filter: a leaver belongs in the transfer conversation, not out of it.

**5. The window gate comes for free.** `leavers` delegates to `reported_leaving`, where ADR-154's gate already
lives, so Health cannot start flagging an October rumour that AI Tips is deliberately silent about.

**What the reader sees** — the outlet, not the headline. `event_tag` is `event_phrase` shortened, because the
full quote is right where there is room to read it and buries the other five names in a list:

```
  Squad value : £100.0m   Availability issues: 2
  9  Watkins (out)   AVL  FWD  7.9  4.3 …
  Availability : Gibbs-White, Watkins (leaving — Romano).
```

On the web table the same fact reads **✈️ leaving** in Trends, with the outlet named in the analysis below.

### 🧪 Definition of Done

1. **Tests: +10.** The issue appears though `status == "a"`; a fit squad still has none and the argument stays
   optional; the captain lead skips a leaver; **his xP survives** (the deliberate difference from the plan);
   the render names the outlet and marks the row; `leavers` answers for a squad and inherits the window gate;
   `event_tag` is shorter than `event_phrase`; the storage grouping, including on a snapshot predating the
   table; and a headless Health render that asserts the view actually asks — the stub must be called.
2. **Manual smoke** — the live squad on the CLI, shown above: 1 → 2 issues, Watkins named with his outlet.
3. **Docs** — this ADR, PROJECT_STATUS, the sprint retro.

---

### 💡 The lesson

**A fact that each surface derives for itself will be known by some of them.** Three ADRs in a row ended with
a version of *"remember to update the other places"*, and the count went 2 → 4 → 5 anyway. Enumerating
consumers is a task you have to get right every time; giving the fact **one owner and one shape** is a task
you get right once. The fix here was not adding Health to a list — it was deleting the four hand-written
copies of the question so there is nowhere left for a surface to disagree.

The corollary, and the reason this ADR isn't just a merge: **the surfaces should share the fact, not the
reaction.** Health, the plan and the transfer engine now read identical data and still do three different
things with it — describe, exclude, replace. Sharing the reaction would have zeroed a player's xP on a page
whose whole job is to tell you what you own.
