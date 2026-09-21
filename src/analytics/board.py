"""Read the published xP board instead of recomputing it (ADR-213 → spike 017).

⭐⭐ **The pipeline already computes this every tick, and the app was downloading 1.9 MB of raw history to
work it out again.** Measured on production: a cold page load moved **2.41 MB** at about **1.8 Mbps** — over
ten seconds — and **81% of it was history fetched only to feed `decision_xp`**.

⚠️ **This does not reimplement the model.** Nothing here computes an xP. The board holds the per-gameweek
values the engine produced; this sums a prefix of them and reassembles the row shape callers expect. The one
recipe stays in `decision_xp`, which is what the pipeline calls (ADR-181).
"""

from src.analytics.xp import apportion


def ranked_from_board(rows, *, horizon: int = 5) -> list[dict]:
    """`decision_xp`'s output shape, reconstructed from the published board.

    ⭐ **Any horizon 1–8 is exact, not approximate** — the board stores *unrounded* per-gameweek values
    precisely so a prefix sums to the same number the engine produces at that horizon (ADR-213). Summing the
    rounded display values would drift, which is the trap that decision documented.

    Returns `[]` when the board is empty, so a caller can tell *"the pipeline has not published"* from
    *"nobody scores"* and fall back to computing.
    """
    out = []
    for row in rows or []:
        per_gw = row.get("by_gameweek") or {}
        gws = sorted(per_gw)[:horizon]
        exact = {gw: per_gw[gw] for gw in gws}
        xp = round(sum(exact.values()), 1)
        games = row.get("games_by_gameweek") or {}
        out.append({
            "id": row["id"],
            "web_name": row["web_name"],
            "team": row["team"],
            "position": row["position"],
            "xp": xp,
            "games": sum(games.get(gw, 0) for gw in gws),
            # ⚠️ **The board's column is REAL because `players.ep_next` is.** It was declared TEXT, which
            # made this the one field that came back a `str` where the engine gives a `float` — same number,
            # different type, and the only thing separating the two paths. ⭐ *A published copy has to match
            # the type as well as the value, or a client comparing them finds a difference that is not one.*
            "ep_next": row.get("ep_next"),
            "difficulty": row.get("difficulty"),
            "rate": row.get("rate"),
            "rate_source": row.get("rate_source"),
            # ⭐ Apportioned, not rounded per cell — so the breakdown sums to the total it is shown beside,
            # exactly as `decision_xp` does it (ADR-213).
            "by_gameweek": apportion(exact, xp),
            "by_gameweek_exact": exact,
            "gameweeks": gws,
            "games_by_gameweek": {gw: games.get(gw, 0) for gw in gws},
            "minutes_weight": row.get("minutes_weight"),
            # ⚠️ Scaled to the horizon. Both are 0 while their weights are dormant, but storing and scaling
            # them means the board does not quietly disagree with the engine the day a weight is raised.
            "defcon_xp": _scaled(row.get("defcon_xp"), len(gws), len(per_gw)),
            "clean_sheet_xp": _scaled(row.get("clean_sheet_xp"), len(gws), len(per_gw)),
        })
    return out


def _scaled(total, used: int, of: int):
    """A horizon-8 total, pro-rated to a shorter horizon.

    ⚠️ **An approximation, and the only one here** — the board stores these as a sum over eight gameweeks
    and the per-gameweek split is not published. It is exact while the terms are dormant (0 scales to 0) and
    approximate the day one is raised, which is the point at which the split should be published too.
    """
    if total is None or not of:
        return total
    return round(total * used / of, 1)


def ranked_for(board, players, upcoming, history, gw_history, *, horizon: int = 5) -> list[dict]:
    """The published board when there is one, a live computation when there is not.

    ⚠️⚠️ **An empty board is a real state, not a test artefact.** The committed snapshot has never had one
    published into it, a fresh project has none until the pipeline's first tick, and ADR-211's fallback
    serves that snapshot whenever Postgres cannot be read. Without this, My Squad would show **zero xP with
    nothing saying why** — the silent-degrade failure that whole ADR exists to prevent.

    ⭐ *Declining is right when the instrument cannot answer; falling back is right when another instrument
    can.* Here one can: the engine that produced the board in the first place.
    """
    if board:
        return ranked_from_board(board, horizon=horizon)
    from src.analytics.xp import decision_xp
    return decision_xp(players, upcoming, history or {}, horizon=horizon,
                       gw_history_by_code=gw_history or {})
