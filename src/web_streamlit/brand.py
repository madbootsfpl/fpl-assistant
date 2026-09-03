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

# FDR 1–5 → (background, text) pairs — **mirrors the official FPL app** so it reads familiarly (owner, 2026-08-17):
# deep-green → bright-green → **grey (the neutral break)** → red → maroon. One home for the ticker + the card pills.
FDR_STYLE = {
    1: ("#257d5a", "#ffffff"),   # very easy — FPL deep green
    2: ("#01fc7a", "#0a3d2a"),   # easy — FPL bright green (dark ink for contrast)
    3: ("#e7e7e7", "#3a3a3a"),   # medium — FPL grey, a calm break from the greens/reds
    4: ("#ff1751", "#ffffff"),   # hard — FPL red
    5: ("#80072d", "#ffffff"),   # very hard — FPL maroon
}

# Neutrals (on the light app) — text · muted · hairline · surfaces.
TEXT, MUTED, LINE, SURFACE, SURFACE_2 = "#1c1830", "#5f6472", "#e6e6ea", "#ffffff", "#f4f2f8"

# Scales — collapse the ad-hoc paddings/radii onto rungs.
SPACE = (4, 8, 12, 16, 20, 24)
RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_PILL = 10, 14, 18, 999

# The canonical throughline — one wording, referenced everywhere (was ~4 variants).
#
# ⚠️ **Changed 2026-08-29 (ADR-168): it used to say "The AI explains."** That was a promise the deployed app
# could not keep — there is no Ollama on Streamlit Cloud, so for every tester the narration simply is not
# there (Help said so; the mantra did not). madboots.com had already quietly dropped the clause, running
# "The analytics decide; you stay in control" — so the in-app wording was the last place still claiming it.
#
# What replaced it is the thing the app actually does, on Cloud, today: every answer carries its evidence —
# the ✓/⚠ trust line, the named outlet behind a departure, the reasons under a Scout pick. "Ask it anything"
# is what everyone claims; showing the working is what almost nobody does.
MANTRA = "The analytics decide. Every answer shows its working. You make the call."
# NOTE: a `token_css_vars()` CSS-variable helper was tried (S165) to single-source the card hexes, but prepending a
# 2nd `<style>` block broke Streamlit's markdown rendering of the cards (the banner rendered unstyled). Reverted —
# the shared brand hexes stay inline in the card CSS. Not worth a 2nd style block; revisit only with a safer route.

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


def nav_css(key: str, *, primary_button: str | None = None) -> str:
    """CSS for the app's main selector — purple, full width, equal segments (ADR-176).

    Returns a `<style>` block scoped to `st.container(key=…)`, which Streamlit renders with a `.st-key-{key}`
    class. Pass the same key you gave the container.

    **Why CSS and not a theme.** ADR-114 tried `primaryColor` in `config.toml` and reverted it: **any**
    `[theme]` block *pins* the theme — `base` defaults to light — which removes the viewer's Light/Dark/System
    toggle. Theme-following beats a brand accent, so the purple lives where we control it directly. This is
    that rule applied to a widget instead of markup.

    **Why one function and not five copies.** This began inline in `1_My_Squad.py` (ADR-175). Pasting it into
    each page is *"one rule written twice always drifts"* (ADR-140) — the failure this project has since paid
    for in a stale caption, a stale ADR index and a stale runbook. A test asserts no page hand-rolls it.

    `primary_button` optionally styles a keyed button container the same way, for the one action a panel is
    really about (ADR-174's *Apply this transfer*).

    ⚠️ It degrades to Streamlit's own widget if these selectors ever stop matching — the control keeps
    working and merely looks default, which is what these pages had before. A broken selector is not a
    possible outcome of this failing.
    """
    css = f"""
        .st-key-{key} div[data-testid="stButtonGroup"] {{ width: 100%; }}
        .st-key-{key} div[data-testid="stButtonGroup"] > div {{ width: 100%; display: flex; gap: 4px; }}
        /* `min-width: 0` lets a segment shrink below its label, and Streamlit's own ~1rem of horizontal
           padding then pushed "This week" and "Transfer" into "This …" / "Trans…" on a phone. Trimming
           the padding buys the characters back; `nowrap` keeps a segment one line if it still runs
           short, because a wrapped label makes the whole row taller. (Owner, 2026-09-03.) */
        .st-key-{key} div[data-testid="stButtonGroup"] button {{
            flex: 1 1 0; min-width: 0; padding-left: 0.35rem; padding-right: 0.35rem;
            white-space: nowrap; }}
        .st-key-{key} div[data-testid="stButtonGroup"] button p {{
            overflow: hidden; text-overflow: ellipsis; }}
        .st-key-{key} button[aria-checked="true"],
        .st-key-{key} button[kind="segmented_controlActive"] {{
            background: {PURPLE} !important; border-color: {PURPLE} !important; color: #fff !important; }}
    """
    if primary_button:
        css += f"""
        .st-key-{primary_button} button {{
            width: 100%; background: {PURPLE}; border-color: {PURPLE}; color: #fff; font-weight: 600; }}
        .st-key-{primary_button} button:hover {{
            background: {PURPLE_LT}; border-color: {PURPLE_LT}; color: #fff; }}
    """
    return f"<style>{css}</style>"


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
