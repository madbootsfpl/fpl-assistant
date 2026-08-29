# Sprint 229: Split FDR from Team DNA, and order the sidebar by use (ADR-169)

**Dates:** 2026-08-29
**Status:** ✅ Complete — ADR-169. 1578 tests, ruff clean.

> **Owner:** *"Split Team DNA and FDR as 2 submenu items… order: Home - MySquad - FDR - Signals - Team DNA -
> Players - Trending - Help - Feedback - Admin."*

---

### 🔧 What shipped

```
My Squad · FDR · Signals · Team DNA · Players · Trending · Help · Feedback   (+ Admin)
```

Two pages instead of one, each cross-linking to the other and each owning **its own squad lens** — ADR-164's
rule is one lens per page, and the FDR half had been reading a checkbox declared on the DNA half. Legal while
they shared a script; a bug the moment they didn't.

**This looks like a reversal of the week and isn't.** We went 12 → 8; this goes 8 → 9. But the owner's own
ordering explains it: FDR third, Team DNA fifth, Signals between them. They shared a *topic*, not a *moment* —
the ticker is a weekly check, the fingerprints are research.

**URLs:** renumbering is free (Streamlit's slug drops the number prefix, so `/My_Squad` survives moving from
`4_` to `1_`). The split retires `/Team_DNA_and_FDR`, which does break a bookmark.

---

### 🐛 The same test pinned a page name for the second time

`test_home_hero_box…` asserted `"📅 **Fixtures**"` until ADR-134 renamed that page, then
`"🧬 **Team DNA & FDR**"` until this split — **breaking both times because the app improved.** It now asserts
the tour's *shape* and leaves naming to the guard that derives the page list from the filesystem.

I loosened one literal in that test yesterday and left another sitting beside it.

---

### 💡 The lesson

> **"Fewer pages" was never the principle.**

A week of merging could calcify into a rule — *don't add sidebar entries* — that would make this split look
like backsliding. It isn't. FDR earns its slot on frequency exactly as Squad Lab lost its slot on frequency.
**The metric is how often you need the thing, and it argues in both directions.**

> **A page boundary is a scope boundary.**

The FDR half read a variable the DNA half declared — invisible while they shared a file, a `NameError` the
moment they didn't. Moving code across a boundary makes implicit sharing explicit, usually by breaking it.

### 🧪 Tests

1578 green. ~120 references renumbered, and the combined page's tests routed to whichever half each actually
exercises — ticker to FDR, fingerprints to Team DNA.
