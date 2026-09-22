# ADR-236 — The comparison belongs where the decision is

**Date:** 2026-09-22
**Status:** Accepted
**Extends:** ADR-110 (Boot Battle), ADR-197 (no verdict)

---

## Context

From the Hub review, the owner: *"the way they do their AI transfers is akin to our Boot Battle / Player
DNA."*

He was right, and more precisely than "similar feature". **We already had the substance** — ADR-110's
`compare_rows` puts two same-position players side by side with the better value marked per stat. They had
two presentations we lacked, and one placement.

⭐⭐ **The placement is the finding.** Theirs sits *inside the transfer flow*, attached to the swap being
suggested. Ours lives on the Players page as a destination you navigate to.

*A screen that suggests `Groß → Belloumi` and cannot show you the two of them is sending you to another
room to answer the question it just raised.*

## Decision

**`POST /api/v1/compare`, rendered inside the transfer card.** Tap *Compare* on a suggested move and it
expands in place — **lazily**, so a list of five suggestions costs five requests it never makes.

Three things, because the Hub showed two we did not have:

* **the stat grid** — ours already
* **recent form** — the last five gameweeks, ⭐ *with minutes*, because **ten points off the bench is not
  ten points from a starter** and a form line without them flatters a substitute
* **the projected run** — both players' per-gameweek xP, drawn on **one shared scale**: ⚠️ normalising each
  line to its own maximum would draw two flat lines and call it a comparison

### ⚠️ No verdict

ADR-197 gave the DNA comparison none on purpose, and the same reasoning holds here. The tally is rendered
small and grey: ⭐ *a count of stats won is a headline, not a recommendation.* The engine already made the
recommendation — **this is the working behind it**, which is the half ADR-182's mantra promises.

---

## ⚠️ The third module that could not be shared because it imports Streamlit

`player_card.py` holds the comparison **and** its HTML. The API cannot pull a web framework into itself to
ask *"which of these two numbers is better?"*, so the pure half moved to `src/analytics/compare.py`.

That is now **three**: `badges.py` (ADR-222), `access.py`, and this. ⭐ *A module that mixes a rule with its
rendering will eventually be needed by something that cannot render.*

**Moved verbatim, not retyped** — ADR-222 reproduced a URL template from memory and lost a `-66` suffix.
All **185** existing card and DNA tests pass unchanged, which is what moving rather than rewriting buys.

### The rule that a naive comparison gets wrong

`_BETTER` knows that a **lower** expected goals-conceded is the better number. ⚠️ A `max()` would crown the
worse defence — and it would do it on exactly the stat a defender is bought for. Pinned with a constructed
fixture, because whether the seed holds two defenders whose xGC differs is an accident of the snapshot.

---

## Verification

* **7/7 mutations killed**, including *xGC treated as higher-is-better* and *form looked up by id rather
  than code*.
* ⚠️ One mutation was a **no-op**: it added an unused dict instead of changing `_BETTER`, and "survived"
  for a reason that had nothing to do with the tests. ⭐ *A mutation that changes nothing proves nothing* —
  the same false signal as the not-applied pattern (ADR-219) and the broken harness (ADR-235).
* **`code`, not `id`** — FPL restarts element ids every August, so per-gameweek history is stored under a
  player's code. Looking it up by id returns another player's season, silently, and only after a summer.

## Consequences

**Good:** the working sits under the recommendation. One comparison engine serves the web card and the
phone.

**Costs:** ⚠️ `/compare` needs the raw history (1.9 MB server-side) for the form strip, so it is the one
lazy call on the transfers screen that is not cheap. It runs once per expansion, not per render.

**Open:** the same comparison would fit the **Players** tab — tap two rows, battle them. That is the
audit's *"compare"*, still unbuilt on the phone.
