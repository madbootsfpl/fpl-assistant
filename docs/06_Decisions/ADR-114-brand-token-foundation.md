# Architectural Decision Record: A brand-token foundation (design system in `brand.py`)

**Decision ID:** ADR-114
**Date:** 2026-08-17
**Status:** Accepted — design gate. Build = Sprint 161 (Sprint B of the UX/Style Audit).
**Superseded By / Replaces:** **Extends ADR-103** (the MADBOOTS brand). Formalises what ADR-103 started (a brand
source of truth) into a small **design-token system** + an app-wide **Streamlit theme**. Consumed incrementally by
the card components (ADR-084, ADR-109/110/113, US-386) and the data surfaces.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The app-wide **UX/Style Audit** (`docs/00_Project/UX_Style_Audit.md`, 2026-08-17) found the brand is **not actually
sourced from the brand**: **~50 distinct hex values** across `web_streamlit/`, only **4** defined in `brand.py`;
the hero `PURPLE`/`ORANGE` used ~2× each outside it. Concretely:
- **No semantic token** — good/warn/bad is reinvented per component (~12 greens, 4 ambers, 5 reds) *and* as emoji
  (🟢🟡🟠🔴 in `ratings.py`); several tinted chips fail **WCAG AA contrast** (white on FDR green ~2.6:1, amber ~2.7:1).
- **No Streamlit theme** — `.streamlit/config.toml` has no `[theme]`, so the primary accent is Streamlit's **red
  `#FF4B4B`** (off-brand) on every slider/checkbox/selected control; only 1 of 22 `st.button`s sets `type=`.
- **No scale** — one-off font sizes, paddings and radii (8/9/10/12/14/16/18px) with no rungs; 5 bespoke card styles.
- **Thin brand presence** — most page headers are a bare emoji title; only Home + Maddie carry the MADBOOTS mark.
- **The mantra drifts** — "the analytics decide…" appears in ~4 wordings, none sourced from `brand.py`.

Sprint A (Sprint 160) fixed the cheap honesty/copy items. **This ADR sets the foundation** the rest of the audit
(naming/onboarding, My Squad density) aligns to — so future work *consumes tokens* instead of inventing colour.

#### Decision Drivers
- **One source of truth** — colour/spacing/type decisions live in `brand.py`; a raw hex in a component becomes the
  exception, not the norm.
- **Fix real defects on the way** — the sub-AA contrast chips and the off-brand-red primary are corrected *by*
  adopting the tokens, not as separate work.
- **Low blast radius, incremental adoption** — define tokens + theme now; retro-fit components **as they're
  touched**, not in one risky sweep. Keep `brand.py` Streamlit-free (pure constants + string helpers).
- **Consistent, honest brand** — purple accents app-wide; the MADBOOTS mark on every page; one mantra.

---

### ✅ Decision

**1. A design-token layer in `brand.py`** (additive — pure constants/strings, no Streamlit import):
- **Brand:** keep `PURPLE #8B2FC9 · PURPLE_LT #B45CF0 · ORANGE #FF6A00 · INK` — now *consumed*, not re-typed.
- **Semantic triad (AA-safe on white ≥4.5:1):** `GOOD #1e8047 · WARN #b7791f→` a legible gold · `BAD #c62828`, each
  with a `_TINT` (chip background) and `_FG` (text-on-tint) so a chip is always a **colour pair**, never white-on-
  mid-tint. `ACCENT_TEAL #5eead4` stays the single "projected/winner" highlight.
- **A 5-band FDR scale** (`FDR_STYLE`: 1–5 → (bg, fg) pairs) derived from GOOD→BAD, shared by Fixtures + the player
  card + the pitch (today each re-types its own).
- **Neutrals:** a small text/muted/line/surface ramp.
- **Scales:** spacing `4/8/12/16/20/24`; radius `SM 10 · MD 14 · LG 18 · PILL 999`.
- **`MANTRA`** = *"The analytics decide. The AI explains. You make the call."* (the canonical throughline).
- **A `card_css(...)` recipe helper** (optional this sprint) — one function returning the shared card frame
  (border/radius/surface/shadow/padding) with a `dark` ("objects": player card, pitch, countdown) vs `theme-aware`
  ("chrome": captain card, team banner) variant, so cards *call* it instead of hand-rolling `<style>`.

