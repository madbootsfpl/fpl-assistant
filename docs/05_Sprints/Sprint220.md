# Sprint 220: One strip, one banner, one widget (ADR-163 — US-449 · US-439 · US-443)

**Dates:** 2026-08-28
**Status:** ✅ Complete — ADR-163. 1549 → 1560 tests, ruff clean.

> **Owner:** *"On iPhone the xP for XI, Captain and Bench wraps… same with transfer flow and head to head."* ·
> *"Trending subtabs not consistent."* · *"Could the blue banner be more like the other MADBOOTS banners?"*

Three items from the UX review that looked unrelated and had one cause: **every page decided its own
presentation.**

---

### 🔧 What shipped

**A shared stat strip**, rendered rather than composed. `st.columns` lays out server-side at a fixed ratio, so
a 3-across row keeps its shape at any width and on a phone the labels wrap. No Python-side fix exists —
nothing in Python knows the viewport. `flex-wrap` reflows, `clamp()` shrinks the numbers. Now used by My
Squad's XI/Captain/Bench, the Leagues transfer flow and the head-to-head.

**Trending moved to a segmented control.** `st.tabs` builds every panel each run and hides all but one, so
four leaderboards were computed to show one — the consistent widget is also the cheaper one.

**The Signals lede.** The explained-exodus banners are promoted to a **🔴 Right now** block at the top — but as
a *lede, not a reorder*: the sections are ordered by evidentiary strength (ADR-149) and lifting one above
*Official FPL news* would break that ordering for everything below. Section 2 now holds only the genuinely
unexplained sell-offs and points upward.

---

### 💡 The lesson

> **A workaround that removes the symptom guarantees the defect comes back.**

US-404 already "fixed" this wrapping by cutting a five-metric row to three because it *slivered on mobile*.
That shrank the symptom and left the mechanism — so it returned the moment the app grew, twice in one week, in
the two strips shipped for ADR-161 and ADR-162, and was found by the owner rather than by us. The question
that would have caught it is *"is this the cause, or the count?"* — which is what ADR-135 answered the hard way
about widget counts.

> **Three unrelated-looking complaints were one cause.**

Worked as three tickets there would now be three per-page fixes and the fourth strip would break again. Only
seeing the batch showed the shape.

### 🧪 Tests

**+11, four rewritten.** The strip wraps and clamps rather than fixing a column count; labels, values, tones,
escaping, empty input, a missing value; the banner's kind, defaults and trusted markup. **Two guards, each
verified to fail on reintroduction** — a column-handle metric row outside Admin, and `st.tabs` on any page.
Four tests moved from asserting `at.metric` (the widget) to the numbers on the page (the contract).
