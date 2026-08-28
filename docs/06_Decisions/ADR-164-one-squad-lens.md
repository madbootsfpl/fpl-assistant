# Architectural Decision Record: One squad lens per page, not one per section

**Decision ID:** ADR-164
**Date:** 2026-08-28
**Status:** ✅ **Accepted — owner-gated, built** (Sprint 221, 2026-08-28). **1560 → 1563 tests, ruff clean.**
**Superseded By / Replaces:** Fixes US-441 · US-442 from the 2026-08-28 UX review. Extends US-407b's filter.
**No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

> *"Team DNA should have option for my squad only."* · *"Signals should have a global option for my squad only
> related news/signals etc."*

Both pages **already had** a my-squad control. That is what made them worse than pages with none:

* **Team DNA** — the checkbox sat on the *ticker*, halfway down. The 20-club DNA scan **above** it ignored a
  control the reader had already set, so one page answered *"my squad"* in its lower half and *"the league"* in
  its upper half, with nothing saying which was which.
* **Signals** — the filter was created *inside section 1*. Section 4 reused its result by coincidence of scope;
  sections 2 and 3 ignored it. Two of four.

**A lens that covers part of a page is worse than no lens.** A quiet section might mean *"nothing about your
squad"* or *"not filtered"*, and the reader cannot tell which — so they learn to distrust all of it.

---

### ✅ Decision

**1. One control, above everything it governs.** On Signals the filter is created before section 1; on Team DNA
the checkbox sits above the scan and the ticker reads the *same* variable rather than owning a second.

**2. It reaches the headlines too — by a different mechanism, because they are a different kind of thing.**
Sections 1, 2 and 4 are player rows, so `apply_filter` matches on id. **A headline is a sentence**, with
nothing for a row filter to match. It is resolved with ADR-152's name index — the same longest-match-first
resolver the extraction uses — so a headline about *Reece James* does not surface for an owner of *James
Maddison*. Reusing that resolver rather than writing a second one is the point: name matching is the part of
this codebase most likely to be subtly wrong, and it has already been got right once.

**3. The page says when it is filtered**, and counts what it hid (*"6 of 47 headlines mention one of your
players"*). A filter you can forget you set is how a page starts lying quietly.

**4. Disabled, not hidden, without a squad** — with the reason in the tooltip. A control that vanishes teaches
nothing; a disabled one that explains itself teaches where to go.

### 🐛 Found while building

Unifying the Team DNA control introduced a **`NameError`**: the checkbox is created inside `if _all_dna:` but
the ticker below reads it unconditionally, so a snapshot with no DNA to draw would have crashed the page. Bound
`False` before the block, and there is a test that fails with the original `NameError` if the binding is
removed. Worth recording because the *consolidation itself* created the risk — one variable now spans two
sections that used to be independent.

### 🧪 Definition of Done

1. **Tests: +3.** Signals has exactly one `filter_controls`, created before section 1, read by at least four
   sections, plus name resolution for the headlines; Team DNA has exactly one checkbox with the ticker's old
   key gone and the lens bound before use; and the DNA page survives an empty DNA map — verified by removing
   the binding and confirming the `NameError` returns.
2. **Manual smoke** — both pages render filtered and unfiltered.
3. **Docs** — this ADR, the feedback log, PROJECT_STATUS, a sprint retro.

---

### 💡 The lesson

**A control's scope is part of its meaning, and scope is invisible.** Both pages passed a checklist that asked
*"is there a my-squad filter?"* — the answer was yes on both, and both were wrong. The question that finds this
is *"what does it govern, and can the reader tell?"*

The general form, which this project keeps meeting from different directions: **a feature that works on some of
the surface is not a smaller version of one that works on all of it — it is a different, worse thing**, because
it teaches the reader that the answer depends on where they look. ADR-155 met it as one fact known by some
surfaces; here it is one control obeyed by some sections.
