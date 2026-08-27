# Sprint 210: Health reads the same departure fact as everything else (ADR-155)

**Dates:** 2026-08-27
**Status:** ✅ Complete — ADR-155. 1466 → 1476 tests, ruff clean.

> **Owner:** *"Works well on AI Tips and in Risk Monitor. Where it does **not** show is **Health**."*

---

### 🔧 What shipped

Health was describing a squad with an agreed transfer to Al-Hilal in it as having **one** availability issue —
and it wasn't him. It asked FPL's `status`, which still reads `a`.

Now `analyse_squad` takes `reported_out`, so a reported leaver is an availability issue, his row reads
`Watkins (out)` (**✈️ leaving** on the web), and the line beneath names the outlet:

```
  Squad value : £100.0m   Availability issues: 2
  Availability : Gibbs-White, Watkins (leaving — Romano).
```

**His xP is untouched, on purpose.** The gameweek plan zeroes him because it *recommends* an XI; Health
*describes* the squad you own, and until you transfer him he is in it. The captain lead does skip him — that
line is a recommendation.

The window gate came for free: `leavers` delegates to `reported_leaving`, where ADR-154's check already lives,
so Health can't flag an October rumour that AI Tips is deliberately quiet about.

---

### 🧹 What actually caused this

Four surfaces had each hand-written the same three-line loop to group `headline_events` by player. So "teach
the app about departures" meant "find every place that asks" — and that search came up short three sprints
running: **2 consumers, then 4, then 5.**

Replaced with one `Storage.headline_events_by_id()` and one `headlines.leavers()`. Four copies deleted.

---

### 💡 The lesson

> **A fact that each surface derives for itself will be known by some of them.**

ADR-153 ended with *"list every decision that would change if this were true"*. I wrote that lesson, then
under-applied it twice. That says the problem isn't memory — enumerating consumers is a task you have to get
right *every time*, whereas giving the fact one owner and one shape is a task you get right *once*.

The corollary, and why this wasn't just a merge: **share the fact, not the reaction.** Health, the plan and
the transfer engine now read identical data and still do three different things with it — describe, exclude,
replace. Sharing the reaction would have zeroed a player's xP on the one page whose job is to say what you own.

### 🧪 Tests

**+10.** The issue appears though `status == "a"`; a fit squad still has none and the argument stays optional;
the captain lead skips a leaver; **his xP survives** (the deliberate difference from the plan); the render
names the outlet and marks the row; `leavers` answers for a whole squad and inherits the window gate;
`event_tag` is shorter than `event_phrase`; the storage grouping, including on a snapshot predating the table;
and a headless Health render that asserts the view actually *asks* — the stub must be called, or the test fails.
