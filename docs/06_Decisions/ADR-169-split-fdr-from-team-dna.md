# Architectural Decision Record: Split FDR from Team DNA, and order the sidebar by use

**Decision ID:** ADR-169
**Date:** 2026-08-29
**Status:** ✅ **Accepted — owner's spec, built** (Sprint 229, 2026-08-29). **1578 tests, ruff clean.**
**Superseded By / Replaces:** Splits ADR-134's combined page; completes ADR-166's frequency ordering.
**No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner, after living with the reordered app:

> *"I think we could split Team DNA and FDR as 2 submenu items… and then the order of the sidebar
> Home - MySquad - FDR - Signals - Team DNA - Players - Trending - Help - Feedback - Admin."*

**On its face this reverses the week's work** — we went 12 pages → 8, and this goes 8 → 9. It doesn't, and the
owner's own ordering says why: **FDR sits third and Team DNA fifth, with Signals between them.** They shared a
*topic* (teams) but not a *moment*. The ticker is a weekly *"who has a good run?"*; the fingerprints are
occasional research. ADR-134 bundled them by subject; that put a frequent check behind the same click as an
infrequent one.

**Consolidation was never the goal — ordering by use was.** The same argument that folded Squad Lab *into*
My Squad pulls these apart.

---

### ✅ Decision

**Two pages, `📅 FDR` and `🧬 Team DNA`**, each cross-linking to the other, each owning its **own** squad lens.
That last part matters: ADR-164's rule is one lens *per page*, and the FDR half had been reading a checkbox
declared on the DNA half — legal while they shared a script, and a bug the moment they didn't.

**The sidebar is renumbered to the owner's order**, which reads as: your squad → the weekly checks (FDR,
Signals) → research (Team DNA, Players, Trending) → reference (Help, Feedback, Admin).

**⚠️ `/Team_DNA_and_FDR` is retired**, so a bookmark to it breaks — the cost ADR-149 named for
`/News → /Signals`. **Every other URL survives**: Streamlit's slug drops the number prefix, so
`4_My_Squad.py → 1_My_Squad.py` still serves `/My_Squad`. Renumbering is free; splitting is not.

### 🐛 A test that pinned a page name for the second time

`test_home_hero_box_consolidates_cta_and_nudges` asserted `"📅 **Fixtures**"` until ADR-134 renamed that page,
then `"🧬 **Team DNA & FDR**"` until this split — **breaking both times because the app improved**. It now
asserts the tour's *shape* (an emoji-led bullet per page, six or more) and leaves naming to the guard that
derives the list from `pages/`, which is the guard that actually catches drift.

Yesterday's fix loosened one literal in that test and left another. Removing a specific assertion is not the
same as removing the *habit* of asserting specifics.

### 🧪 Definition of Done

1. **1578 tests green**, ruff clean. Roughly 120 references renumbered; the combined page's tests routed to
   whichever half each actually exercises (ticker → FDR, fingerprints → Team DNA).
2. **Manual smoke** — nine pages in the owner's order, both halves render, each with its own lens.
3. **Docs** — this ADR, Home's tour, the Feedback picker, PROJECT_STATUS, a retro.

---

### 💡 The lesson

**"Fewer pages" was never the principle, and it is worth saying so out loud before the next request.** A week
of merging could easily calcify into a rule — *don't add sidebar entries* — that would have made this split
look like backsliding. It isn't: FDR earns its slot on frequency, exactly as Squad Lab lost its slot on
frequency. **The metric is how often you need the thing, and it can argue in both directions.**

The narrower one: **a page boundary is a scope boundary.** The FDR half read a variable the DNA half declared,
which was invisible while they shared a file and would have been a `NameError` the moment they didn't. Moving
code across a boundary makes implicit sharing explicit — usually by breaking it.
