# Architectural Decision Record: One navigation primitive

**Decision ID:** ADR-176
**Date:** 2026-09-02
**Status:** 🚧 **Proposed — preview before code.**
**Superseded By / Replaces:** Extends **ADR-163** (shared presentation primitives) from the stat strip and
banner to the *navigation*. Applies **ADR-175**'s golden-page shape to four more pages. Respects **ADR-114**
(the brand purple lives where we control it, never the widget theme) and **ADR-150** (Signals is excluded,
and that is a decision rather than an omission).
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

> *"Can we add this structure and layout to all our pages?"*

ADR-175 gave My Squad a shape: **title → tabs → one line of facts → the value → one styled selector → the
chosen panel**, with a purple, full-width selector and chrome that has to earn its line.

Surveying the rest, **four pages already have that structure and are wearing Streamlit's default clothes:**

| page | its selector | chrome above it |
|---|---|---|
| **Players** | 6 views (Pool · Value · Card · Radar · Scout · History) | a page caption, **plus a second caption signposting the Radar view that is visible in the selector directly below it** |
| **Trending** | 4 boards | a page caption + a legend |
| **Team DNA** | "Sort the league by" | a caption, a checkbox, a labelled control |
| **FDR** | "Sort by" (new today) | a caption, a **labelled** weeks slider, a checkbox, then the sort — four stacked controls before the grid |

None of them needs a redesign. They need the primitive My Squad now has, and the same discipline about lines.

---

### ✅ Proposed Decision

**1. One shared helper, not five copies.** `brand.nav_css(key)` joins `render_stat_strip` and the banner as a
presentation primitive (ADR-163). The purple, full-width, equal-segment selector is defined **once** and
called by each page.

**This is the whole reason to write an ADR rather than just do it.** The CSS currently lives inline in
`1_My_Squad.py`; pasting it into five files is precisely *"one rule written twice always drifts"* — ADR-140's
lesson, which this project has since paid for in stale captions, a stale ADR index and a stale runbook. **A
test asserts no page hand-rolls the selector CSS.**

⚠️ It stays **scoped CSS on a keyed container**, never a theme. ADR-114 tried `primaryColor` in
`config.toml` and reverted it: any `[theme]` block *pins* the theme, defaults `base` to light, and takes the
viewer's Light/Dark/System toggle away. Theme-following beats a purple accent.

**2. The chrome pass, page by page.** Each keeps its content; each loses lines that explain the page you are
on or point at something already visible:

* **Players** — the *"🎯 Looking for **who to buy**? The **Radar** view below…"* caption goes. It signposts an
  option **in the selector immediately beneath it**.
* **FDR** — the weeks slider, the squad checkbox and the sort share one row instead of three, with labels
  collapsed.
* **Team DNA** — checkbox and sort share a row.
* **Trending** — the legend folds under the board it explains.

**3. Signals is excluded, and that is the interesting decision.**

ADR-150 orders that page by **evidentiary strength** — official FPL news, then an unexplained exodus, then
media headlines, then crowd chatter — and says plainly:

> *the page descends by evidentiary strength, and that ordering **is** the answer to the risk.*

Put those four behind a selector and a reader can open *"crowd chatter"* without ever seeing that it sits
below *"official news"*. **The stacking carries the honesty**; it is not a layout that was never tidied. The
one page that looks most like it needs this pattern is the one page that must not have it.

---

### 🔀 Alternatives Considered

- **Apply it everywhere, Signals included.** Rejected above — it would convert an evidence ladder into four
  equal choices, which is the claim ADR-150 exists to avoid making.
- **Copy the CSS into each page.** Rejected: five copies of a rule that will be edited once and then disagree.
- **Set the theme properly and drop the CSS.** Rejected — ADR-114 measured the cost: it pins light mode for
  every viewer.
- **Do nothing; the pages work.** Rejected, but honestly: they *do* work. This is a consistency and density
  change, and its value is that four pages stop looking like a different app from the one the owner just
  approved.

---

### 🧭 Consequences

**Positive** — one definition of the app's main control; four pages gain the shape the owner signed off;
chrome that explains the page you are on goes; the primitive makes the *next* page free.

**Negative / risks (mitigations)** — scoped CSS depends on Streamlit's DOM, which can change under us
(*mitigation:* it degrades to the default widget, which is what those pages have today — a broken selector
is not a possible outcome). More surface changing in one week (*mitigation:* the owner is holding My Squad
for tester feedback, and this deliberately does not touch it, so that feedback stays about the page it is
about).

---

### 📏 How this gets judged

**Not by line count.** By two things: the four pages look like the same app as My Squad, and **Signals still
reads top to bottom** — because the moment it does not, this ADR has done harm rather than good.
