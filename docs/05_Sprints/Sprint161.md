# Sprint 161: UX Sprint B — the brand-token foundation (US-394–397)

**Dates:** 2026-08-17
**Status:** ✅ Complete — US-394–397 (ADR-114), display-only. Owner-approved via a token preview. 1001 → 1003 tests.
**Capacity:** ~1 session
**Carried Over:** none

> **Why:** the UX audit found colour isn't sourced from the brand (~50 hexes, 4 in `brand.py`; no semantic token;
> off-brand-red primary; sub-AA contrast chips; thin brand presence; a drifting mantra). Define the tokens + an
> app-wide theme, then adopt where it fixes a real defect. **Not** a full retro-fit of every card (incremental).

---

### 🎯 Scope

**US-394 — tokens in `brand.py`** (additive, pure constants; keep it Streamlit-free):
- Semantic `GOOD/WARN/BAD` each with `_TINT` + `_FG` (a chip is always a colour **pair**); `ACCENT_TEAL`.
- `FDR_STYLE` (1–5 → (bg, fg) pairs) derived from GOOD→BAD — one home for the fixture/ pill palette.
- A neutral ramp (text/muted/line/surface); spacing (`4/8/12/16/20/24`) + radius (`SM/MD/LG/PILL`) scales.
- `MANTRA = "The analytics decide. The AI explains. You make the call."`.
- *(Stretch)* a `card_css(...)` recipe helper (dark vs theme-aware variant).

**US-395 — the app-wide theme** — add `[theme] primaryColor = "#8B2FC9"` (+ a light base) to
`.streamlit/config.toml`; accents/`type="primary"` go **purple, not red**. Convention: one primary action per view.

**US-396 — clear the AA-contrast chips** — re-point the **FDR pills** (`player_card.py`), **captain bands**
(`captain_card.py`) and the **Fixtures ramp** (`2_Fixtures.py`, from US-391) at `FDR_STYLE`/the semantic pairs, so
every state chip clears WCAG AA (was ~2.6–2.7:1). Display-only; values change, structure doesn't.

**US-397 — brand presence + one mantra** — add a small `brand.mark_html` lockup to the data-page headers
(Players · Fixtures · Trending · News · Ask · Help · Feedback); replace the ~4 ad-hoc "analytics decide…" wordings
with `brand.MANTRA`.

**Owner sign-off before build:** a small **swatch/accent preview** (the token colours + a themed primary button +
the before/after chips) as an Artifact.

**Not this sprint (follow-ons):** routing all ~50 hexes through tokens; a shared `card_css` across all 5 cards;
audit themes C (naming/onboarding) + D (My Squad density).

---

### ✅ Definition of Done
1. **Tests:** `brand.py` exposes the tokens/`MANTRA` (a light unit test); the themed pages still render; the
   contrast-chip renderers use the tokens (assert the token values appear, not the old hexes); the mantra is sourced
   from `brand.MANTRA` on the pages that show it. Full suite green + ruff.
2. **Manual smoke** (owner): primary buttons/accents are **purple**; the FDR/captain chips are legible; every page
   header carries the mark; the mantra reads the same everywhere.
3. **Docs:** this plan + retro; ADR-114; PROJECT_STATUS; the audit's Sprint-B row ticked; memory.

### 📋 Sprint Review

**Delivered — the design-token foundation + the fixes it pays for immediately.**
- **US-394 tokens in `brand.py`:** semantic `GOOD/WARN/BAD` as **(solid, TINT, FG)** trios, `FDR_STYLE` (1–5 →
  (bg, fg)), a neutral ramp, `SPACE`/radius scales, and the canonical `MANTRA`. Additive, Streamlit-free.
- **US-395 the theme:** `[theme] primaryColor = #8B2FC9` in `.streamlit/config.toml` — every accent + primary
  button is **brand purple, not Streamlit red**.
- **US-396 contrast:** the Fixtures ticker, the player-card FDR pills and the captain-confidence bands now source
  `brand.FDR_STYLE` / the semantic pairs, so each chip carries a **text colour per band** and clears WCAG AA (was
  ~2.6–2.7:1). Dropped the ad-hoc hexes + the `cc-high/med/low` classes.
- **US-397 brand + mantra:** the MADBOOTS mark on the four data-page headers (Players/Fixtures/News/Trending); the
  ~4 "analytics decide…" wordings unified to `brand.MANTRA` (Home/Help/Maddie).
- **Tests:** +2 (token/mantra unit test · mark-on-headers) and re-pointed the captain/player-card/home tests off
  the old hexes/classes/wording onto the tokens. **1003 total.**

**Deliberately partial (the ADR's stance):** not every one of the ~50 hexes / all 5 cards is on tokens yet — the
retro-fit is incremental as each component is touched. player_card/pitch/countdown "objects" + `ratings.py` + a
shared `card_css()` are the tracked follow-on.

**Owner smoke (post-deploy):** primary buttons/sliders/accents are **purple**; the FDR + captain chips are legible;
every data page carries the mark; the mantra reads identically everywhere.

### 🧠 Lessons

- **A chip is a colour *pair*, not a colour.** Encoding `GOOD/WARN/BAD` as (tint, fg) — and FDR as (bg, fg) — is
  what makes "vibrant" and "accessible" the same change instead of opposing ones. The token *shape* carries the
  accessibility guarantee.
- **One config line moves the whole app on-brand.** `primaryColor` recolours every accent — the highest
  brand-per-effort change in the sprint, and zero code.
- **Define centrally, adopt incrementally.** Trying to route all ~50 hexes at once would have been a huge, risky
  diff; defining the tokens + fixing the *defects* (contrast) + the *most-visible* gaps (mark, mantra) delivers the
  value now and lets the rest ride on components we already revisit.
- **A token change ripples into pinned tests.** Cards/pages that asserted the old hex/class/wording had to move onto
  the tokens (`brand.WARN_TINT`, `brand.MANTRA`) — the right anchor, and now drift-proof.
