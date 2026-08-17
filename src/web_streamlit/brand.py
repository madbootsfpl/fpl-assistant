"""MADBOOTS brand — the single source of truth for the product's user-facing identity (ADR-103).

The **name**, the **tagline**, the **MB badge** (favicon + small mark), and the two-tone **wordmark**. Kept light —
no Streamlit import — so any surface (a page, the card, the gate) can use it. US-348 introduced the name/tagline +
`page_config`; **US-349** adds the badge favicon (`page_config`'s `page_icon` is now the badge) + `badge_path()` /
`badge_data_uri()` + the CSS `wordmark_html()`.

Only *visible* surfaces rebrand: the internal `fpl-assistant` package + the `FPL_*` secrets are unchanged (ADR-103).
"""

import base64
import functools
from pathlib import Path

NAME = "MADBOOTS"                              # the display name — one word; the wordmark is two-tone (MAD/BOOTS)
TAGLINE = "Fantasy Football, Calculated."
# Legal hygiene (ADR-103): a named product on official FPL data — a quiet, honest not-affiliated line.
DISCLAIMER = f"{NAME} is not affiliated with the Premier League or the official Fantasy Premier League game."

# Brand palette (ADR-103)
PURPLE = "#8B2FC9"
PURPLE_LT = "#B45CF0"                          # a lighter purple, legible on the card band's dark ground
ORANGE = "#FF6A00"
INK = "#17131F"

# --- Design tokens (ADR-114) — the single source of truth for colour/scale; consume these, don't re-type hexes. ---

# Semantic state — each is a **pair**: a solid, a light TINT (chip background), and an FG (text-on-tint), so a state
# chip is always a colour pair and never white-on-mid-tint (which failed WCAG AA). The solids clear ~4.5:1 on white.
GOOD, GOOD_TINT, GOOD_FG = "#1e8047", "#e6f4ec", "#0b5e30"
WARN, WARN_TINT, WARN_FG = "#d98c00", "#fdf1d6", "#8a5a00"
BAD, BAD_TINT, BAD_FG = "#c62828", "#fce8e8", "#a51d1d"
ACCENT_TEAL = "#5eead4"                         # the single "projected / winner" highlight

# FDR 1–5 → (background, text) pairs, vibrant green→red — one home for the fixture ticker + the card FDR pills.
FDR_STYLE = {
    1: ("#1a9850", "#ffffff"), 2: ("#66bd63", "#0b3d1a"), 3: ("#f9a825", "#3d2c00"),
    4: ("#f46d43", "#ffffff"), 5: ("#d73027", "#ffffff"),
}

# Neutrals (on the light app) — text · muted · hairline · surfaces.
TEXT, MUTED, LINE, SURFACE, SURFACE_2 = "#1c1830", "#5f6472", "#e6e6ea", "#ffffff", "#f4f2f8"

# Scales — collapse the ad-hoc paddings/radii onto rungs.
SPACE = (4, 8, 12, 16, 20, 24)
RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_PILL = 10, 14, 18, 999

# The canonical throughline — one wording, referenced everywhere (was ~4 variants).
MANTRA = "The analytics decide. The AI explains. You make the call."


def token_css_vars() -> str:
    """The brand palette as CSS custom properties (`:root{--mb-*}`) — so the self-contained HTML cards can
    reference `var(--mb-teal)` / `var(--mb-purple)` and stay in sync with `brand.py` instead of re-typing the hex
    (ADR-114/116). Prepended to each card's CSS block so the vars are defined wherever a card renders (redundant
    `:root` blocks are harmless — identical values). Only the genuinely *shared* brand colours are exposed;
    component/object surfaces (the dark card, the pitch turf, the countdown slate) stay component-specific."""
    return ("<style>:root{"
            f"--mb-purple:{PURPLE};--mb-purple-lt:{PURPLE_LT};--mb-orange:{ORANGE};--mb-ink:{INK};"
            f"--mb-teal:{ACCENT_TEAL};--mb-good:{GOOD};--mb-warn:{WARN};--mb-bad:{BAD};"
            "}</style>")

_ASSETS = Path(__file__).with_name("assets")
_BADGE = _ASSETS / "madboots-badge.png"        # 298² transparent — the favicon + the Home/gate mark (via st.image)
_BADGE_SMALL = _ASSETS / "madboots-badge-64.png"   # 64² — inlined as a data URI where the badge is small (the band)

PAGE_ICON = str(_BADGE)                         # the favicon on every page — Streamlit `page_icon` takes an image path


def badge_path() -> str:
    """Filesystem path to the MB badge PNG — for `st.image(...)` (the Home header + the beta gate)."""
    return str(_BADGE)


@functools.lru_cache(maxsize=1)
def badge_data_uri() -> str:
    """The (small) badge as a base64 `data:` URI — for **inline HTML** (the player-card brand band). Cached
    (read + encoded once); uses the 64² asset so the card stays light."""
    return "data:image/png;base64," + base64.b64encode(_BADGE_SMALL.read_bytes()).decode()


def page_config(page: str | None = None) -> dict:
    """Kwargs for `st.set_page_config(**brand.page_config("Players"))` — a per-page browser-tab title
    (`"Players · MADBOOTS"`, or just `MADBOOTS` on Home) + the **badge favicon** + wide layout."""
    return {"page_title": f"{page} · {NAME}" if page else NAME,
            "page_icon": PAGE_ICON, "layout": "wide"}


def mark_html(badge_px: int = 15, font_px: int = 12, purple: str = PURPLE) -> str:
    """The MB badge **+** the two-tone MADBOOTS wordmark as one compact lockup — for card bands/footers (the player
    card, the captain card). MAD+BOOTS are a **single** flex child (wrapped in one span), so the badge↔word `gap`
    can never fall *inside* the word — the colour split (`purple` · orange) carries the break. `purple` lets the
    caller pick a shade legible on the surface (e.g. `PURPLE_LT` on a dark band)."""
    return (
        f'<span style="display:inline-flex;align-items:center;gap:6px;line-height:1">'
        f'<img src="{badge_data_uri()}" alt="" style="height:{badge_px}px;width:auto"/>'
        f'<span aria-label="{NAME}" style="font-weight:900;font-style:italic;font-size:{font_px}px;'
        f'letter-spacing:-.01em">'
        f'<span aria-hidden="true" style="color:{purple}">MAD</span>'
        f'<span aria-hidden="true" style="color:{ORANGE}">BOOTS</span></span></span>')


def wordmark_html(px: int = 38) -> str:
    """The two-tone **MADBOOTS** wordmark as inline HTML — **MAD** purple · **BOOTS** orange, the colour split doing
    the word-break (no literal space). `aria-label` carries the whole-word accessible text; the coloured spans are
    decorative (`aria-hidden`)."""
    return (
        f'<div aria-label="{NAME}" style="font-family:\'Arial Black\',\'Helvetica Neue\',Impact,sans-serif;'
        f'font-weight:900;font-style:italic;font-size:{px}px;line-height:1;letter-spacing:-.02em;'
        f'-webkit-text-stroke:1.5px {INK};paint-order:stroke fill;">'
        f'<span aria-hidden="true" style="color:{PURPLE}">MAD</span>'
        f'<span aria-hidden="true" style="color:{ORANGE}">BOOTS</span></div>')
