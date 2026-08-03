"""A shared renderer for the fixed-width console ranking tables (ADR-025).

The ranking views — table, xg, overperf, defcon, cleansheet — all build the same
shape: a header line, a divider, then rows of fixed-width, aligned cells. This module
holds that shape once. A view describes its columns as `Col` specs and calls
`render_rows`; its title and footer stay in the view.

The seam that keeps output byte-identical (ADR-025): each column's `fmt(row)` returns
the *finished* cell string — including any truncation and number formatting — and
`render_rows` does nothing but pad each string to its width and join with a single
space. It never truncates and never formats numbers, so every per-view quirk (an
ellipsis, a `.2f`, a signed `+.1f`) lives in that view's specs, not in the core.
"""

_RANK_W = 3  # width of the leading "#" column, shared by every ranking view


class Col:
    """One table column: a header, a fixed width, an alignment, and a cell formatter.

    `align` is "<" (left, for text) or ">" (right, for numbers) and applies to both the
    header and the cells. `fmt` takes a row (a mapping) and returns the finished cell
    string — do any truncation or number formatting there, never in the renderer.
    """

    def __init__(self, header: str, width: int, align: str, fmt):
        self.header = header
        self.width = width
        self.align = align
        self.fmt = fmt


def _pad(text: str, width: int, align: str) -> str:
    return f"{text:<{width}}" if align == "<" else f"{text:>{width}}"


def render_rows(rows, columns, *, rank: bool = False, divider: bool = True) -> list[str]:
    """Render a table body as lines: `[header, (divider), *row lines]`.

    With `rank=True`, a left-aligned "#" column is prepended and numbered from 1 — it
    restarts each call, so a two-section view (e.g. overperf) numbers each section
    independently. With `divider=False`, the "---" line is omitted. Titles and footers
    are the caller's job; this renders only the header, divider, and rows.
    """
    def join(cells) -> str:
        return " ".join(_pad(c, col.width, col.align) for c, col in zip(cells, columns))

    header = join(col.header for col in columns)
    divider_line = join("-" * col.width for col in columns)
    if rank:
        header = _pad("#", _RANK_W, "<") + " " + header
        divider_line = _pad("-" * _RANK_W, _RANK_W, "<") + " " + divider_line

    lines = [header]
    if divider:
        lines.append(divider_line)
    for i, row in enumerate(rows, start=1):
        body = join(col.fmt(row) for col in columns)
        lines.append(_pad(str(i), _RANK_W, "<") + " " + body if rank else body)
    return lines
