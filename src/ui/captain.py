"""Console rendering for captain suggestions (ADR-029).

Pure formatting: takes the annotated picks (from analytics.captain_picks) and shows a
short, explained shortlist — xP, penalty duty, and the opponent/venue — so the manager
sees *why*. Built on the shared table renderer (ui._table, ADR-025).
"""

from src.analytics.minutes import expected_minutes

from ._table import Col, render_rows
from .explain import MODEL_NOTE, render_explanation

_NAME_W = 17
_MEDALS = ("🥇", "🥈", "🥉")


def render_captain_pick(ranked, explanation, *, scope: str = "", team_names=None) -> str:
    """The structured **Captain Pick** card (ADR-089, US-277) — the mockup a tester asked for.

    A medal pick (`Team · Pos` · `Projected: N pts`), a clean Confidence line, the grounded Why (✓) / Risks
    (⚠) from the `Explanation`, the runner-up **Alternatives** (🥈/🥉 + their xP), and the shared Model note.
    `ranked` is the `captain_picks` list already sliced so `[0]` is the chosen pick (its runner-ups are the
    alternatives); `team_names` maps a team short code → a friendly name ("MUN" → "Man Utd"). Pure/empty-safe.
    """
    if not ranked:
        return "No captain candidates — run `refresh` first."
    top = ranked[0]
    team = (team_names or {}).get(top.get("team"), top.get("team") or "")
    lines = ["Captain Pick"]
    if scope:
        lines.append(scope)
    lines += [
        "",
        f"🥇 {top['web_name']}",
        f"{team} · {top.get('position') or ''}",
        f"Projected: {top['xp']:.1f} pts",
    ]
    if explanation is not None:
        lines += ["", f"Confidence: {explanation.confidence}/100 ({explanation.band})"]
        if explanation.reasons:
            lines += ["", "Why", *[f"✓ {r}" for r in explanation.reasons]]
        if explanation.risks:
            lines += ["", "Risks", *[f"⚠ {r}" for r in explanation.risks]]
    alternatives = ranked[1:3]
    if alternatives:
        lines += ["", "Alternatives"]
        lines += [f"{_MEDALS[i + 1]} {a['web_name']} {a['xp']:.1f} pts"
                  for i, a in enumerate(alternatives)]
    lines += ["", MODEL_NOTE]
    return "\n".join(lines)


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


_XMINS_COL = Col("xMins", 6, ">", lambda r: str(expected_minutes(r.get("minutes_weight"))))

_COLS = [
    Col("Player", _NAME_W, "<", _name),
    Col("Team", 5, "<", lambda r: str(r["team"] or "")),
    Col("Pos", 4, "<", lambda r: str(r["position"] or "")),
    Col("xP", 6, ">", lambda r: f"{r['xp']:.1f}"),
    Col("Pen", 4, "<", lambda r: "pen" if r.get("penalty_taker") else ""),
    Col("Opponent", 12, "<", _opponent),
]


def render_captain_picks(picks, squad_name: str | None = None, show_xmins: bool = False,
                         explanation=None) -> str:
    if not picks:
        base = "No captain candidates"
        if squad_name:
            return f"{base} in squad '{squad_name}' — check the name, or `refresh` first."
        return f"{base} — run `refresh` first (and `history --backfill` for baseline rates)."

    # xMins v0 (ADR-038): show the expected-minutes column, and weight xP by it, when on.
    cols = [_COLS[0], _COLS[1], _COLS[2], _XMINS_COL, *_COLS[3:]] if show_xmins else _COLS

    scope = f" from squad '{squad_name}'" if squad_name else ""
    lines = []
    if explanation is not None:   # the Why/Risk/Confidence for the top pick (ADR-089), above the shortlist
        lines += [f"Captain: {picks[0]['web_name']}", "", render_explanation(explanation), ""]
    lines += [f"Captain picks{scope} — next gameweek (by xP; goalkeepers excluded)", ""]
    lines += render_rows(picks, cols, rank=True)

    lines.append("")
    note = (
        "`xMins` = expected minutes next GW (xMins v0); xP is weighted by it. "
        if show_xmins else ""
    )
    lines.append(
        f"Ranked by expected points next GW. {note}`pen` = first-choice penalty taker (already "
        "in xP — shown to break ties); a doubtful pick shows (chance%). xP is a mean, not a "
        "ceiling — a high-ceiling differential won't always top this list."
    )
    return "\n".join(lines)
