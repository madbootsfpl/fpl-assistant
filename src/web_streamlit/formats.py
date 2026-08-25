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

from src.analytics.price import PRICE_DOWN, PRICE_UP

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


# Green up, red down (ADR-140). `st.dataframe` renders **plain text** in cells — `st.column_config.TextColumn`
# has no colour, and `MarkdownColumn` only renders its markdown in a click-through overlay, not in the cell —
# so `:green[▲]` is not an option here. A pandas **Styler** is: Streamlit applies its `color` CSS per cell,
# and it composes with `column_config` (ImageColumn thumbnails and NumberColumn formats both survive).
#
# Only the *cell* can be coloured, not part of a string. That is why this colours the forward-looking **Price**
# column and not the retrospective 💰↑/💸↓, which shares a cell with the other Trends flags.
_PRICE_CSS = {PRICE_UP: "color:#16a34a;font-weight:700", PRICE_DOWN: "color:#dc2626;font-weight:700"}


def colour_price(rows, column: str = "Price"):
    """`rows` as a Styler that paints the price arrows green-up / red-down — or `rows` unchanged.

    Returns the input untouched when there is nothing to paint (no rows, or no such column), so a caller can
    hand the result straight to `st.dataframe` without asking which it got. Degrading to an uncoloured table
    is the right failure: the glyphs still carry direction by shape.
    """
    if not rows or column not in rows[0]:
        return rows
    import pandas as pd

    frame = pd.DataFrame(rows)
    return frame.style.map(lambda v: _PRICE_CSS.get(v, ""), subset=[column])
