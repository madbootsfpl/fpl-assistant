# Sprint 194: Price arrows use the colour channel (ADR-140)

**Dates:** 2026-08-25
**Status:** ✅ Complete — ADR-140. 1350 → 1354 tests, ruff clean.

> **Owner:** *"Price changes should show green triangle for up & red triangle for down."*

---

### 🔍 What was actually wrong

Verified before building, and it was sharper than a preference. `price_flag` returned 🔺 / 🔻 — **both red**.
U+1F53A is named, literally, *"red triangle pointed up"*. So direction was carried **twice** (shape, and
position in the legend) while **colour, the fastest channel a reader has, carried nothing.**

**And it was not a one-character swap.** There is no green triangle in the emoji set, and an emoji brings its
own colour that CSS cannot override. So any fix meant leaving emoji behind — and the replacement had to work
in three different rendering contexts:

| context | can it colour? | mechanism |
|---|---|---|
| `st.dataframe` cell (the Pool "Price" column) | not with markdown | **pandas Styler** |
| Streamlit caption / tooltip | yes | `:green[…]` / `:red[…]` |
| terminal | no | shape only |

Two dead ends, checked and recorded so nobody re-checks them: `st.column_config.TextColumn` has no colour
option, and **`MarkdownColumn` renders markdown only in a click-through overlay** — its own docstring says it
*"displays cell values as plain text within the table cells"*. `:green[▲]` is simply unavailable in a
dataframe.

---

### 🔧 What shipped

**One glyph pair for the whole app** — plain `▲` / `▼`, defined once as `PRICE_UP` / `PRICE_DOWN`, with the
CLI importing them rather than keeping its own literals. Plain glyphs inherit the surrounding colour, which is
what makes everything else possible; and *one rule written twice always drifts* is a lesson already paid for
here.

Colour applied where colour exists: a `colour_price(rows)` Styler for the Pool column (green `#16a34a` up, red
`#dc2626` down), Streamlit colour markdown for the legends and the My Squad Health nudge, and plain shape in
the terminal. `colour_price` returns the input untouched when there is nothing to paint, so callers never have
to ask which they got.

**Explicitly not coloured: the retrospective 💰↑ / 💸↓ crowd pair.** A Styler paints a *whole cell*, and those
share the "Trends" cell with the ownership tier, transfer momentum and form flags — colouring it would paint
five unrelated signals. Recorded in the ADR so the asymmetry reads as a decision, not a miss.

---

### 💡 Two things worth keeping

**1. "Change the colour" was a three-context problem wearing a one-character disguise.** The request took ten
words; the answer needed a survey of what each rendering surface can actually do, and two of the three
plausible mechanisms turned out not to work at all. The cost of *finding that out* was most of the sprint —
and writing down the dead ends is what stops it being paid twice.

**2. A crash in a probe you wrote is evidence about the probe first.** Smoking the CLI block, I passed raw
`sqlite3.Row`s to `render_price_movers`, got `'sqlite3.Row' object has no attribute 'get'`, and diagnosed a
latent Row-unsafety bug — the exact species this codebase has hit repeatedly, which is *why* it was such an
easy call to make. It was wrong: that renderer takes the caller's **display dicts**, its `pressure` column is
computed and exists on no player record, so a Row was never valid input. The fix was reverted; a docstring
stating the contract stayed, since that is what would have prevented the mistake.

The reflex was right and the diagnosis was not, which is the more interesting failure. Pattern-matching to a
known bug species is a good instinct precisely because it is usually right — and that is what makes it worth
checking rather than acting on.

### 🧪 Tests

**+4 (1350 → 1354).** The glyphs are asserted as a **property** — no codepoint in the emoji plane — so a
revert to 🔺/🔻 fails loudly rather than silently disabling the Styler's exact-glyph match. The two legends are
pinned to agree with the markup stripped. The Styler is checked by reading its CSS rules back **per row**, so
it asserts the *pairing* (green on the up row, red on the down row, nothing on a stable one) rather than
merely that two colours appear somewhere. And the Pool column still reads back as plain values, because row
selection and the ⭐ watchlist index into it.
