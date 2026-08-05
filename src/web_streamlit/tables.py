"""Shared image-rich table rendering for the Streamlit edge (Sprint 059).

One helper so every squad tab (Build · Analyse · Transfer · Captain · My Squad) shows the same
photo + team-badge table Players/Fixtures do — visual consistency, one place for the column config.
The tabs keep their text summaries beneath (the "augment" approach): the picture *and* the analysis.
"""

import streamlit as st

# Any row key named "photo" / "badge" (or "out"/"in" photo variants) renders as an image thumbnail.
_IMAGE_COLS = ("photo", "badge", "out", "in")


def render_player_table(rows) -> None:
    """Render `rows` (dicts whose image keys hold FPL CDN URLs) as a native sortable table with the
    photo/badge columns shown as thumbnails. A no-op on empty rows."""
    if not rows:
        return
    present = [c for c in _IMAGE_COLS if any(c in r for r in rows)]
    st.dataframe(
        rows, hide_index=True, width="stretch",
        column_config={c: st.column_config.ImageColumn("", width="small") for c in present},
    )
