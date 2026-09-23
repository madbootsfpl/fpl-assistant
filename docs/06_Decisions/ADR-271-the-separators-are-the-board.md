# ADR-271 — The separators are the board

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner, with a screenshot of the desktop view — *"Trending had these separators and are very
important"*
**Brings across:** ADR-170 (worth noticing), alongside ADR-167 (worth a look)

---

## Context

The phone's Trending carried four boards and one reader. The desktop has a second reader the phone was
missing entirely — and ⭐ *the headings are the whole point of it.*

**Three patterns, each needing two boards at once:**

| Heading | What it says |
|---|---|
| **In form, still under-owned** | the crowd has not caught up — a differential **with evidence** |
| **A bandwagon forming** | bought heavily, not yet template — *are you early or late?* |
| **The template breaking up** | widely owned and being sold — this changes what *"safe"* means |

⚠️ **A player can top none of the four boards and still be the most interesting name on the page.** That
is precisely what a ranking of one number cannot say, and why this is not a fifth board.

⭐⭐ **Twelve rows in three named groups say three different things; the same twelve in one list say
nothing** — *the pattern a row belongs to IS the reason it is on the page.*

## Decisions

**A second reader, second in the row.** Trending now reads: **Worth a look · Worth noticing**, then the
four boards. ⭐ *Two readers, then the data they read* — and each reader leads because it says something
no single board can.

**⚠️ Rows carry a `group`, rather than this being a third answer shape.** The client draws a heading when
the group changes. ⭐ *Two lists that have to be zipped are two lists that will be*, and a row under the
wrong heading is a wrong claim about a player. A test asserts each group's rows stay **contiguous**,
because a group appearing twice would draw two headings for one pattern.

**⚠️⚠️ No ranking number, and the column is deliberately empty.** These rows are **sentences**. ⭐ *A
figure in the corner invites a reader to sort by it*, and there is nothing here to sort by. The client
omits the value block entirely when a board declares no column.

**⚠️ Every threshold is one that already exists** — `FORM_MIN`, `TRENDING_NET`, `DIFFERENTIAL_OWN`,
`TEMPLATE_OWN` are calibrated constants. ⭐ *Inventing a fourth cut-off to make a nicer shortlist would be
a number with no population behind it.*

**And it says what the crowd is DOING, never why.** Trending and Signals split on exactly that axis
(ADR-149/150) — ⚠️ *repeating a headline here would put an unsourced guess next to a measured fact.*

## ⚠️ One sentence had to be reworded, and not in the engine

The engine's note reads *"the four boards **below**"* — true of a page that stacks them, **false on a
phone** where they are a tap away. Reworded in the transport, because the Streamlit page it was written
for still stacks them. ⭐ *A sentence about a layout belongs to the layout.*

## Verification

* **5 Python tests** — the under-owned pattern leads, every row knows its group, groups stay contiguous,
  the column is empty, and the note does not describe a layout the phone does not have.
* **5 Dart tests** against a committed sample — ⭐ its own sample, because this is the only answer whose
  rows carry a `group` and whose `column` is **empty**, and ⚠️ *both are shapes a client must handle that
  appear in no other example.*
* **3/3 mutations killed** (the group blanked, a column invented, the order re-sorted alphabetically).
* 2,560 Python · 216 Dart.
