# Lessons Learned

**Sprint:** Sprint 099 — Redesign the My Squad pitch (an FFH-style green pitch)

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Replace the plain native card-grid with a **green football pitch** — players by formation as kit cards (image ·
name · xP chip · £ · opponent · (C) armband · sub badges · flags) + a bench strip — a clear visual jump toward
the Fantasy Football Hub look, keeping all information and all edit controls.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Contained custom CSS in Streamlit** — one self-contained `st.markdown(unsafe_allow_html=True)` block for a
  styled, themeable, JS-free graphic.
- **Keeping a redesign testable** — assert on the emitted HTML (`AppTest.markdown`) instead of native elements.

### New Skills Acquired

- Streamlit **1.61.1 preserves** `<style>` + `<div>`/`<img>` through `unsafe_allow_html` (not sanitised), and
  the HTML is inspectable via `AppTest.markdown` — so a CSS redesign is both feasible and headless-testable.
- **HTML in `st.markdown` must be unindented** — a 4-space indent makes Markdown treat it as a code block.
- **Overlaid badges** need a positioned wrapper: a `.pic{position:relative}` around the `<img>` with
  `position:absolute` badges (captain armband top-right, sub number top-left).
- **A published Artifact is the right feedback tool for a visual change** — reproduce the real CSS/HTML with
  real data; swap CDN images (blocked by the Artifact CSP) for inline **SVG** stand-ins so the layout/badges
  are exactly what ships.

---

# What Went Well ✅

- **Feasibility verified before the gate** — the `st.markdown` HTML check made ADR-084 a safe decision.
- **Tiny blast radius** — the pitch was already display-only (edit controls are separate widgets), so the
  redesign touched one source file + one test file; interactivity was never at risk.
- **The preview closed the loop** — I can't see the tester's FFH image and the owner couldn't run the app
  mid-sprint; a faithful Artifact turned "does it look right?" into a concrete approval.
- **US-255 synergy** — the photo-or-shirt resolver means every kit renders on the pitch.
- 663 tests stayed green (3 pitch-content tests rewired to the HTML blob); ruff clean.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Content moved off `st.caption` | the pitch is now one HTML block | Rewire the 3 pitch tests to read `AppTest.markdown` |
| Markdown ate the HTML as a code block | 4-space-indented HTML lines | Keep the HTML/CSS lines unindented |
| The (C)/sub markers looked plain | text, not badges | A `.pic` wrapper + absolutely-positioned `.c-badge`/`.s-badge` |
| Can't show the owner the result | mid-sprint, no running app; can't see FFH ref | Publish a faithful Artifact preview (real data + SVG jerseys) |
| Artifact CSP blocks the FPL CDN | strict sandbox | Inline SVG club jerseys as photo stand-ins |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| `st.markdown` HTML | Keeps `<style>`/`<div>`/`<img>`; unindent the lines; inspectable via `AppTest.markdown` |
| Overlaid badges | A positioned `.pic` wrapper, absolute badges |
| Display-only redesign | One file, no interactivity risk when controls are separate widgets |
| Artifact previews | The right tool for a visual sign-off; inline SVG when the CSP blocks images |

---

# Development Lessons 💻

- When a redesign moves content between element types, the tests must follow the content (caption → markdown).
- Keep custom CSS to one self-contained, JS-free, display-only block — a visual regression can't break logic.
- For a subjective visual change, produce a concrete artifact to review against, don't ship blind.

---

# AI Collaboration Lessons 🤖

- "Make it look like FFH" is a subjective target I couldn't see. Reproducing the *actual* shipping CSS/HTML in
  a published preview (with real squad data) made the feedback loop concrete and fast — the owner approved from
  the preview, not a description.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-084 | **A styled (CSS) pitch view for My Squad** — `render_pitch` emits one self-contained HTML/CSS block: a green pitch with formation rows + a bench strip, each player a kit card (image · name · xP chip · £ · opponent · (C) armband · sub badges · flags). Names HTML-escaped; responsive; theme-readable; no JS; display-only (edit controls unchanged). Revisits the informal Sprint-062 "native cards, no custom CSS" call; tests read the HTML via `AppTest.markdown` | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Reuse the pitch on Build** (the formation preview is still a table) — a consistency win.
- **Auto-derive a display XI** when no bench is declared (today the pitch shows all 15 in position rows).
- **AI Chat Assistant** (owner intake) — still needs a grounded-vs-free-form design/ADR + a willing LLM.
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- Post-**GW1 (2026-08-21)**: the Data Hardening flip + xP calibration; the Price Change Predictor lights up.
- Backlog still open: persisted chat context; season countdown / deadline banner; server-side squad
  persistence; Chip Strategy's gated half (DGW/BGW + mini-league).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Publish a preview for visual work — it's faster than describing and safer than shipping blind.

---

# Key Commands Learned

```text
python -m src.web_streamlit   # Squads → My Squad: the new green pitch (kits in formation, badges, xP chips)
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Kit card | A player's pitch cell — image · name · xP chip · £ · opponent · badges · flags |
| Captain armband | The gold "C" badge overlaid on the captain's kit |
| Sub badge | The green 1/2/3/GK badge showing a bench player's auto-sub priority |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-084 | The styled-pitch decision + the "one contained block, display-only" rationale |
| `src/web_streamlit/pitch.py` | The pitch HTML/CSS + kit-card builder |
| The Artifact preview | A faithful, reviewable render of the pitch (real squad, SVG jerseys) |

---

# Questions for Future Me ❓ _(for Tony)_

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- US-257 The FFH-style pitch — a green CSS pitch, formation rows + bench, kit cards (ADR-084)
- US-258 Badges & polish — (C) armband + sub-number badges, 👕 placeholder, hover/spacing; a preview Artifact

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
