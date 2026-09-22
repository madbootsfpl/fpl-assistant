# ADR-222 — The landing screen is a pitch, and it needed an endpoint that did not exist

**Date:** 2026-09-22
**Status:** Accepted
**Builds on:** ADR-219 (the contract), ADR-220 (the six endpoints), ADR-221 (the Dart models)

---

## Context

The mobile app's first screen was a **list**: projected xP, captain, flagged players, then the XI and bench
as rows. It worked, and the owner's reaction on seeing a draft was immediate:

> *"as a landing page on my team i would prefer a pitch layout format"*

— with two references: the Fantasy Football Hub app, and **madboots.streamlit.app itself**, which has drawn a
pitch since ADR-084.

⭐ **The second reference is the decisive one.** The web app already solves this, and it solves it with a
card the owner uses every week. A phone that drew a *different* card would give two surfaces two ways of
describing one squad, and a manager no way to tell which is right.

## Decision

**The landing screen is the web app's pitch, plus a header band.**

The card is what `pitch.py` already draws: kit · name · white xP pill · price · fixture, with the manager's
own **C** and **V**. The header band is the one thing the Hub has that MADBOOTS did not — gameweek,
deadline, predicted points, squad value and flag count, above the fold.

### What was declined, and deliberately

The Hub colours each card by fixture difficulty. Offered as a second variant, and **not taken** —
⚠️ **ADR-179 already declined whole-card colour** on the grounds that it *trades a readable number for a
hue*, on the surface ADR-135 taught this project not to over-density.

⭐ That was a judgement about a laptop, and a phone is a smaller screen where colour does more work, so the
answer could legitimately differ. It stays declined because the owner chose the readable number — but the
point is that it was **re-decided rather than drifted into**. A prior ADR is a fact about a version, not a
law (ADR-180), and the way to overturn one is on purpose.

---

## The finding: the screen could not be drawn from the contract

`analysis` returns eleven fields. The pitch needs **ten things it does not**:

| needed for | missing |
|---|---|
| the header | `gameweek` · `deadline` |
| the armbands | `captain_id` · `vice_captain_id` |
| the shirt | `kit` |
| the card | `opponent` · `venue` · `difficulty` |
| the bench | `bench_role` |

⭐⭐ **The contract was built for questions, and a landing screen needs furniture too.** Every endpoint so
far takes *ids in* and returns *analysis out* — which is right, and which is not a whole screen. Fetching
the rest separately is **five round trips before anything renders**, on the client whose entire architecture
was justified by measuring payload (spike 017: 2.41 MB → 0.81 MB).

So: **`POST /api/v1/squad/my-team`**, which composes `fetch_manager_team`, `analysis`, `team_schedule`,
`bench_order`, `shirt_url` and `deadline_line`. Every one already shipping; nothing here computes football.
**6.5 KB, one call.**

⚠️ **A screen-shaped endpoint is a real cost** — it couples the API to a layout, and a second client wanting
a different arrangement gets a payload built for someone else's screen. It is the smaller cost here, and it
is named so the next person can weigh it rather than discover it.

### Two things that shaped the response

**Every map is keyed by something JSON leaves alone.** Kits and fixtures by **club short name**, bench roles
by **role** — never by player id. ⭐ Keying by id would have repeated `by_gameweek`'s trap on a new screen:
integer keys become strings in transit, and `"10"` sorts before `"6"`.

**FPL's own words survive a failure.** A bad id, an unreachable API and a team that is not public until the
first deadline are three different problems. `fetch_manager_team` distinguishes them and never raises —
it returns `(None, message)` — so discarding the message loses the only diagnosis there is. The endpoint
passes it through as the 400's detail.

### ⚠️ A constant copied is a constant that can differ

The kit URL lives in `web_streamlit/badges.py`, **which imports Streamlit** — so the API could not import
it without pulling the web framework into the API process.

The first attempt retyped the template into `src/kits.py` from memory as `shirt_{code}{gk}.png`, **dropping
the `-66` suffix**. A URL that is wrong and looks entirely plausible. ⭐ *It was caught only because the two
were compared side by side* — which is the argument for moving rather than copying, made by the copy
failing. `badges` now re-exports from `src/kits.py`; every existing caller is untouched.

---

## Verification

* **10/10 mutations killed** on the new endpoint, including *the armbands are dropped*, *the bench order is
  invented*, *the keeper gets the outfield kit* and *my-team prices the squad its own way*.
* One test pins that `my_team`'s embedded analysis is **identical** to calling `/squad/analysis` directly —
  ⭐ a composing endpoint that quietly priced a squad differently would put two answers about one team in
  one app, by the back door.
* ⚠️ **The FPL fetch is stubbed in every test.** A test that reaches the internet is not a test; it passes
  on someone else's uptime. The committed sample is regenerated through the same stub, so the contract guard
  stays hermetic.
* **19 Dart tests** against the real committed responses, including that every XI player resolves a kit and
  a fixture, and that the keeper's shirt differs from the outfield one.
* The app loads the owner's real team over HTTP and draws it.

## Consequences

**Good:** the phone and the web draw the same card, and cannot disagree about a squad. One call fills the
screen. The manager id is typed into the app, so it opens on a real team.

**Costs:** ⚠️ the API now has one endpoint shaped by a layout. If a second arrangement ever wants different
furniture, the honest move is a second composition — **not** to widen this one until it serves nobody well.

**Open:** the four player shapes (checklist 1b) are still unnormalised; `build` and `route` still ship 42–45
raw database columns. This endpoint deliberately did not touch them.
