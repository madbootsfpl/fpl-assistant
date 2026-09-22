# ADR-234 — Which chips you have actually got

**Date:** 2026-09-22
**Status:** Accepted
**Fixes:** ADR-229
**Prompted by:** a competitor review

---

## Context

The owner reviewed Fantasy Football Hub — *"not because I want to copy like for like, but the testers use
it as a benchmark and will feedback using it as a reference."*

Across twenty-four screens, most of what it surfaced was layout. **One was not.** The Hub's chip sheet
labels every chip `Played GW2` or `1x Not played`.

⚠️⚠️ **Our chip advisor had no idea which chips were still in hand.** It would recommend a wildcard for
GW11–13 to a manager who played it in GW4 — ⭐ *not a rough edge, a wrong answer delivered confidently.*

**Checked rather than assumed:** `entry/{id}/history/` returns a `chips` array of what has been played and
when. It was one endpoint away.

---

## Decision

**`chips` takes an optional `manager_id`.** With it, each chip reports `available` and `played_in`.

### ⭐⭐ Three states, not two

`true` in hand · `false` spent · **`null` we could not check.**

⚠️ **`null` must never render as `true`.** *"We could not check"* and *"you still have it"* are different
facts and only one is safe to act on — the same distinction as the bank's `None`-not-zero (ADR-223).
Without a manager id, or after a failed fetch, every chip reads **unknown** and the screen says so out
loud. *Silence there would read as "you have all four".*

### ⚠️ Availability is per HALF-SEASON, not per season

Chips come in two sets, the second unlocking around GW20 — `CHIP_HALVES` already knew this for deadlines
(ADR-166) and nothing used it for *availability*.

⭐ *"Have I used my wildcard?"* is meaningless without saying **which** wildcard. Treating it as a
season-long question would tell a manager in January that he has nothing left.

### A spent chip is marked, not removed

*When it would have been best* is still true. ⭐ Hiding the card would leave a manager wondering whether the
app knew about the chip at all — so it is dimmed and pilled, and **the recommendation stops being an
instruction**.

⭐ And the pill names the gameweek: *"Played GW4"*, because **"unavailable" alone invites a reader to think
it is a bug.**

### Never load-bearing

The timing advice needs no network. A failed lookup loses the status and **keeps the answer**.

---

## Verification

* **6/6 mutations killed**, including *unknown defaults to available* and *availability ignores the
  half-season split*.
* ⚠️ One survived first: *the gameweek it was played is dropped*. The endpoint tests stub `_chip_status`
  wholesale, so the real function was never reached — ⭐ *a stub bypasses exactly the thing it stands in
  for.* Fixed by asserting `played_in` against `chips_available` directly.
* The spent-chip tests are **constructed**: the owner has played none, and a fixture where nothing has been
  spent cannot show that spending is noticed.

## Consequences

**Good:** the app no longer recommends something you cannot do. The half-season rule is now used for
availability as well as deadlines.

**Costs:** ⚠️ one more FPL call, on the Chips screen only — deliberately not in `my-team`, whose speed
ADR-217/218 spent a day earning.

**Open:** the same question applies to **free transfers**, which FPL does not publish at all (ADR-228). A
chip we can check; a transfer we must ask about. ⭐ *That asymmetry is worth remembering when someone
proposes inferring one from the other.*
