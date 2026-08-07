"""One number-formatting convention for the web tables (ADR-072) — display-only.

The Streamlit tables didn't pin decimals, so money columns went ragged (`24.2345`, `5.5`, `6`). This
formats them consistently with `st.column_config.NumberColumn` — which right-aligns and keeps the column
**numeric + sortable** (a pre-formatted string would left-align and sort lexically). The underlying
analytics value is untouched: this is display, not a round of the data.

`FORMATS` is the single source of the policy; Pool / stat boards / squad tables all build their
`column_config` through `column_config(...)`, so the convention can't drift between tables. It composes
with the ADR-071 tooltips (same `NumberColumn`, with `help=`).
"""

import streamlit as st

# column label → printf format. 1dp for money/%/rates · integer for counts · 2dp for the expected-goals
# family (FPL-native precision; 1dp blurs small ratios) · %+.1f for signed differences.
FORMATS = {
    "£m": "%.1f", "Val/£m": "%.1f", "Own%": "%.1f", "Form": "%.1f", "ICT": "%.1f",
    "xP": "%.1f", "Actual": "%.1f", "Exp": "%.1f", "DC/90": "%.1f", "Thr": "%.1f",
    "Pts": "%d", "Mins": "%d",
    "Pen": "%d", "Corners": "%d", "FK": "%d",        # set-piece order (1 = first-choice), ADR-081
    "xG": "%.2f", "xA": "%.2f", "xGI": "%.2f", "xGC": "%.2f", "xGC/90": "%.2f",
    "Diff": "%+.1f", "Margin": "%+.1f", "+xP": "%+.1f",
}

# Labels whose cells hold an FPL CDN URL → rendered as a thumbnail.
IMAGE_COLS = ("photo", "badge", "out", "in")


def column_config(labels, *, help=None, images=IMAGE_COLS) -> dict:
    """A `{label: column-config}` dict for `st.dataframe`, applying the convention (ADR-072).

    - a numeric label (in `FORMATS`) → `NumberColumn(label, format=…, help=…)` — aligned + sortable;
    - an image label (in `images`) → `ImageColumn("")`;
    - a text label carrying `help` → a plain `Column(label, help=…)` (so a tooltip still shows);
    - any other label → omitted (Streamlit's default rendering).
    """
    help = help or {}
    config = {}
    for label in labels:
        if label in images:
            config[label] = st.column_config.ImageColumn("", width="small")
        elif label in FORMATS:
            config[label] = st.column_config.NumberColumn(
                label, format=FORMATS[label], help=help.get(label))
        elif label in help:
            config[label] = st.column_config.Column(label, help=help[label])
    return config
