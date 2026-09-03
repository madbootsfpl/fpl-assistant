# Architectural Decision Record: The accent belongs to the theme

**Decision ID:** ADR-180
**Date:** 2026-09-03
**Status:** ✅ **Accepted — built** (Sprint 241, 2026-09-03). **1727 → 1731 tests, ruff clean.**
⏳ **One thing remains owner-verified: that the accent actually renders on Cloud.** No browser here.
**Superseded By / Replaces:** **Reverses [ADR-114](./ADR-114-brand-token-foundation.md)'s removal of the `[theme]`
block** on re-measurement, and **narrows [ADR-176](./ADR-176-one-navigation-primitive.md)**: `nav_css` keeps
the layout it invented and hands the colour back to the platform.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Owner feedback with four screenshots, on the deployed app **in dark mode**:

> *"Lot of real estate used in Lab when new build. Lots of inconsistency with colours vs the style guide,
> should be purple. Can't really see the GW1-3 numbers on the pitch, make the white maybe. Some truncation
> across the tabs."*

Two of those were unambiguous defects and shipped immediately (`8284b3e`): the per-gameweek line was **dark
green text on a green pitch**, and `flex: 1 1 0` plus Streamlit's own padding truncated *"This week"* into
*"This …"*. This ADR is the other two.

#### Why the colours are wrong, and why it is not a small thing

**He is in dark mode**, and every control the app has not hand-styled falls back to Streamlit's default
**red**: the top-level Tool nav (My Squad · DNA · Leagues · Lab), the Build-mode radio, checkboxes, the
budget slider, multiselect chips. The purple only appears where ADR-176's `nav_css` is explicitly applied —
**five containers on five pages**.

That is not a gap to fill with a sixth. It is the shape of a design that put the accent in the wrong layer.

#### Decision Drivers

- **Driver 1 — the accent should be declared once, not painted per widget.** The current approach scales with
  the number of controls, which is the wrong axis.
- **Driver 2 — the viewer's Light/Dark/System toggle must survive.** This is ADR-114's whole point and it
  still stands. Any change has to be measured against it, not asserted past it.
- **Driver 3 — the Lab's default path should not pay for its advanced path.** Eight controls precede the
  answer, and **every one of them is inert unless touched.**

---

### 🔬 The measurement — ADR-114's blocker is gone

ADR-114 (2026-08-17) removed a `[theme]` block after finding:

> *"**any** `[theme]` in config.toml *pins* the theme — `base` defaults to light, so it forced light-only and
> removed the user's Light/Dark/System toggle."*

**Re-run today on Streamlit 1.61.1, that is no longer true — and the reason is a feature that did not exist
when it was written.** Streamlit now has **per-mode theme sections**:

```
[theme.light] primaryColor = "#8B2FC9"
[theme.dark]  primaryColor = "#B45CF0"

    theme.base = None            ← not pinned
```

Checked at three levels, each stronger than the last:

**1. Config.** `theme.base` resolves to `None`. (A *bare* `[theme] primaryColor` also leaves it `None` now —
so that behaviour changed too, independently of the per-mode sections.)

**2. The wire format**, which is what actually decides it. `app_session` sends the theme as a
`CustomThemeConfig` with **nested `light` and `dark` messages**. With only the per-mode sections set:

```
fields set on the TOP-LEVEL theme: (none)
    light.primary_color = #8B2FC9
    dark.primary_color  = #B45CF0
```

**The top-level message — the one carrying `base` — is empty.** There is nothing there to pin the theme
with, while each mode still receives its own accent.

**3. A local run** on the real config served HTTP 200 with the block in place.

⚠️ **What is *not* verified, stated plainly: the rendered pixel.** The Chrome extension is not connected in
this environment, so the final *"the radio is purple"* is the owner's reboot, not mine. Everything above says
the colour reaches the frontend correctly configured; only a browser can say it is painted.

> ⭐ **This is ADR-157's rule earning its keep: re-run a remembered measurement before it justifies work.** I
> was one step from writing a fourth batch of scoped CSS on the strength of a seventeen-day-old finding about
> a library that had changed underneath it. **A constraint recorded in an ADR is a fact about a version, not
> a law.**

