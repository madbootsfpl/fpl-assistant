"""Console rendering for captain suggestions (ADR-029).

Pure formatting: takes the annotated picks (from analytics.captain_picks) and shows a
short, explained shortlist — xP, penalty duty, and the opponent/venue — so the manager
sees *why*. Built on the shared table renderer (ui._table, ADR-025).
"""

from ._table import Col, render_rows

_NAME_W = 17


def _name(r) -> str:
    """Player name, with a (chance%) marker appended when the pick is doubtful."""
    name = str(r["web_name"])
    if r.get("doubtful") and r.get("chance") is not None:
        name = f"{name} ({r['chance']}%)"
    return name[:_NAME_W]


def _opponent(r) -> str:
    if not r.get("opponent"):
        return "—"
    return f"{r['opponent']} ({r['venue']})"


_COLS = [
    Col("Player", _NAME_W, "<", _name),
    Col("Team", 5, "<", lambda r: str(r["team"] or "")),
    Col("Pos", 4, "<", lambda r: str(r["position"] or "")),
    Col("xP", 6, ">", lambda r: f"{r['xp']:.1f}"),
    Col("Pen", 4, "<", lambda r: "pen" if r.get("penalty_taker") else ""),
    Col("Opponent", 12, "<", _opponent),
]


def render_captain_picks(picks, squad_name: str | None = None) -> str:
    if not picks:
        base = "No captain candidates"
        if squad_name:
            return f"{base} in squad '{squad_name}' — check the name, or `refresh` first."
        return f"{base} — run `refresh` first (and `history --backfill` for baseline rates)."

    scope = f" from squad '{squad_name}'" if squad_name else ""
    lines = [f"Captain picks{scope} — next gameweek (by xP; goalkeepers excluded)", ""]
    lines += render_rows(picks, _COLS, rank=True)

    lines.append("")
    lines.append(
        "Ranked by expected points next GW. `pen` = first-choice penalty taker (already in "
        "xP — shown to break ties); a doubtful pick shows (chance%). xP is a mean, not a "
        "ceiling — a high-ceiling differential won't always top this list."
    )
    return "\n".join(lines)
