"""MADBOOTS brand — the single source of truth for the product's user-facing identity (ADR-103).

The **name**, the **tagline**, and the Streamlit **page config** (tab title + icon). Deliberately **pure** — no
Streamlit import — so any surface (a page, the card, the gate) can use it. US-348 introduces the name/tagline +
`page_config`; **US-349** grows this with the **MB badge** favicon + the two-tone CSS **wordmark**.

Only *visible* surfaces rebrand: the internal `fpl-assistant` package + the `FPL_*` secrets are unchanged (ADR-103).
"""

NAME = "MADBOOTS"                              # the display name — one word; the wordmark is two-tone (MAD/BOOTS)
TAGLINE = "Fantasy Football, Calculated."

PAGE_ICON = "⚽"                                # US-349 swaps this for the MB badge asset (the favicon)


def page_config(page: str | None = None) -> dict:
    """Kwargs for `st.set_page_config(**brand.page_config("Players"))` — a per-page browser-tab title
    (`"Players · MADBOOTS"`, or just `MADBOOTS` on Home) + the shared icon + wide layout. One place to change the
    tab title/icon on every page."""
    return {"page_title": f"{page} · {NAME}" if page else NAME,
            "page_icon": PAGE_ICON, "layout": "wide"}
