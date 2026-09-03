# Sprint 241: The accent belongs to the theme (ADR-180)

**Dates:** 2026-09-03
**Status:** ✅ Complete — ADR-180. **1727 → 1731 tests, ruff clean.**
✅ **Owner-verified same day: the accent renders** — purple on the Tool nav and the answer selector, in
dark mode, from his own screenshots.

> **Owner**, on the deployed app **in dark mode**, with four screenshots: *"Lot of real estate used in Lab
> when new build. Lots of inconsistency with colours vs the style guide, should be purple. Can't really see
> the GW1-3 numbers on the pitch, make the white maybe. Some truncation across the tabs."*

Two of those were unambiguous defects and shipped first (`8284b3e`). This is the other two.

---

### ⭐ The lesson — a constraint in an ADR is a fact about a version, not a law

`brand.nav_css` paints the purple one widget at a time, on five containers across five pages. It exists in
that shape for one reason: **ADR-114** (2026-08-17) found that *any* `[theme]` block pinned the theme —
`base` defaulting to light — which removed the viewer's Light/Dark/System toggle.

Re-run today on Streamlit 1.61.1, **that is no longer true**, because of a feature that did not exist when it
was written: **per-mode `[theme.light]` / `[theme.dark]` sections.**

Checked at three levels, the middle one decisive:

1. **Config** — `theme.base` resolves to `None`.
2. **The wire format** — the theme reaches the browser as a `CustomThemeConfig` with nested `light`/`dark`
   messages. With only the per-mode sections set, *the top-level message — the one carrying `base` — has no
   fields at all.* There is nothing there to pin with.
3. **A local run** served the app with the block in place.

So two config lines now do what five stylesheets were doing, in **both** themes, for widgets nobody has
written yet.

> **I was one step from writing a fourth batch of scoped CSS** on the strength of a seventeen-day-old finding
> about a library that had changed underneath it. ADR-157's rule — *re-run a remembered measurement before it
> justifies work* — has now paid for itself twice.

**ADR-114's reasoning is preserved, not overturned.** *Theme-following beats a brand accent* was right and
still is; it simply stopped being a trade-off. And its finding is now **a test**: re-introduce `base` and the
suite fails, naming the toggle it would take away.

---

### 🔧 Also shipped

**The Tool nav joins the primitive** — the one selector ADR-176 never wrapped, which is why it rendered
narrower than every other row *and*, in dark mode, in Streamlit's red.

**`nav_css` keeps the layout and hands back the colour.** Keeping both would clash: the CSS can hard-code
only one shade, and the theme gives dark mode `PURPLE_LT`.

**The Lab's eight constraints fold into one expander.** The line is not *"they look advanced"* — it is
checkable: **every one defaults to no constraint**, so on the default path they provably did not affect the
squad rendered beneath them. A count in the expander's label means a *set* constraint can never hide, which
is the failure mode an expander invites.

---

### 🔬 What the build turned up

**Removing a rule found something depending on it.** Stripping colour from `nav_css` would have taken the
*Apply this transfer* button's fill with it. Fixed properly rather than re-exempted: it is now
`type="primary"`, which Streamlit colours **from the theme**.

> **A hand-painted "primary" button was describing itself as primary in CSS while telling Streamlit it was
> ordinary.** The dependency was the wrong shape, and only removing the rule exposed it.

**And a guard I wrote contained a no-op assertion.** The Lab test ended `assert labels or True` — a hedge
around AppTest's inconsistent expander support, which asserts precisely nothing. Replaced with an **AST
check**: the eight keyed widgets must sit inside the expander's body, the essentials outside it. A mutation
lifting one control back into the open proves the difference — a string grep would have passed.

> **A hedge is not a weaker assertion; it is the absence of one.**

Four of the last five sprints have surfaced a guard that passed while protecting nothing. This is the most
brazen form: visible in the diff, written by me, in a sprint whose subject is guards that do not work.

---

### 🧪 Seven mutations, all caught

A colour rule creeping back into the primitive · dark mode left on Streamlit red · a top-level `primaryColor`
· **`base` pinning the theme again** · the top nav dropping the primitive · a hidden constraint gaining a
biting default · a constraint lifted out of the expander.

The clean suite was re-run against a recorded baseline after every restore.


---

### 🔁 A follow-up, same day: the truncation fix was not enough

`8284b3e` trimmed the segment padding. The owner came back with it still broken — **My … | DNA | Lea… | Lab**
— because trimming padding left `flex: 1 1 0` and `min-width: 0` in place, and a segment could still be
squeezed below its own text.

> **Equal width and legible labels are not both achievable at phone width, and I optimised the wrong one.**

The floor is now `min-width: max-content`: segments still grow to fill the row, they cannot shrink past their
label, and when four will not fit the row **wraps**. A taller nav is worse than a shorter one and better than
an unreadable one — which is the trade the first attempt got backwards, and said so in its own comment.

⭐ **The first fix treated a symptom (too little space); the defect was a rule (a segment may be narrower than
its own label).** Buying characters works until the next label or the next screen width. A floor holds for
both. Three mutations, all caught.