---

### 💡 Options Considered

#### Option 1: Per-mode `primaryColor`, and `nav_css` gives the colour back *(Chosen)*
* **Description:** two config lines set the accent for both themes; `nav_css` keeps its full-width-segments
  layout and drops its colour rule.
* **Pros:**
  - ✅ Every control — radio, checkbox, slider, multiselect, segmented — turns purple at once, **in both
    themes**, including ones nobody has thought about yet.
  - ✅ **Dark mode gets its own shade.** `PURPLE` at `#8B2FC9` is dim on a near-black ground; `PURPLE_LT`
    `#B45CF0` already exists in `brand.py` for exactly this ("legible on the card band's dark ground").
  - ✅ Removes a rule rather than adding one.
* **Cons:**
  - ❌ If the theme somehow does not apply on Cloud, the purple is gone everywhere rather than just absent
    from new controls. **Mitigation: one line restores it, and the owner's reboot is the check.**

#### Option 2: Keep `nav_css`'s colour as well, as belt and braces
* **Cons:**
  - ❌ **They would visibly disagree in dark mode.** `nav_css` hard-codes `#8B2FC9`; the theme gives dark mode
    `#B45CF0`. The segmented controls would be a different purple from everything around them.
  - ❌ *"One rule written twice always drifts"* (ADR-140) — the failure this project has already paid for.

#### Option 3: Extend the scoped CSS to cover radios, checkboxes and sliders
* **Cons:** ❌ It is the current approach, continued. Every new widget type is a new rule, and the list is
  Streamlit's, not ours.

---

### 🎯 Decision & Justification

**1. The accent moves to `config.toml`, per mode.** `[theme.light] primaryColor` = PURPLE,
`[theme.dark] primaryColor` = PURPLE_LT. ADR-114's *reasoning* is preserved intact — **theme-following beats
a brand accent** — and it simply is no longer a trade-off we have to make.

