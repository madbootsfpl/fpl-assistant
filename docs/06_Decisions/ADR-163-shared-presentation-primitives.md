# Architectural Decision Record: A stat strip and a banner that every page shares

**Decision ID:** ADR-163
**Date:** 2026-08-28
**Status:** ✅ **Accepted — owner-gated, built** (Sprint 220, 2026-08-28). **1549 → 1560 tests, ruff clean.**
⚠️ Preview published but **the owner could not open it** (404, twice); reviewed on Cloud instead.
**Superseded By / Replaces:** Fixes US-439 · US-443 · US-449 from the 2026-08-28 UX review. **No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Three items from the review looked unrelated and had one cause: **every page decided its own presentation**.

> *"On iPhone the xP for XI, Captain and Bench wraps on phone vs desktop… same with transfer flow and head to
> head on Leagues."* · *"Trending sub-tabs not consistent with other sub-tabs."* · *"Should the blue banner be
> more like the other MADBOOTS banners?"*

**The wrapping had been "fixed" once already, and that is the interesting part.** US-404 cut a five-metric row
to three because it *"slivered on mobile"*. That shrank the symptom and left the mechanism, so the moment two
more strips shipped this week — ADR-161's head-to-head and ADR-162's transfer flow — the owner hit it again.
One reported symptom turned out to be three instances of one defect.

---

### ✅ Decision

**1. A stat strip is rendered, not composed.** `st.columns` lays out server-side at a fixed ratio, so a
3-across row keeps its shape at any width: on a phone each column narrows until the *label* wraps and a strip
meant to be read at a glance becomes a tall ragged block. **No Python-side fix exists, because nothing on the
Python side knows the viewport.** CSS does — `flex-wrap` reflows the items, `clamp()` shrinks the numbers — so
`components.stat_strip_html` renders HTML. Three items ask for ~150px each and wrap when they can't have it.

**2. Trending uses a segmented control, like everything else.** Not only cosmetic: `st.tabs` builds *every*
panel on every run and hides all but one with CSS, so four leaderboards were computed to display one. The
consistent widget is also the cheaper one.

**3. The Signals banner is promoted as a lede, not by reordering.** The owner asked for the explained-exodus
banner nearer the top. The sections are ordered by **evidentiary strength** (ADR-149), and lifting one above
*Official FPL news* would break that ordering for everything beneath it. So a **🔴 Right now** block sits above
the ordered sections and section 2 keeps only the genuinely *unexplained* sell-offs, pointing upward — the
same fact appearing twice on one page reads as two findings.

**4. The banner restyle lands on Signals only.** Sixty-odd `st.info`/`st.warning` calls exist; converting them
on a styling preference would be a large blind change to error and empty states, and the owner asked for this
*"for discussion"*.

### ⚖️ The tradeoff, stated

`st.metric(help=…)` renders a **tappable "?"**; the strip's help is a `title` attribute — a hover tooltip on
desktop, nothing on touch. Accepted because that help explains a number which is already labelled, while the
wrapping made the number itself hard to read. Reversible if the owner disagrees.

### 🧪 Definition of Done

1. **Tests: +11, four rewritten.** The strip wraps and clamps rather than fixing a column count; labels,
   values, tones, escaping, empty input and a missing value; the banner's kind, defaults and trusted markup.
   Plus **two guards, each verified to fail on reintroduction**: a column-handle metric row anywhere outside
   Admin, and `st.tabs` on any page. Four tests were rewritten from `at.metric` (the *widget*) to the numbers
   on the page (the *contract*) — yesterday's lesson, applied.
2. **Manual smoke** — a preview at desktop and 320px. ⚠️ The owner could not open it (404 twice, artifact
   confirmed present in the gallery); reviewed on Cloud instead.
3. **Docs** — this ADR, the feedback log, PROJECT_STATUS, a sprint retro.

---

### 💡 The lesson

**A workaround that removes the symptom guarantees the defect comes back.** US-404 made the row smaller and
the row got bigger again the moment the app grew — twice in one week, in two new places, found by the owner
rather than by us. The question that would have caught it is *"is this the cause, or the count?"*, which is the
same question ADR-135 answered the hard way about widgets.

The corollary is why this sprint is worth its size: **three unrelated-looking complaints were one cause.** Had
they been worked as three tickets, there would now be three per-page fixes and the fourth strip would break
again. Batched feedback is worth more than a stream of it, because only the batch shows the shape.
