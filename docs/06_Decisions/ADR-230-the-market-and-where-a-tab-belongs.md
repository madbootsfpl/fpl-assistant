# ADR-230 — The market, and where a tab belongs

**Date:** 2026-09-22
**Status:** Accepted
**Builds on:** ADR-229 (the bar), ADR-227 (one shape)

---

## 1. Players: fetched once, filtered on the device

`POST /api/v1/players` returns **every available player, ranked**, in one call — 96 KB, 481 players, 75 ms.
The client searches and filters locally.

⭐ *The cheap thing sent once beats the small thing sent constantly.* A round trip per keystroke is worse
than 96 KB once, and it is the same payload reasoning spike 017 used to shape this whole client.

⭐ **Unavailable players are excluded, not flagged.** A browse list is for finding someone to buy, and a
player who cannot play is not a candidate — leaving him in makes the reader do the filtering the app exists
to do. ⚠️ **Doubtful players stay and are flagged**: a doubt is a probability, not a verdict (ADR-206), and
a 75% player is often exactly who you want.

### ⚠️ This is not what §4.1 designed, and that is on purpose

The audit says the browse surface should read the published board **straight from Supabase** — which is
what ADR-213 publishes it for, and spike 018 proved (667 players, 162 KB, 511 ms).

**It is not testable today.** Staging predates the board (`xp_board` → `PGRST205, table not found`), and
production credentials are not something to hand a browse screen in order to try it.

⭐ **So I built the path I can verify.** *Shipping code nobody has run is how this session's bugs were
made* — twice today a guard passed because it had never reached the thing it guarded. 📅 **Revisit when the
app carries Supabase config for a real device**, which is the same moment hosting stops being optional.

---

## 2. Where a tab belongs: working earns a place, frequency earns a slot

ADR-229 put Chips in the bar on the rule *"a tab earns its slot by working"*. ⚠️ **That rule answers the
wrong question.**

⭐⭐ *"Should this be hidden?"* and *"should this hold one of five permanent slots?"* are different
questions. Working answers the first. **Frequency answers the second** — which is ADR-166's rule for the
web sidebar, applied one screen smaller.

A chip is a handful of decisions per season. Players is browsed weekly.

⭐ **And the audit settles it without my opinion:** §6's first release is *This week · My squad ·
Transfers · Players*. **Chips is not in it.**

So the bar is `My team · This week · Transfers · Players · More`, and Chips is a full entry in More that
opens the real screen. ⚠️ **More is no longer a graveyard for unbuilt things** — it holds working ones now,
which is what makes that placement a decision rather than a demotion.

⚠️ **Chips has moved four times** (greyed → More → bar → More). That is churn, and it is worth naming: each
move was right on the rule being applied and the rules kept turning out to be about different questions.
The bar is now ordered by the audit's own priority, which is the first ordering that came from outside this
conversation.

---

## Also fixed

**The Dart client hardcoded `/api/v1/squad/`.** Every endpoint was squad-shaped until this one, so the
prefix lived in the shared `_post`. The market reached it only via `'../players'` — a path that depends on
URL normalisation to work at all. ⭐ Now each caller names its own path, including the prefix.

## Verification

* Suite **2,254 passed**; the shape sweep's completeness check demanded `players` be covered before it
  would go green.
* Payload pinned by a test: ⚠️ the *fetch-once* design only holds while the market stays a sensible size.

## Consequences

**Good:** the first release's four screens all exist. Search finds a player by name **or club**, because
*"ars"* is how a manager actually looks. The list marks who you already own — ⭐ *a market list that does
not know what you hold makes you check your own pitch to read it.*

**Costs:** ⚠️ two ways to get the board now exist in principle (API here, Supabase in §4.1), and only one
is built. That is a fork to close, not a design.

**Open:** the player **card** — the audit's §6 says *"search, compare, the card"*, and this is search
only. Tapping a row does nothing yet.
