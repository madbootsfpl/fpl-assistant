# Sprint 161: UX Sprint B — the brand-token foundation (US-394–397)

**Dates:** 2026-08-17 →
**Status:** 🚧 Planned — gated by **ADR-114**. Display-only; the foundation the rest of the audit aligns to.
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
*(filled at retro)*

### 🧠 Lessons
*(filled at retro)*
