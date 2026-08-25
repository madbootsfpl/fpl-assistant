# Architectural Decision Record: Price arrows use the colour channel — green up, red down

**Decision ID:** ADR-140
**Date:** 2026-08-25
**Status:** ✅ **Accepted — built** (Sprint 194, 2026-08-25). **1350 → 1354 tests, ruff clean.**
Owner-reported 2026-08-25, logged to the Roadmap the same day, built the same day.
**Superseded By / Replaces:** A display correction to ADR-092 (the price-change predictor). **No analytics
change** — `price_prediction` and `price_pressure` are untouched; only the glyph and its colour change.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner, 2026-08-25:

> Price changes should show green triangle for up & red triangle for down.

**Verified, and the problem was sharper than a preference.** `price_flag` returned 🔺 / 🔻 — and *both of those
are red*. U+1F53A is named, literally, **"red triangle pointed up"**; U+1F53B is "red triangle pointed down".
So direction was carried **twice** (by shape and by position in the legend) while **colour — the fastest
channel a reader has — carried nothing at all.**

**And this is not a one-character swap, which is the part worth writing down.** There is no green triangle in
the emoji set. An emoji brings its own colour and cannot be recoloured by CSS, so *any* fix means leaving
emoji behind, and the replacement has to survive three different rendering contexts:

| context | can it colour? | mechanism |
|---|---|---|
| `st.dataframe` cell (the Pool "Price" column) | not with markdown | **pandas Styler** |
| Streamlit caption / tooltip (legends, the Health nudge) | yes | `:green[…]` / `:red[…]` |
| terminal (`ui/price.py`, the `ask` price answer) | no | shape only |

Two dead ends were checked before landing on the Styler, both worth recording so nobody re-checks them:
`st.column_config.TextColumn` has no colour option at all, and **`MarkdownColumn` renders its markdown only in
a click-through overlay, not in the cell** — its own docstring says *"displays cell values as plain text within
the table cells"*. So `:green[▲]` is simply not available inside a dataframe.

---

### ✅ Decision

**1. One glyph pair for the whole app: plain text `▲` / `▼`**, defined once as `PRICE_UP` / `PRICE_DOWN` in
`analytics/price.py`. Plain glyphs **inherit** the surrounding colour, which is the property that makes
everything else possible.

Defining them once, and having the CLI import them rather than keep its own literals, is deliberate: *one rule
written twice always drifts* is a lesson this project has paid for more than once. The terminal renders them
uncoloured — no worse than two identical reds, and there the section headers already carry the direction.

**2. Colour where colour is possible.**
- **Pool "Price" column** — a `colour_price(rows)` helper returns a pandas **Styler** painting `▲` green
  (`#16a34a`) and `▼` red (`#dc2626`). It composes with `column_config`: ImageColumn thumbnails and
  NumberColumn formats both survive, and multi-row selection still indexes positionally, which is what the ⭐
  watchlist depends on.
- **My Squad ▸ Health price nudge** and **`PRICE_LEGEND`** — Streamlit colour markdown, natively.

**3. `colour_price` degrades to the plain rows** when there is nothing to paint (no rows, or no such column),
so a caller hands the result straight to `st.dataframe` without asking which it got. An uncoloured table is
the right failure: the glyphs still carry direction by shape.

**4. Two legends, pinned to agree.** `PRICE_LEGEND` carries the colour markdown; `PRICE_LEGEND_PLAIN` is the
literal version. A test asserts one is the other with the markup stripped, because that is exactly the kind of
pair that drifts silently.

**Not in scope — and this is a real limitation, not an oversight.** The **retrospective** crowd pair
(💰↑ / 💸↓, `cost_change_event`) is *not* coloured. A Styler can only paint a **whole cell**, and those flags
share the "Trends" cell with the ownership tier, transfer momentum and form flags. Colouring that cell would
paint five unrelated signals. They are also already visually distinct from each other, which the two red
triangles were not. Recorded here so the asymmetry reads as a decision rather than a miss.

### ⚠️ Risks

- **A Styler is a different object than a list of dicts.** Anything reading the table back must cope. Pinned
  by a test that the Pool's `Price` column still reads as plain values, since selection and the watchlist
  index into it.
- **Red/green is the worst possible pair for the ~8% of men with red-green colour vision deficiency.** Direction
  is still carried by **shape** (▲ vs ▼), so no information is colour-only — which is the accessibility rule
  that matters. The colour is an accelerator, not the message.

### 🧪 Definition of Done

1. **Tests** — the glyphs are non-emoji (asserted as a *property*: no codepoint in the emoji plane, so a
   revert to 🔺/🔻 fails loudly rather than silently disabling the Styler match); the two legends agree; the
   Styler paints green on the **up** row and red on the **down** row and leaves stable rows alone; it degrades
   to plain rows; and the Pool column still reads back as plain values.
2. **Manual smoke** — the Pool table on live data (16 risers / 18 fallers today, so both colours are visible);
   the CLI mover block.
3. **Docs** — this ADR, the Roadmap entry, PROJECT_STATUS, the Feedback_Log row, `docs/05_Sprints/Sprint194.md`.

---

### 🔎 One thing I got wrong on the way

While smoking the CLI block I passed raw `sqlite3.Row`s to `render_price_movers`, hit an
`AttributeError: 'sqlite3.Row' object has no attribute 'get'`, and concluded it was a latent Row-unsafety bug
of the kind this codebase keeps hitting. **It was not.** That renderer takes the caller's *display dicts* — its
`pressure` column is computed by the caller and exists on no player record — so a Row was never valid input
and the `.get()` was correct. The "fix" was reverted; what stayed is a docstring stating the contract, which is
the actual improvement, since it is what would have stopped me making the mistake.

Worth recording because the reflex was right and the diagnosis was not: *a crash in a probe you wrote is
evidence about the probe first.*
