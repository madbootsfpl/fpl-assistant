# Spike — tap the pitch (ADR-108 follow-on)

**Date:** 2026-08-24 · **Timebox:** ~1 hour · **Verdict: viable, pending two checks only a human can do.**

ADR-108 deferred the tap-the-shirt component because it *"introduces a front-end build toolchain to a
pure-Python project"* and because the golden page would *"lose AppTest coverage"*. Both objections turn out to
be softer than they read.

---

## What was answered

**1. No npm. No React. No build step.** `st-click-detector` (PyPI, 0.1.3) ships a **pre-built** frontend and is
about thirty lines of Python around `components.declare_component(path=…)`. Installing it pulls **one package
and zero new transitive dependencies** — `streamlit>=0.63` is its only requirement and we already exceed it.

```
Would install st-click-detector-0.1.3          ← the entire dependency impact
```

Its API is exactly the shape this needs: `click_detector(html) -> id_of_clicked_anchor`.

**2. The iframe auto-sizes.** ADR-084 rejected `components.v1.html` because of *"a fixed-height iframe that
can't auto-size"* — a fair reading of the raw API, but this component's bundle calls `setFrameHeight`, so it
sizes to its content. That objection does not carry over.

**3. The real pitch survives intact.** No sanitiser in the bundle, so the HTML passes through raw. Verified
against the live squad by injecting an anchor per kit card:

```
kit cards in the pitch : 15        pitch <style> survives : True
anchors injected       : 15        hover cards survive    : 18 popovers
ids match the squad    : True      payload size           : 25,297 chars
all ids resolve        : True
```

The ADR-084 pitch — CSS, kits, captain armband, hover cards — comes through whole. Nothing needs redesigning.

**4. It is MIT licensed.** The metadata says `License: UNKNOWN`, which is alarming until you look: the wheel
ships an MIT `LICENSE` (Streamlit Inc's, inherited from the component template). Compatible with our
PolyForm-NC.

---

## What it costs

**The package looks abandoned.** Version 0.1.3, no homepage, no author, no declared license, and the wheel
ships **eleven** `main.*.chunk.js` builds (~1 MB of JS) of which `index.html` loads two — the accumulated
output of past builds, shipped wholesale. It works, but nobody is tending it.

**That risk is smaller than it looks, and worth stating plainly:** the package is thirty lines of Python plus a
static directory, under MIT. If it ever breaks, we can vendor it outright — no upstream needed. That is a very
different exposure from depending on an abandoned framework.

**One refactor is required.** `render_pitch` writes straight to `st.markdown` and returns nothing, so there is
no HTML to hand a component. The build needs a `pitch_html()` split out of it (build → render), which is a
clean separation the module wants anyway. The spike works around it by capturing `st.markdown`; production
should not.

---

## Answered since (2026-08-24, owner)

**1. ✅ The click works.** Owner tapped Virgil on the spike app and it returned him. The round-trip is real.

**2. ✅ Cloud is de-risked by precedent.** `streamlit-cookies-controller` — already live in production for
"remember me", owner-verified on Safari and Chrome — uses the **identical mechanism**: `declare_component`
with a static frontend build directory. The component-serving path is therefore already proven on this Cloud
deploy. Residual risk is a package-specific install or CSP failure, not the mechanism, and the build should
still confirm it on the real deploy.

---

## (original, at spike time) What was NOT answered

**1. The click itself.** No browser tooling was available in this session, so the round-trip was never
exercised — everything above is static verification of the payload. **The spike app is the way to check it:**

```
./venv/bin/python -m streamlit run spikes/185-tap-the-pitch/spike_app.py
```

Tap a shirt; the player's id and name should appear beneath the pitch. That is the whole test.

**2. Streamlit Community Cloud.** The deploy check ADR-108 flagged, and still the likeliest thing to kill an
otherwise-working approach. Only a real deploy answers it.

Both are owner steps. **Neither should be assumed** — the ADR that follows should record the answers, not the
expectations.

---

## Recommendation

Proceed to an ADR **if and only if** both checks pass, and build it as a **strictly additive** input: the
dropdown stays exactly as it is (owner-agreed), so AppTest keeps driving it, keyboard users keep a path, and a
component failure degrades to today's behaviour rather than an unusable page. That turns ADR-108's coverage
objection from a cost into a non-issue.

Fallback if Cloud says no: rebuild the pitch from native Streamlit widgets (image buttons in a column grid).
Zero JS and fully testable, but it means giving up the CSS pitch ADR-084 deliberately chose — so it is the
answer of last resort, not the plan.
