# ADR-226 — The manager chooses; we price it

**Date:** 2026-09-22
**Status:** Accepted
**Builds on:** ADR-225 (drafts), ADR-223 (the tabs)
**Amends:** ADR-223's bottom bar

---

## Context

Two calls from the owner, both of which made the app smaller:

> *"manual transfer, can select a higher priced player, just flag it as over budget."*
> *"For Captain, do we need it on bottom bar, surely a simple client side click for captain & vice
> Captain could be viable."*

---

## 1. Over budget is flagged, never hidden

`suggest_transfers` filters candidates by `price <= budget`, which is right when the app is
**recommending**. It is wrong when the manager is **choosing**.

⭐⭐ **A candidate silently removed looks like a candidate that does not exist.** A manager who cannot see
Saka concludes he is ineligible, not that he is £2.5m dear — and those are different facts leading to
different decisions.

⚠️ It is also inconsistent with what this codebase already does: `apply_transfer` has always treated an
over-budget squad as a **soft warning that never blocks**, *"because prices drift"*. A move you cannot quite
afford today is a plan, not an error.

So `replacements_for` returns every legal candidate with `affordable` and `over_by`. **Affordability is the
only rule relaxed** — position, ownership, availability and the ≤3-per-club cap all still hold, because an
illegal squad is not a plan, it is a squad FPL will refuse.

### The rule was extracted, not copied

The legality predicate lived inline inside `suggest_transfers`. A manual screen needs exactly the same
notion of *legal*, so the choice was **one rule with two implementations, or one rule in one place**.
ADR-181 is this project's record of which of those survives contact with a change — so
`is_legal_replacement` and `_club_counts` came out, and `suggest_transfers` now calls them. All 44 existing
transfer tests passed unchanged, which is the point of extracting rather than rewriting.

## 2. The armband is a tap, not a tab

⭐⭐ **Setting a captain changes no number this app computes.** FPL doubles the captain's points; our
projections are the XI's own xP and do not. So it is a *display* decision — which means no round trip, no
server involvement, and no screen of its own.

The owner saw this before I did. **Captain is gone from the bottom bar**; tapping any player on the pitch
offers *Make captain · Make vice-captain · Replace him…*.

⭐ The pitch is the right surface for it: it is where a manager already looks to decide anything, and a tab
called "Captain" would have been a second place to do a thing that belongs here.

⚠️ **A captain cannot also be vice.** Setting one clears the other if they collide — FPL would reject it,
and an app that lets you build an impossible team is teaching you something untrue.

---

## What building it found

### ⚠️ The four player shapes arrived in practice

`transfer.py`'s `_summary` is the **five-key minimal** player shape — no `status`, no `position`. A
candidate list built from it alone **could not flag anybody**, so the screen would have offered a
25%-chance player with nothing to say he was doubtful.

⭐⭐ That is ADR-206's exact failure on a new surface: *a doubt is a probability, and hiding it prices it at
certainty.* The rows now carry position, status and chance.

This is start-checklist item **1b** — the four inconsistent player shapes — arriving as a bug rather than as
a tidiness argument. It is still not fixed globally.

### ⚠️⚠️ Two tests of mine were wrong in ways worth recording

**A presence check passes against a lie.** `assert "status" in candidate` survived a mutation that
hard-coded every status to `"a"`. Presence is not truth.

**A skip is not a pass.** The replacement test then *skipped* when no doubtful candidate was found — and
the same mutation caused that skip, so it survived again (ADR-178, again). ⭐ The fix was to **measure the
population first**: the seed holds 24 doubtful players, 99 of whom are legal replacements in a normal
squad. The case is real, so its absence is now a failure.

**And a test assumed a legality it had not checked.** The first version picked a doubtful player and
asserted he must be listed; he was not, because the ≤3-per-club cap legitimately blocked him. ⭐ *The same
species as the bug it was written to catch.*

---

## Verification

* **10/10 mutations killed**, including *over-budget candidates are filtered out*, *affordability is
  inverted*, *the club cap is ignored on the manual screen* and *availability is dropped from a candidate*.
* All **44 pre-existing transfer tests** pass unchanged after the predicate extraction.
* Suite **2,239 passed**; **29 Dart tests**.

## Consequences

**Good:** the manager can pick anyone legal and see the price of wanting them. The bottom bar is one item
shorter and the pitch does more. One legality rule, in one place.

**Costs:** ⚠️ the pitch is now interactive, so every card is a target — and a mis-tap opens a sheet rather
than doing something, which is the safe direction, but it is a surface that did nothing before.

**Open:** Chips is the last unbuilt tab. Item **1b** — normalising the four player shapes — is now
overdue; this change worked around it in one place rather than fixing it.
