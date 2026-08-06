"""Console rendering for the 'trending' intent (Sprint 067, ADR-057).

Pure formatting: a leaderboard of players by a free crowd metric (own % · net transfers · form) — a
display lens, never xP. Built on the shared table renderer (ADR-025).
"""

from ._table import Col, render_rows

_NAME_W = 17


def render_trending(rows, title: str, value_header: str, by: str = "owned") -> str:
    def _fmt(r):
        v = r.get("trend", 0)
        # net transfers as a signed count (e.g. +123,456); ownership / form to one decimal.
        return f"{int(v):+,}" if by in ("in", "out") else f"{v:.1f}"

    cols = [
        Col("Player", _NAME_W, "<", lambda r: str(r["web_name"])[:_NAME_W]),
        Col("Team", 5, "<", lambda r: str(r["team"] or "")),
        Col("Pos", 4, "<", lambda r: str(r["position"] or "")),
        Col(value_header, 10, ">", _fmt),
    ]
    lines = [title, ""]
    lines += render_rows(rows, cols, rank=True)
    lines += ["", "A community lens from free FPL data (ownership / transfers / form) — not a prediction."]
    return "\n".join(lines)
