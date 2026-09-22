# ADR-223 — A pitch you can navigate from

**Date:** 2026-09-22
**Status:** Accepted
**Builds on:** ADR-222 (the landing pitch)

---

## Context

ADR-222 put the squad on a pitch. Three things came back from using it:

> *"Transfers & Bank is better, if we dont have lets live with what we have got."*
> *"The pitch render is just a blank green background. If possible can you overlay pitch markings?"*
> *"On the web, our bottom tab took us to 'What to do this week', 'Captain', 'Transfers', 'Chips'. We need a
> mechanism to have these selectable from the landing screen."*

---

## 1. The money: FPL had been sending it all along

⭐⭐ **`picks_to_squad` was reading the picks out of the payload and discarding `entry_history`** — which
carries **`bank`** and **`value`** in the very same response.

That matters beyond a header. **ADR-191** is the record of this app advising a position its manager was not
in, because `bank` was hard-coded to £0.0m on one surface while the Transfer tab collected it by hand three
tabs away. ⚠️ *The number was one dictionary key away the whole time.*

**⚠️ FPL counts money in tenths.** `bank: 13` is £1.3m. A missing division hands a manager ten times his
money, and every affordability answer downstream is wrong while looking entirely reasonable.

**⭐ None is not zero.** An empty bank is a real position a manager can be in; *"we could not read your
bank"* is not. `_money` returns `None` for absent, and the header renders `—` rather than `£0.0m`.

### Free transfers cannot be had

Checked rather than assumed: the entry payload carries bank and value and **not** free transfers, which sit
behind a login. `event_transfers` is how many were *made*, not how many are held.

So the client states it and the server echoes it back. ⭐ *A stated assumption can be corrected where a
silent one cannot* — and a header showing a number the manager never set would be the app inventing his
position.

## 2. The pitch: painted, not a picture

Markings drawn as vectors scale to any phone with no second asset and nothing to download. ⭐ The real
reason is placement: the lines position **relative to the card rows**, so a five-defender formation and a
three-defender one both read as a football pitch rather than as a background someone laid players on.

⚠️ **Deliberately faint — white at 22%.** The markings are orientation, not content: the eye must land on
the xP number first. ADR-135 is this project's record of what happens when a surface is over-densified, and
a pitch at full contrast competes with every card standing on it.

## 3. Navigation: five tabs, three built

`My team · Transfers · This week · Captain · Chips` — the web's own sub-tabs, in the same order.

⚠️ **Captain and Chips are shown greyed rather than hidden.** A bar that grows items later moves everything
under the user's thumb, and muscle memory is the first thing a returning user brings. ⭐ *"Not built yet" is
information; an empty screen is a bug report* — so tapping them says so, and says what they would need.

**The squad is loaded once and shared across tabs.** Two screens fetching it separately could disagree
about who you own — the failure this app's whole contract layer exists to prevent — and on a phone it is
three round trips for one answer.

⭐ **Still no Riverpod.** A `setState` at the top of one widget is genuinely enough for three tabs over one
object. The moment it stops being enough is the moment it earns its place; adding it now would be a
foundation built to a guess.

---

## What using it found

* **The "on your bench" warning fires on real advice.** `Leno → Tzolakis +2.0 xP` is a genuine gain and
  changes the XI by nothing this week. ⭐ *The number is right and would mislead alone*, which is what that
  line of copy is for.
* ⚠️ **A test of mine asserted FPL's arithmetic with a fabricated fixture.** It paired a synthetic £104.6m
  squad with FPL's real `value: 995` — from a different squad — and checked `cost + bank == value`. That
  relationship is a fact about *FPL's* payload, verified once against the live API; a constructed fixture
  cannot confirm it. ⭐ *A fixture only confirms what you put in it.* The assertion was removed and the
  observation written down instead.

## Consequences

**Good:** the header carries what the owner asked for; the pitch reads as a pitch; three screens are
reachable without leaving the landing view; and `bank` now flows from FPL into every affordability answer
rather than being typed twice.

**Costs:** the bottom bar advertises two screens that do not exist. That is a deliberate trade against
moving the bar later, and it expires the moment they are built.

**Open:** Captain and Chips need a **mechanism to change the team**, not just read it — every screen so far
is read-only, and making a substitution or setting an armband is the first thing that writes. Where that
state lives (session-only, or saved against a manager id) is a Stage C question.
