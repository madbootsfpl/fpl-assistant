# ADR-286 — Lenses the phone could not see

**Date:** 2026-09-24
**Status:** Accepted
**From:** the owner, with the mobile and web cards side by side — *"the 4 options 'Captain to Transfer'
could be side by side on one line… add set piece and template emojis above that… Note that XL is not
rendering for next and 3rd Gameweeks"*

---

## The bug: the numbers were already on the device

The card showed `TOT (H) 5.4`, then `LEE (A) —`, then `BOU (H) —`. The web card, same player, same
moment: **5.4 · 5.4 · 5.3**.

The sheet read `player.byGameweek`. `my-team` is fetched with `horizon: 1`, so that map holds **one**
gameweek — while the same response carries `run_xp`, which holds all three, and which `MyTeam.runXpFor`
has exposed since it was written.

⭐⭐ *A value that is fetched, parsed, stored and then read from the wrong place looks exactly like a
value the server never sent.* One line.

## The badges: the same product, disagreeing with itself

`🟦 template · ⚽ pens · 🚩 corners · 🎯 FK` have been on the web card since ADR-081 and US-289. The phone
showed none of them — not because they were hard, but because the `player` endpoint never sent them.

⚠️ **A lens the engine already applies, withheld from one client, is not a missing feature.** The server
now sends `badges`, built from `crowd`'s **public** helpers so the duty rules and the ownership
boundaries keep one definition — *a second copy of "who takes the corners" is a second answer to it.*

⭐ **Glyph and word arrive apart**, not as the `"🟦 template"` string the tables use: *a client that has
to split a string to lay it out will one day split it differently*, and the phone draws the two at
different sizes.

⭐ **And both halves are rendered.** The emoji alone was the temptation, and the pitch already learned the
opposite lesson from the other side (ADR-178): on a 104px kit the words wrapped to three lines, so the
glyphs went bare and a key went at the bottom. A sheet has room and no key — ⚠️ *three unlabelled
pictures is a rebus, and a reader who does not know what 🎯 means has no way to find out from a phone.*

## The layout: four rows became one

Four full-width actions cost ~200pt of a sheet whose subject is a player, and ⚠️ *a sheet that pushes its
own subject off the screen has become a menu about him.* Across, they read as one question with four
answers.

Three things that fell out of it:

- **The labels shortened** — "Make captain" → **Captain**, "Bench him…" → **Bench**. The icon above each
  word carries the recognition; the verb was there because they were stacked rows.
- **Order is preserved left to right.** A substitution is free and reversible; a transfer costs points
  and cannot be undone — ⭐ *order on a set of actions is a recommendation whether or not it was meant as
  one*, and reading order still carries it.
- **Bench is greyed, not removed**, when a player has no legal partner. ⚠️ *A row of four that sometimes
  has three moves the other three sideways*, and a control that changes place is one you have to find
  again.

## What the tests had to be told

The existing sheet tests asserted `'Make captain'` and failed — ⭐ *which is the guard working*, and the
right moment to decide the rename was deliberate rather than discover it in a screenshot.

The new ones pin what a screenshot would show: that **no fixture renders an em-dash** (not merely that
the first number is right), that each badge appears **glyph and word together**, and that a card with no
badges renders **no strip at all** — *an empty row of pills reads as "loading", not as "nothing to say".*

6/6 mutations killed on the client, including the one-gameweek map returning, the strip rendering empty,
and only the emoji being shown. 7 tests on the server, one of them pinning that the badges agree with
`crowd` rather than reimplementing it.

## ⚠️ This needs the API deployed

The badge strip is empty until Render has the new build; the sheet renders without it and the fixture
fix is independent of it. ⭐ *A client change that degrades to the previous behaviour can ship before its
server does* — which is why `badges` defaults to empty rather than being required.
