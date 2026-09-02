# Sprint 237: One navigation primitive (ADR-176)

**Dates:** 2026-09-02
**Status:** ✅ Complete — ADR-176. **1702 → 1706 tests, ruff clean.**

> **Owner:** *"You know what I am going to ask next — can we add this structure and layout to all our pages?
> Success brings more work!"*

---

### 🔧 What shipped

`brand.nav_css(key)` joins the stat strip and the banner as a shared presentation primitive (ADR-163). **Five**
pages call it — My Squad, Players, Trending, Team DNA, FDR — each with its own container key.

Surveying first was what made this small: **four pages already had ADR-175's structure** and were simply
wearing Streamlit's default clothes. They needed the primitive, not a redesign.

Chrome cut along the way: Players' *"🎯 Looking for **who to buy**? The **Radar** view below…"* caption, which
signposted an option in the selector directly beneath it; and FDR's two labelled controls, now one row.

---

### 💡 The lesson

> **A page can be made consistent and worse in the same edit.**

📡 **Signals was deliberately excluded.** It is the page that looks *most* like it wants this pattern — four
numbered sections, no selector, eighteen blocks — and it is the one page that must not have it. ADR-150 orders
it by **evidentiary strength** (official news → an unexplained exodus → media → crowd chatter) and states that
the ordering **is** the answer to the risk. Behind a selector a reader could open *"crowd chatter"* without
ever seeing that it sits below *"official news"*: four equal choices where there is a ladder.

So the guard that matters here is not the one protecting the purple. It is
`test_signals_is_not_behind_a_selector`, which asserts Signals never adopts the primitive **and** that its
four sections still read in order — with the reasoning in the docstring, because the next person to make this
page "consistent with the others" will be doing something that looks like tidying.

**The first three guards protect a look. The fourth protects a claim.**

---

### 🧭 On the framing

The owner corrected me mid-sprint, and it is worth recording because it changes how the previous two sprints
read:

> *"You did not make a mistake, we are iterating, an agile framework… the preview has undoubtedly made the
> greatest contribution and you have now turned that into a solution."*

ADR-175 went through two revisions after the owner compared the build against the preview. I had written that
up as drift I should have caught. His framing is that the preview → build → compare → revise loop *is* the
method, and the preview is the artefact that made it work — which is a better description of what happened
than "I missed it twice", and the reason the same loop was used again here before a line was written.

---

### 🧪 Tests

**+4**, each mutation-checked: a page hand-rolling the CSS fails · a second definition outside `brand.py`
fails · two pages sharing a container key fails · **Signals adopting the selector fails**.