**2. `nav_css` keeps its layout and loses its colour.** It was always two things bolted together: equal
full-width segments (ours, and the theme cannot do it) and a purple active state (the platform's job). It
keeps the first. ADR-176's guard, which asserts the purple is defined once, is rewritten to assert the
*layout* is — because that is now the thing the primitive owns.

**3. The Tool nav joins the primitive.** The top-level My Squad · DNA · Leagues · Lab switch is the one
selector ADR-176 never wrapped, which is why it is red in the screenshot and narrower than every other row.

**4. The Lab's eight inert controls move into one expander.** *Low-cost · Premium · Differentials · Must
include · Must exclude · Declare bench · Ignore expected minutes · Include injured/suspended.*

The line is not "advanced-looking" — it is checkable: **every one of them defaults to no constraint**
(`0`, `[]`, `False`). They cannot change the built squad unless touched, so on the default path they are
eight controls' worth of height above an answer they did not affect. The essentials stay visible: *Start from
· Budget · Objective · Build mode · Name.*

---

### 🔬 Found at build time

**1. The *Apply this transfer* button would have lost its fill.** `nav_css`'s `primary_button` block painted
it purple, and stripping colour from the primitive took that with it. Fixed properly rather than
re-exempted: the button is now `type="primary"`, which Streamlit colours **from the theme** — so it follows
the same single declaration and is correct in both modes. The CSS hook keeps only the full width.

⭐ **Removing a rule found a second thing depending on it, and the dependency was the wrong shape anyway.**
A hand-painted "primary" button was always describing itself as primary in CSS while telling Streamlit it
was ordinary.

**2. A guard I wrote contained a no-op assertion.** The Lab test ended `assert labels or True` — a hedge
around AppTest's inconsistent expander support, which asserts nothing at all. Replaced with an **AST check**:
the eight keyed widgets must sit *inside* the expander's body and the essentials outside it. String-grepping
the source would have passed with every control still at the top level, which the mutation below proves.

> **A hedge is not a weaker assertion; it is the absence of one.** Four of the last five sprints have turned
> up a guard that passed while protecting nothing, and this is the most brazen form of it — visible in the
> diff, written by me, in a file whose whole subject is guards that do not work.

#### ✅ Mutation results — seven, each reverted alone, restore verified against a recorded baseline

| mutation | caught |
|---|---|
| a colour rule creeps back into the primitive | ✅ |
| dark mode loses its accent (light-only config) | ✅ |
| a top-level `primaryColor` is added back | ✅ |
| `base` pins the theme again — **ADR-114's original finding** | ✅ |
| the top nav stops calling the primitive | ✅ |
| a hidden constraint gains a **biting** default | ✅ |
| one constraint is lifted back out of the expander | ✅ *(the AST check; a string grep would not have seen it)* |

The fourth is worth keeping deliberately: **ADR-114's finding is now a test.** If a future edit re-introduces
`base`, the suite says so and names the toggle it would remove — the ADR's reasoning outlives the
circumstance that produced it.

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:**
  - One declaration replaces a growing list of per-widget rules, and covers widgets not yet written.
  - Dark mode stops looking like a different product.
  - The Lab's first screen becomes the five decisions that matter.
* **Negative Impact / Trade-offs:**
  - The accent now depends on a platform feature rather than our own CSS. That is the right dependency, and
    it is a reversible one.
  - An expander is a click. Accepted: it is a click on the path that was already the minority one.
* **Risks & Mitigations:**
  - **Risk:** the theme does not apply on Community Cloud (a different Streamlit build). **Mitigation:** the
    owner's reboot is the check, and restoring `nav_css`'s colour rule is one line. Recorded here so the
    fallback is not re-derived.
  - **Risk:** `#B45CF0` is too light on dark. **Mitigation:** it is already the brand's answer for a dark
    ground (`brand.py`), not a new colour invented here.
  - **Risk:** someone re-adds a colour rule to `nav_css` for a page that "looks wrong". **Mitigation:** a
    guard asserts the primitive carries no colour, with the dark-mode clash as the reason.

---

### 🛠 Implementation & Migration
* **Components Affected:** Config, Code (`brand.py`, `pages/1_My_Squad.py`, `views/squads.py`), Tests, Docs
* **Action Items:**
  - [x] `[theme.light]` / `[theme.dark]` `primaryColor` in `.streamlit/config.toml`, with ADR-114's history
        rewritten in place rather than deleted
  - [x] `nav_css` drops its colour rule; keeps layout
  - [x] Guard: `nav_css` contains **no** colour — and the reason (the dark-mode clash) is in the docstring
  - [x] Guard: the config sets the accent for **both** modes and sets **no** `base`
  - [x] Wrap the Tool nav in `st.container(key="ms_tool_nav")` + `brand.nav_css`
  - [x] Fold the eight inert Lab controls into **⚙ Constraints (optional)**
  - [x] Guard: every control in the expander is inert by default, so the default path is unaffected
  - [x] **Mutation-test every new guard**, clean suite re-run between mutants
  - [ ] Owner reboot → confirm the accent renders (the one thing not verifiable here)

#### ✅ Always
- [x] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

#### 🧭 If this ADR renames/moves/merges/retires a user-facing surface
The Lab's eight constraint controls **move** behind an expander; none is renamed or removed.
- [x] Checked — no copy names the Lab's constraint controls as visible.
- [x] Nothing for `RETIRED` — no phrase is retired, only relocated.

---

### 🔄 Review & Reconsideration
* **Review Date:** 2026-10
* **Triggers for Reconsideration:**
  - [ ] The accent does not render on Cloud — fall back to `nav_css`'s colour rule, per the risk above
  - [ ] Streamlit changes theme handling again — **re-measure, do not consult this ADR's numbers**
  - [ ] Testers hunt for a Lab constraint they used to see

---

### 🔗 References & Related Artifacts
- **Reverses:** [ADR-114](./ADR-114-brand-token-foundation.md) — on measurement, with its reasoning preserved
- **Narrows:** [ADR-176](./ADR-176-one-navigation-primitive.md) — the primitive keeps layout, not colour
- **Method:** ADR-157 — *re-run a remembered measurement before it justifies work*
- **Shipped separately:** `8284b3e` — the invisible per-gameweek line and the truncated nav labels
