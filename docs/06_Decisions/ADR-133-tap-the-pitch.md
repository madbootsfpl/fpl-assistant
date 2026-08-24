# Architectural Decision Record: Tap a shirt to select a player

**Decision ID:** ADR-133
**Date:** 2026-08-24
**Status:** ✅ **Accepted — owner-approved, built** (Sprint 185). ⚠️ **One claim below was wrong and is
corrected in the follow-ups** — the build proved it. The Cloud deploy check is still outstanding.
**Superseded By / Replaces:** Delivers the "My Squad v2 — tap-the-pitch" that ADR-108 deferred as a *committed
next*. Extends ADR-084 (the CSS pitch) without redesigning it.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Testers keep describing the same gesture: *"FFH pops a menu on **clicking** a player."* ADR-108 shipped the
**panel** — one selection → card + captain + substitute — as the achievable shape, explicitly *"a foundation,
not a stopgap"*, and deferred the tap itself with a written trigger:

> Ship the panel, watch the testers; if *"I want to tap the shirt"* stays the top ask, that's the green light.

**It has.** The owner also cites fplapex's solver app as the interaction to match, and as a differentiator
against Fantasy Football Hub.

ADR-108 deferred on two grounds, both of which a spike (`spikes/185-tap-the-pitch/`) has now tested:

1. it *"introduces a front-end build toolchain to a pure-Python project"*, and
2. *"the golden page loses AppTest coverage"*.

---

### 🔬 What the spike established

**No toolchain.** `st-click-detector` (PyPI 0.1.3) ships a **pre-built** frontend and is ~30 lines of Python
around `components.declare_component(path=…)`. Installing it pulls **one package and zero new transitive
dependencies**. Its API is exactly the shape needed: pass HTML, get back the id of the anchor clicked. MIT
licensed (the wheel carries the licence even though its metadata says `UNKNOWN`).

**ADR-084's iframe objection does not carry over.** That ADR rejected `components.v1.html` over *"a fixed-height
iframe that can't auto-size"*. This component's bundle calls `setFrameHeight` and sizes to its content.

**The pitch survives whole** — no sanitiser, so the HTML passes through raw. Against the live squad:

```
kit cards: 15 · anchors injected: 15 · ids match the squad: True · all ids resolve: True
pitch <style> survives: True · hover cards survive: 18 popovers · payload: 25,297 chars
```

**The click works.** Owner tapped Virgil on the spike app; it returned him.

**Cloud is proven, by precedent.** `streamlit-cookies-controller` — live in production for "remember me",
owner-verified on Safari and Chrome — uses the *identical* mechanism, `declare_component` with a static
frontend build. The component-serving path already works on this deploy.

---

### ✅ Proposed Decision

**Tapping a shirt selects that player — as an *additional* input, never a replacement.**

**1. The dropdown stays. Permanently.** (Owner-agreed.) This is the decision that dissolves ADR-108's second
objection rather than accepting it: AppTest keeps driving the selectbox exactly as it does today, so **the
golden page loses no coverage at all**. Keyboard and screen-reader users keep a working path. And if the
component ever fails — an upgrade, a Cloud quirk, a blocked iframe — the page degrades to precisely today's
behaviour instead of becoming unusable. The tap is strictly additive.

**2. Split `pitch_html()` out of `render_pitch`.** It currently writes straight to `st.markdown` and returns
nothing, so there is no HTML to hand a component. Build → render is a separation the module wants regardless;
the spike had to monkeypatch around it, which production must not.

**3. Emit the anchor in `_kit_html`, not by regex.** Each kit card becomes
`<a href="#" id="{player_id}" class="kit-a">…</a>`. The spike's regex was fine for answering *"does it work?"*
and is not fine for shipping.

**4. One selection state, two ways to set it.** The tap writes the same `session_state` key the selectbox
uses, so the ADR-108 panel is reused **entirely unchanged** — which is what that ADR meant by ~90% already
built. Only the *input* is new.

---

### 🔀 Alternatives Considered

- **A hand-rolled static-HTML component** (`declare_component(path=…)` + a `postMessage` contract we write).
  No dependency, but it rides Streamlit's *internal* component protocol, which is undocumented and free to
  change. Rejected while a maintained-enough MIT package does the same job.
- **A full React component + npm.** What ADR-108 feared. Unnecessary — nothing here needs a build.
- **Rebuild the pitch from native widgets** (image buttons in a column grid). Zero JS and fully AppTestable,
  but it means abandoning the CSS pitch ADR-084 deliberately chose for its look. Kept as the fallback of last
  resort if the dependency ever becomes untenable, not as the plan.
- **Replace the dropdown with the tap.** Rejected — this is the choice that would have made ADR-108's coverage
  objection real.

---

### 🧭 Consequences

**Positive** — delivers the most-asked-for interaction and the one visibly differentiating gesture against FFH;
reuses the entire ADR-108 panel; costs one dependency and no build tooling; strictly additive, so the failure
mode is "the tap stops working", never a broken page.

**Negative / risks (mitigations)** — the package looks abandoned: 0.1.3, no homepage or author, and the wheel
ships eleven `main.*.chunk.js` builds of which `index.html` loads two (*mitigation:* it is thirty lines of
Python plus a static directory under MIT — if it breaks we vendor it outright, which is a very different
exposure from an abandoned framework, and the native-widget fallback stands behind that); the pitch moves
inside an iframe, so page-level CSS no longer reaches it (*mitigation:* the pitch already carries its own
`<style>`, which the spike verified survives); the tap path cannot be AppTested (*mitigation:* the dropdown
can, and it drives the same state — the component boundary is exactly where the test coverage stops needing to
go, and the HTML transform that feeds it **is** unit-testable on its own).

---

### 🧾 Status & follow-ups

- **Proposed — needs the owner gate.** It adds a dependency to the **golden page**, which given
  `prefers-lightweight-over-data-completeness` is the owner's call, not mine.
- **If accepted:** `pitch_html()` split; the anchor in `_kit_html`; `st-click-detector` into
  `requirements.txt`; the tap wired to the existing selection state on My Squad; tests for the anchor emission
  and the id round-trip through the transform, plus the existing AppTest suite unchanged as proof the dropdown
  path still carries the page; a **Cloud deploy check** before it is called done; 3-part DoD.
- **⚠️ A claim in this ADR was wrong, and the build found it.** It stated the golden page would lose *"no
  coverage at all"*. That was true of the **selection** path and false of the **pitch markup**: four AppTest
  tests read the pitch out of `AppTest.markdown`, and once it renders inside the component it is no longer
  there. Coverage did not vanish — it **moved**, and it moved somewhere better. Splitting `pitch_html()` out
  made the markup a pure function, so those assertions now run directly against it (`tests/test_pitch_html.py`,
  10 tests) without a page render at all: stricter, faster, and no longer dependent on how the page happens to
  be assembled. The page-level tests keep asserting what a page can still prove — that it renders, and that
  the picker driving selection is there. Worth recording precisely, because "additive change, no test impact"
  was the reasoning that made this cheap, and it was three-quarters right rather than right.
- **⏳ Still outstanding: the Cloud deploy check.** Strongly de-risked (`streamlit-cookies-controller` runs the
  identical mechanism in production) but **not verified**. Not done until it is.
- **Not this ADR:** the same gesture on other surfaces (Squad Lab's build pitch is the obvious next), and
  tap-to-*act* shortcuts — fplapex's `✕` to remove — which are a second interaction on top of selection.
