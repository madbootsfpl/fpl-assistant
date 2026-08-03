"""Tests for the shared table renderer (ui._table, ADR-025).

These pin the *mechanics* the five ranking views depend on: fixed-width padding,
per-column alignment, the optional rank column (restarting each call), and the
optional divider. The seam is that `fmt` produces the finished string and the
renderer only pads — so these tests check padding/alignment, not formatting.
"""

from src.ui._table import Col, render_rows

COLS = [
    Col("Player", 8, "<", lambda r: str(r["name"])),
    Col("Pts", 5, ">", lambda r: str(r["pts"])),
]
ROWS = [{"name": "Salah", "pts": 12}, {"name": "Haaland", "pts": 9}]


def test_header_and_divider_are_padded_and_aligned():
    lines = render_rows(ROWS, COLS)
    # left-aligned text header, right-aligned number header, single-space join
    assert lines[0] == f"{'Player':<8} {'Pts':>5}"
    assert lines[1] == f"{'-' * 8} {'-' * 5}"


def test_rows_pad_to_width_with_alignment():
    lines = render_rows(ROWS, COLS)
    assert lines[2] == f"{'Salah':<8} {'12':>5}"
    assert lines[3] == f"{'Haaland':<8} {'9':>5}"


def test_rank_prepends_a_numbered_column_from_one():
    lines = render_rows(ROWS, COLS, rank=True)
    assert lines[0].startswith(f"{'#':<3} ")
    assert lines[1].startswith(f"{'-' * 3} ")
    assert lines[2].startswith(f"{'1':<3} ")
    assert lines[3].startswith(f"{'2':<3} ")


def test_rank_restarts_at_one_each_call():
    # two-section views (overperf) call render_rows once per section
    first = render_rows(ROWS, COLS, rank=True, divider=False)
    second = render_rows(ROWS, COLS, rank=True, divider=False)
    assert first[1].startswith("1  ") and second[1].startswith("1  ")


def test_divider_false_omits_the_dashes():
    lines = render_rows(ROWS, COLS, divider=False)
    assert lines[0] == f"{'Player':<8} {'Pts':>5}"
    assert lines[1] == f"{'Salah':<8} {'12':>5}"  # rows follow the header directly


def test_fmt_output_is_padded_verbatim_not_truncated():
    # the renderer only pads; an over-wide cell is left as-is (truncation is fmt's job)
    cols = [Col("X", 3, "<", lambda r: r["v"])]
    lines = render_rows([{"v": "toolong"}], cols)
    assert lines[2] == "toolong"  # not clipped to width 3


def test_empty_rows_still_yields_header_and_divider():
    lines = render_rows([], COLS)
    assert len(lines) == 2
