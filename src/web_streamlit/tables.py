"""Shared image-rich table rendering for the Streamlit edge (Sprint 059).

One helper so every squad tab (Build · Analyse · Transfer · Captain · My Squad) shows the same
photo + team-badge table Players/Fixtures do — visual consistency, one place for the column config.
The tabs keep their text summaries beneath (the "augment" approach): the picture *and* the analysis.
"""

import streamlit as st

from src.web_streamlit.formats import column_config


def render_player_table(rows) -> None:
    """Render `rows` (dicts whose image keys hold FPL CDN URLs) as a native sortable table — image
    columns as thumbnails, numeric columns formatted by the shared convention (ADR-072). No-op on empty."""
    if not rows:
        return
    labels = {label for r in rows for label in r}      # union — callers pass different column sets
    st.dataframe(rows, hide_index=True, width="stretch", column_config=column_config(labels))
