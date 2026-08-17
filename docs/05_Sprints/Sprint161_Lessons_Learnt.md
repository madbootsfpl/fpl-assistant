# Lessons Learned

**Sprint:** Sprint 161 — UX Sprint B (the brand-token foundation)

**Dates:** 2026-08-17

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Turn `brand.py` into a small **design-token system** and set an app-wide theme (ADR-114), then adopt the tokens
where they fix a real defect — the sub-AA contrast chips, the off-brand-red primary, the thin brand presence and
the drifting mantra. The foundation the rest of the UX audit (naming/onboarding, My Squad density) aligns to.
Display-only; owner-approved via a token/accent preview.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Tokens as Python constants.** `brand.py` stays Streamlit-free; the semantic triad, `FDR_STYLE`, scales and
  `MANTRA` are plain constants any surface can import — the same "single source of truth" idea ADR-103 started.
- **Incremental adoption over a big-bang refactor.** Defined everything, adopted it in the contrast-failing chips +
  the visible gaps, and explicitly deferred the full retro-fit — a small, safe diff with most of the value.

## New Skills Acquired

- **Accessibility lives in the token's shape.** Modelling a state colour as a **(tint, fg) pair** (not a single
  hex) makes every chip legible by construction — "vibrant" and "AA-safe" become the same edit. This is the reusable
  insight for the rest of the card work.
- **`primaryColor` is the cheapest brand win.** One line in `config.toml` recolours every accent app-wide.

---

# What Went Well ✅

- Owner signed off the palette from a swatch preview, so the build matched intent first time.
- Clean, display-only diff; the token change is drift-proof (tests now anchor on `brand.*`, not raw hexes).

# What Was Tricky ⚠️

- The token swap broke four pinned tests (captain band classes, player-card FDR hex, the Home mantra) — expected,
  and the fix *improved* them (assert the token, not the literal).
- Scoping restraint: resisting the urge to route all ~50 hexes now — the ADR made "partial on purpose" explicit so
  the remaining drift is tracked, not hidden.

# Process / Meta 🛠️ _(for Tony)_

# Personal Reflections 💭 _(for Tony)_
