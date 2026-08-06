"""Tests for the shared web paginator's pure helper (ADR-063).

`page_labels` builds the "1–50 / 51–100 / …" range labels; `paginate` (the Streamlit render) is
covered by the AppTest suite (Players / Trending / Player Stats).
"""

from src.web_streamlit.paginate import page_labels


def test_page_labels_covers_all_rows():
    assert page_labels(120, 50) == ["1–50", "51–100", "101–120"]   # last page is short


def test_page_labels_exact_multiple():
    assert page_labels(100, 50) == ["1–50", "51–100"]


def test_page_labels_single_page_and_empty():
    assert page_labels(30, 50) == ["1–30"]
    assert page_labels(0, 50) == ["0–0"]                           # empty → a single benign label
