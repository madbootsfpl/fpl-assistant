# ADR-258 — One name, and a page you can read

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner — *"we had it branded as Boot Battle on the desktop app, can we use that language and
formatting. The page is hard to see on the phone in dark mode."*
**Builds on:** ADR-110 (the web's compare card), ADR-255 (photos), ADR-257 (reaching it from the list)

---

## 1. It is called Boot Battle

`player_card.py` has titled it **Boot Battle** since the wave-3 feedback. The phone called the button
*"Compare with…"* and titled the page *"Gabriel v Konsa"*.

⚠️ **A feature with two names is two features to anyone who has to be told which is which** — and that
person is a tester reading the web's help and then opening the app.

So: the MB badge and MADBOOTS lockup in a band, **BOOT BATTLE** as the title, and the same word on the
button and in the picker. ⭐ The page title is the *name*, not the two players — they are on the card
below in their own colours, and repeating them in the bar spends the title on something already said.

**The photos came with it**, because the web's compare header has had them since ADR-110 and ADR-255 says
a face belongs where a name already is.

## 2. ⭐⭐⭐ Colour is identity here, and on the web it is victory

The web tints the **winning** value teal and leaves the loser grey — on a **white card**, where grey is
perfectly legible.

On a near-black phone that same choice produced three separate failures, each defensible alone:

* every losing value at **`white38`** — and on the stat grid that is most of the page
* one player's form row at **`white10`** — dark grey boxes on a dark ground
* one projection line at **`white30`** — on a chart whose entire job is to compare two

⭐⭐ So the phone inverts it: **each player owns a colour** — purple and teal — carried through his name,
his form row, his line and his winning values; and **winning a stat is shown by weight**, not by being the
only thing visible. A reader can follow one player down the page, and nobody disappears for losing.

⚠️ *A comparison where one side is harder to see is not a comparison.*

## What building it found

⭐⭐ **A contrast test that reads the rendered tree, not the source.** Grepping for `white38` would have
caught the colours I remembered to look for; this asks **every `Text` actually on screen** how visible it
is, against the app's real background rather than a default white.

⚠️ **And it was not enough on its own.** A mutation putting a form row back to `white10` **survived** —
because the numbers inside stayed white and the test only inspected text. *The boxes were half of what
could not be read.* The rows are keyed now and a second test asks each one what fill it actually drew.

⭐ **The shape sweep caught the photo**, as it has caught every new endpoint this week. `photo` joins
`ALLOWED_EXTRAS` rather than `SHAPE` — and the reason is recorded there, because it is not a technicality:
putting a face in the shared shape would put one on every XI card's payload and invite it onto the pitch,
which ADR-084 forbids for a reason that has not changed.

## Verification

* **6 Dart tests**: the name and the brand band; every `Text` above a legibility floor; each player keeping
  his colour; the two form rows being visibly different *from each other*; a losing value still readable;
  and the committed sample really being two of the same position.
* **6/6 mutations killed**: the losing value back to `white38`; a form row back to a dark box; the stat
  label dimmed; both players sharing a colour; both form rows sharing a fill; and the band losing its name.
* `compare` joined the committed samples, so the widget tests render the real response.
