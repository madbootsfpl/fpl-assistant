"""Fixtures → players: a planning lens (US-301).

The Fixtures ticker tells you which *teams* have the easiest runs; when you're planning a new
squad or a wildcard you then want the *players* to buy from them. `target_by_fixtures` composes
that — it takes the already-ranked teams (`team_fdr`, easiest-first) and the already-computed
`xp_by_id` (the one `decision_xp` metric, ADR-041) and returns the best **available** players from
the top-run teams. Pure display composition: no analytics change, no new xP.
"""

from collections import defaultdict

from src.analytics.crowd import fit_flag
from src.analytics.optimizer import is_unavailable


def target_by_fixtures(team_ranked, players, xp_by_id, *, position=None,
                       top_teams: int = 6, per_team: int = 3) -> list[dict]:
    """The best available players to buy from the easiest-run teams (a planning lens).

    `team_ranked` is `team_fdr(...)` output (easiest run first). For the first `top_teams`, take
    that team's players — optionally filtered to `position` (one of GK/DEF/MID/FWD; `None`/"All"
    keeps every position) — drop the unavailable (🚑/🚫/⛔; a *doubtful* player stays, carrying its
    Fit), rank by `xp_by_id`, and keep the top `per_team`. Returns a flat list of rows, ordered
    easiest-team-first then xP-desc, each:
    `{team, avg_difficulty, opponents, id, web_name, position, price, selected_by, fit, xp}`.
    """
    by_team: dict = defaultdict(list)
    for p in players:
        if is_unavailable(p):
            continue
        if position and position != "All" and p["position"] != position:
            continue
        by_team[p["team"]].append(p)

    rows = []
    for t in team_ranked[:top_teams]:
        pool = sorted(by_team.get(t["team"], []),
                      key=lambda p: xp_by_id.get(p["id"], 0.0), reverse=True)
        for p in pool[:per_team]:
            rows.append({
                "team": t["team"],
                "avg_difficulty": t["avg_difficulty"],
                "opponents": t["opponents"],
                "id": p["id"],
                "web_name": p["web_name"],
                "position": p["position"],
                "price": p["price"],
                "selected_by": p["selected_by"],
                "fit": fit_flag(p),
                "xp": round(xp_by_id.get(p["id"], 0.0), 1),
            })
    return rows
