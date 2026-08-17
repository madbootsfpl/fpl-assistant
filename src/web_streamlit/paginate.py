"""Row-count caption for the long browse tables (ADR-116 — supersedes ADR-063's paging).

The Players pool · the stat boards · Trending render as **one scrollable, fully-sorted `st.dataframe`** — so the
native column-header sort operates on the **whole** set (paging made it sort only the visible page, a misleading
affordance; Streamlit 1.61 can't disable native sort). This just shows a "N shown" count; the grid itself scrolls
(row virtualisation keeps it light). Display-only — it never mutates the input.
"""

import streamlit as st


def show_count(rows) -> list:
    """Render a "N shown" caption and return `rows` unchanged (the table is one scrollable grid, not paged)."""
    st.caption(f"{len(rows)} shown")
    return list(rows)
