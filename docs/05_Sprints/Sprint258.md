# Sprint 258: Wrap the answer blocks (ADR-191)

**Dates:** 2026-09-15
**Status:** ✅ Complete — **1770 → 1782 tests, ruff clean.** No decision changed; this is layout.

> **Owner, on a chip answer:** *"Could you get the screen to wrap?"*

---

## The problem

The chip and gameweek blocks are fixed-width console output. Their **static** prose has always been
hand-wrapped at 100 columns. Their **dynamic** lines never were, and they have grown — ADR-185 put the
rebuild's value into the wildcard line, ADR-089 appended a confidence to every chip, ADR-191 added a longer
view to every move. The wildcard line now runs past **230 characters**, which a terminal breaks at column 0
and `st.code` does not break at all: finishing the sentence means scrolling a monospace box sideways.

## Three decisions inside a one-line fix

**1. Hang the continuation under the text, not at column 0.** Breaking at the margin would put the wildcard
sentence's continuation in the *label* column, where it reads as another chip. The label column has to stay a
column:

```
  Wildcard:       worth +97.2 xP — a fresh build beats your squad over this window; you keep only 2 of 15;
                  £14.1m of your squad cannot play. Your weakest stretch GW5–GW7 (avg XI 48.8 xP) — reset
                  before it  · Confidence 95/100 · High
```

**2. Never split a hyphenated name or an over-long token.** These blocks are full of Calvert-Lewin,
Dewsbury-Hall, Gibbs-White — a name broken across lines reads as two players.

**3. Weld the confidence suffix.** Nearly every dynamic line ends `· Confidence 40/100 · Low`, and a plain
wrap orphans the band word on a line of its own. It happened at 100 columns, so the width went to 110 — and it
happened again on a different line. ⭐ **When a wrap keeps producing the same ugly break, the fix is to say
what may not be broken, not to move the boundary.** The suffix now travels as one token and moves down whole.

## ⚠️ Three of seven mutants survived the first sweep

| mutant | first sweep | after |
|---|---|---|
| continuations break at the label column | ✅ | ✅ |
| **hyphenated names get split** | ❌ **passed** | ✅ |
| **a long token is chopped** | ❌ *(not tested)* | ✅ |
| **the chip block stops wrapping** | ❌ **passed** | ✅ |
| the confidence suffix is breakable | — | ✅ |
| the weld character leaks into output | — | ✅ |
| the width is widened past any screen | ✅ | ✅ |

**The hyphen one is the instructive fixture fault.** The test padded a line with filler and asserted
`Calvert-Lewin` survived — and passed with hyphen-breaking turned back on, because the name never reached the
wrap point. The padding is now swept across the boundary so the hyphen lands exactly where the break would
fall. ⭐ *A fixture that only exercises the lucky case will confirm a broken mechanism* — third time this
month.

**And the chip one is worse, because it is the thing the owner reported.** Every test exercised `wrap_block`
directly, so removing the call from `render_chip_advice` left the whole file green. ⭐ **Testing a component
is not testing that anything uses it** (ADR-185, and now twice more). A test now asserts the *rendered chip
answer* comes back inside the width.

## One mutant is equivalent, and is left alone

`wrap_block` returns early for lines that already fit. Removing that early return changes nothing: `textwrap`
preserves internal runs of spaces, so a short line comes back identical either way. It is an optimisation and
a statement of intent, not a behaviour — so there is no test for it, and the module says so rather than
someone later writing a contrived one to turn the sweep green.

---

## 💡 The lesson

> **Output grows one commit at a time, and nobody owns its width.**

No single change made the wildcard line unreadable. ADR-185 added what the rebuild is worth, ADR-089 added a
confidence, ADR-191 added a longer view — each correct, each a few characters, each reviewed against the line
it changed rather than against the screen it lands on. The hand-wrapped prose beside it stayed at 100 columns
the whole time, which made the drift invisible: the block *looked* like something that had a width.

The generalisable form: **when a format is enforced by hand in one half of a block and by nothing in the
other, the unenforced half is where the rot goes.** Now the width is a function, applied to both.

---

## Definition of Done

1. **Tests: 1770 → 1782** — twelve for the wrapper, seven mutants confirmed red, one equivalent and
   documented as such.
2. **Manual smoke** — the real chip answer for RoboTS, wrapped, with the confidence suffix intact.
3. **Docs** — ADR-191's action list, this retro.
