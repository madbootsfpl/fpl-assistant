"""Shared pagination for the Streamlit edge (ADR-063).

Page through long lists (Players · Trending · Player Stats) without a 50/30 cap: a page selectbox
("1–50", "51–100", …) + a "Showing X–Y of N" caption, returning the current page's slice. `page_labels`
is pure (unit-tested); `paginate` renders the control. Display-only — it never mutates the input.
"""

import streamlit as st


def page_labels(total: int, per_page: int) -> list[str]:
    """Human page-range labels ("1–50", "51–100", …) covering `total` rows (≥ one label)."""
    if total <= 0:
        return ["0–0"]
    labels = []
    start = 1
    while start <= total:
        end = min(start + per_page - 1, total)
        labels.append(f"{start}–{end}")
        start += per_page
    return labels


def paginate(rows, *, key: str, per_page: int = 50, label: str = "Page") -> list:
    """Render a page control over `rows` and return the current page's slice (ADR-063).

    `len(rows) ≤ per_page` → no control, just a count caption. Each caller passes a unique `key`
    so pages on different tabs/boards don't collide.
    """
    total = len(rows)
    if total <= per_page:
        st.caption(f"{total} shown")
        return list(rows)
    labels = page_labels(total, per_page)
    choice = st.selectbox(label, labels, key=key,
                          help=f"Jump to a page — {per_page} rows at a time (there are {total}).")
    idx = labels.index(choice)
    start = idx * per_page
    end = min(start + per_page, total)
    st.caption(f"Showing {start + 1}–{end} of {total}")
    return list(rows[start:end])
