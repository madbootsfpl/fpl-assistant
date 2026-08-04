"""Console rendering for the compare intent (ADR-039).

Pure formatting: a side-by-side table of the named players — xMins, xP over the horizon,
next fixture, penalty duty — strongest xP first (the analytics decide the order; the LLM
only narrates). Built on the shared table renderer (ADR-025).
"""

from src.analytics.minutes import expected_minutes

from ._table import Col, render_rows

_NAME_W = 17


def _name(r) -> str:
    name = str(r["web_name"])
    if r.get("status") == "d" and r.get("chance") is not None:
        name = f"{name} (d {r['chance']}%)"
    elif r.get("status") in ("i", "s", "u", "n"):
        name = f"{name} ({r['status']})"
    return name[:_NAME_W]


def _opponent(r) -> str:
    if not r.get("opponent"):
        return "—"
    return f"{r['opponent']} ({r['venue']})"


_COLS = [
    Col("Player", _NAME_W, "<", _name),
    Col("Team", 5, "<", lambda r: str(r["team"] or "")),
    Col("Pos", 4, "<", lambda r: str(r["position"] or "")),
    Col("xMins", 6, ">", lambda r: str(expected_minutes(r.get("minutes_weight")))),
    Col("xP", 6, ">", lambda r: f"{r['xp']:.1f}"),
    Col("Pen", 4, "<", lambda r: "pen" if r.get("penalty_taker") else ""),
    Col("Opponent", 12, "<", _opponent),
]


def render_compare(rows, horizon: int = 5) -> str:
    window = f"{horizon} GW" if horizon != 1 else "next GW"
    lines = [f"Compare — by expected points over the next {window} (xMins-weighted)", ""]
    lines += render_rows(rows, _COLS, rank=True)
    lines += [
        "",
        "`xMins` = expected minutes next GW (xMins v0); `xP` is weighted by it. `pen` = first-choice "
        "penalty taker (already in xP). xP is a mean, not a ceiling.",
    ]
    return "\n".join(lines)
