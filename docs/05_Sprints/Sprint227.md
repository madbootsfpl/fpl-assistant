# Sprint 227: Five boards become one shortlist (ADR-167)

**Dates:** 2026-08-29
**Status:** ✅ Complete — ADR-167. 1569 → 1581 tests, ruff clean. Players: 10 views → 6.

> **Owner:** *"I see a similar table in each tab, I am getting weary as I tab through… could we merge these
> together and then call out a recommendation rather than just showing multiple tables of fact which none
> will use."*

---

### 🔧 What shipped

**Set pieces · Over/under · DefCon · Clean sheets · xG·xA** became one **Scout** view with a board selector,
under a shortlist of the players **two or more of those boards agree on**, each with its evidence attached.

Measuring first made the case stronger than the complaint did:

```
Over/under · DefCon · Clean sheets → need 900 minutes; most played this season = 180
SET_PIECE_WEIGHT / DEFCON_MAGNIFIER_WEIGHT → 0.0 (dormant until GW4-6)
```

Three of the five were showing **last season** and will until ~GW10, about signals xP deliberately ignores.

Live today: 8 players, mostly low-owned — *Mateta (CRY FWD, £6.5m, 5.1% owned) — first-choice penalties · 14
pts below expected, due a bounce (2025/26)*.

**The constraint that shaped it:** "worth a look", never "worth points". No score, no rank; ordering is by how
many boards agree, never by any of the numbers. Every last-season reason carries its vintage. An
over-performer never qualifies — that is a regression *warning*, and counting it as a positive would invert
the signal on the way in.

**Players is 10 views → 6**, which is the merge its own ceiling note demanded — and the room that unblocks
moving Trending here (US-438).

---

### 💡 The lesson

> **"None will use" was the useful half of the complaint.**

Every one of those tables was correct, captioned and deliberately built. What they were not is *actionable* —
and five correct tables nobody reads are worth less than one sentence naming three players and why. The app
had been publishing evidence and leaving the inference to the reader.

> **But the honest step up from a fact is not always a recommendation.**

Two of these signals are ones the engine has explicitly refused to price. Turning them into "buy this player"
would have been a confident answer built on numbers we had already decided not to trust — a second opinion
beside the one number the whole app decides through. *"Worth a look, and here is why"* is the strongest claim
the evidence supports, and saying exactly that much is the difference between a useful feature and an
authoritative-looking one.

### 🧪 Tests

**+12.** One signal is not a reason; two carry their evidence; last-season reasons are dated and the current
one is not; an over-performer never qualifies; ordering is by agreement, not by a stat; the duty signal
survives an empty early season; the note never says *buy*; an empty shortlist is an answer; safe on an empty
pool. Plus the view, and **a test that fails the moment either weight is turned on** — because this page's
copy would then be wrong.
