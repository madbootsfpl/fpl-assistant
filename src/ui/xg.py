"""Console rendering for the expected-goals (xG / xA / xGI) table.

Pure formatting: it takes player rows (from storage, already sorted by xGI) and returns
a string. xGI = xG + xA is the headline attacking involvement; xGC (goals conceded) is a
defensive counterpoint. Values may be None on a database refreshed before Sprint 014, so
they're coerced to 0.0 for display.

The table shape (header / divider / aligned rows) comes from the shared renderer
(`ui._table`, ADR-025); this module supplies the columns, title, and footer.
"""

from src.analytics import fit_flag

from ._table import Col, render_rows

_NAME_W = 17  # also the truncation width, so it's named


def _n(value) -> float:
    return value or 0.0


_COLS = [
    Col("Player", _NAME_W, "<", lambda r: str(r["web_name"])[:_NAME_W]),
    Col("Team", 5, "<", lambda r: str(r["team"] or "")),
    Col("Pos", 4, "<", lambda r: str(r["position"] or "")),
    Col("xG", 6, ">", lambda r: f"{_n(r['xg']):.1f}"),
    Col("xA", 6, ">", lambda r: f"{_n(r['xa']):.1f}"),
    Col("xGI", 6, ">", lambda r: f"{_n(r['xgi']):.1f}"),
    Col("xGC", 6, ">", lambda r: f"{_n(r['xgc']):.1f}"),
    Col("Fit", 4, "<", fit_flag),   # availability last (ADR-074); ✅ = available
]


def render_xg_table(rows, limit: int = 20, pos: str | None = None) -> str:
    total = len(rows)
    if total == 0:
        return "No players to rank — run `refresh` first."

    lines = render_rows(rows[:limit], _COLS, rank=True)

    lines.append("")
    scope = f" ({pos.upper()})" if pos else ""
    shown = "all" if total <= limit else f"top {limit} of"
    lines.append(f"Showing {shown} {total} players{scope} by xGI (last-season expected goals).")
    return "\n".join(lines)
