"""Tests for the web number-formatting convention (ADR-072).

`column_config` maps table labels to Streamlit column configs. These are plain dicts, so we assert
equality against the same `st.column_config.*` call — pinning the format per column type without reaching
into Streamlit internals.
"""

import streamlit as st

from src.web_streamlit.formats import FORMATS, column_config


def test_numeric_columns_get_a_numbercolumn_with_the_right_format():
    cfg = column_config(["£m", "Val/£m", "Pts", "xGI", "Diff", "+xP"])
    assert cfg["£m"] == st.column_config.NumberColumn("£m", format="%.1f", help=None)      # money → 1dp
    assert cfg["Val/£m"] == st.column_config.NumberColumn("Val/£m", format="%.1f", help=None)
    assert cfg["Pts"] == st.column_config.NumberColumn("Pts", format="%d", help=None)      # count → integer
    assert cfg["xGI"] == st.column_config.NumberColumn("xGI", format="%.2f", help=None)    # xG family → 2dp
    assert cfg["Diff"] == st.column_config.NumberColumn("Diff", format="%+.1f", help=None)  # signed
    assert cfg["+xP"] == st.column_config.NumberColumn("+xP", format="%+.1f", help=None)


def test_image_text_and_help_columns():
    cfg = column_config(["photo", "badge", "Player", "Rating"], help={"Rating": "vs peers"})
    assert cfg["photo"] == st.column_config.ImageColumn("", width="small")
    assert cfg["badge"] == st.column_config.ImageColumn("", width="small")
    assert "Player" not in cfg                                       # plain text, no help → default render
    assert cfg["Rating"] == st.column_config.Column("Rating", help="vs peers")   # text + help → Column


def test_numeric_help_rides_on_the_numbercolumn():
    cfg = column_config(["xGC/90"], help={"xGC/90": "lower is better"})
    assert cfg["xGC/90"] == st.column_config.NumberColumn("xGC/90", format="%.2f", help="lower is better")


def test_the_convention_covers_the_columns_the_tables_use():
    # A guard so a new numeric column is added to the policy, not left at the Streamlit default.
    assert all(FORMATS[c] == "%.1f" for c in
               ("£m", "Val/£m", "Own%", "Form", "ICT", "xP", "Actual", "Exp", "DC/90", "Thr"))
    assert FORMATS["Pts"] == "%d" and FORMATS["Mins"] == "%d"
    assert all(FORMATS[c] == "%.2f" for c in ("xG", "xA", "xGI", "xGC", "xGC/90"))
    assert all(FORMATS[c] == "%+.1f" for c in ("Diff", "Margin", "+xP"))
