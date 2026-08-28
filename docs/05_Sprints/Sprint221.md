# Sprint 221: One squad lens per page (ADR-164 — US-441 · US-442)

**Dates:** 2026-08-28
**Status:** ✅ Complete — ADR-164. 1560 → 1563 tests, ruff clean.

> **Owner:** *"Team DNA should have option for my squad only."* · *"Signals should have a global option for my
> squad only related news/signals etc."*

---

### 🔧 What shipped

Both pages **already had** a my-squad control, which is what made them worse than pages with none.

On **Team DNA** the checkbox sat on the ticker, halfway down — so the 20-club scan above it ignored a control
the reader had already set. One page answering *"my squad"* in its lower half and *"the league"* in its upper
half, with nothing saying which. On **Signals** the filter was created inside section 1; section 4 reused it by
coincidence of scope and sections 2 and 3 ignored it.

Now one control per page, created above everything it governs. It reaches the **headlines** too, by a different
mechanism — a headline is a sentence, not a player row, so it is resolved with ADR-152's name index rather than
a row filter, which is why a headline about *Reece James* doesn't surface for an owner of *James Maddison*.

The page says when it's filtered and counts what it hid (*"6 of 47 headlines mention one of your players"*),
and the control is **disabled with a reason** rather than hidden when no squad is loaded.

---

### 🐛 The consolidation created its own bug

Unifying Team DNA's control introduced a **`NameError`** — the checkbox is created inside `if _all_dna:` and
the ticker below reads it unconditionally, so a snapshot with no DNA would have crashed the page. Caught,
bound before the block, and pinned by a test that fails with the original error if the binding is removed.

Worth noting because merging two independent things is exactly when a variable quietly starts spanning a
branch it never used to.

---

### 💡 The lesson

> **A control's scope is part of its meaning, and scope is invisible.**

Both pages would have passed a checklist asking *"is there a my-squad filter?"* — yes on both, wrong on both.
The question that finds it is *"what does it govern, and can the reader tell?"*

The general form, which this project keeps meeting from new directions: **a feature that works on some of a
surface is not a smaller version of one that works on all of it — it is a different, worse thing**, because it
teaches the reader that the answer depends where they look. ADR-155 met this as one fact known by only some
surfaces; here it is one control obeyed by only some sections.

### 🧪 Tests

**+3.** Signals has exactly one `filter_controls`, created before section 1, read by four sections, with name
resolution for the headlines; Team DNA has one checkbox, the ticker's old key gone, the lens bound before use;
and the DNA page survives an empty DNA map — verified by removing the binding and watching the `NameError`
come back.