**2. An app-wide Streamlit theme** — add `[theme]` to `.streamlit/config.toml` with `primaryColor = "#8B2FC9"` (the
brand purple), so sliders/checkboxes/selected controls and `type="primary"` buttons are **brand-purple, not red**.
Adopt the convention **one primary action per view** (`type="primary"`); everything else default/secondary;
`st.link_button` for outbound, `st.download_button` for downloads.

**3. Adopt where it fixes a real issue (this sprint), not everywhere at once:**
- **Contrast:** re-point the **FDR pills / captain bands / Fixtures ramp** at `FDR_STYLE`/the semantic pairs → all
  state chips clear AA. (The Fixtures ramp from US-391 becomes a token consumer.)
- **Brand presence:** add a small `brand.mark_html` lockup to the **data-page headers** (Players · Fixtures ·
  Trending · News · Ask · Help · Feedback) so every page carries the mark.
- **Mantra:** replace the ~4 ad-hoc wordings with `brand.MANTRA`.

**4. What this is *not*.** Not a full retro-fit of all ~50 hexes / all 5 cards in one go (that's incremental,
component-by-component as each is touched — a follow-on, `docs/00_Project/UX_Style_Audit.md`). Not a dark-theme
launch (the app stays light; ADR-103 Approach B). Not an analytics/engine change — **display only**. Not a change to
the wordmark/badge/tagline.

---

### 🔀 Alternatives Considered

- **Retro-fit every component to tokens in Sprint B.** Rejected — high risk, large diff across 5 cards + 7 surfaces;
  the value is the *tokens + theme + the contrast/brand fixes*, with adoption spread over the surfaces we already
  revisit. (Recorded as an ongoing "adopt tokens" task.)
- **A CSS file / external design system.** Rejected — Streamlit's model + the self-contained-HTML-card pattern
  (ADR-084) mean tokens-as-Python-constants + a `card_css()` helper fit best and keep `brand.py` importable anywhere.
- **Leave the primary red / set a full custom theme (fonts, backgrounds).** Rejected both — red is off-brand;
  a full theme is more blast radius than needed. Set **just `primaryColor`** (minimal, high-value).

---

### 🧭 Consequences

**Positive**
- Colour/spacing/type decisions have **one home**; future work consumes tokens → drift stops compounding.
- The **contrast defects and the off-brand-red primary are fixed** as a by-product; purple accents app-wide.
- Every page carries the **MADBOOTS mark**; one mantra everywhere.

**Negative / risks (mitigations)**
- **`primaryColor` is app-wide** — it recolours every accent/primary button. *Mitigation:* verify the suite +
  a smoke; it's display-only and there's no test asserting the red. Owner sign-off via a preview of the themed
  accents + the token swatches.
- **Partial adoption** — tokens exist but not every component uses them yet, so some drift remains after this
  sprint. *Mitigation:* explicit — the audit tracks the remaining retro-fit; new/edited components must use tokens.
- **`brand.py` must stay Streamlit-free.** *Mitigation:* tokens are constants; `card_css()` returns a string.

---

### 🧾 Status & follow-ups

- **Accepted.** Build (**Sprint 161 / Sprint B**): **US-394** tokens + `MANTRA` (+ `card_css` helper) in `brand.py`;
  **US-395** the `[theme] primaryColor` in config.toml + the primary-button convention; **US-396** adopt the
  semantic/FDR tokens to clear the **AA-contrast** chips (FDR pills · captain bands · Fixtures ramp); **US-397** the
  brand mark on the data-page headers + unify the `MANTRA`. Owner sign-off via a swatch/accent preview before build.
- **Not this ADR / follow-ups:** the full token retro-fit of player_card/pitch/countdown/ratings; a shared `card_css`
  adoption across all 5 cards; the remaining audit themes (C naming/onboarding, D My Squad density).
