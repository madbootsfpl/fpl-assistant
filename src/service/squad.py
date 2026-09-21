"""Squad-shaped questions: the ones whose input is *this user's fifteen players*.

⭐ **The client sends player ids, never player rows** (audit §4.2). Uploading rows would put the client in
the position of defining the engine's input, which is how two implementations of one rule appear — this
codebase has three ADRs about exactly that (123, 127, 181). The server loads the board; the client says who.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.analytics import analyse_squad, best_legal_xi
from src.analytics.board import ranked_for
from src.storage import Storage

DEFAULT_HORIZON = 5


@dataclass(frozen=True)
class SquadRequest:
    """What a client sends. Ids and options — nothing the server could work out for itself.

    ⚠️ `bench_ids` is optional because a squad may not have declared one; the engine derives the best legal
    XI when it is absent, which is what every existing caller already relies on.
    """

    player_ids: list[int]
    bench_ids: list[int] = field(default_factory=list)
    horizon: int = DEFAULT_HORIZON

    def validate(self) -> None:
        """Reject what the engine would otherwise mis-answer rather than refuse.

        ⭐ A squad of nine does not raise inside `analyse_squad` — it returns an analysis of nine players,
        which reads like an answer. *The checks that matter are the ones whose absence produces a plausible
        result.*
        """
        if not self.player_ids:
            raise ValueError("no players given")
        if len(set(self.player_ids)) != len(self.player_ids):
            raise ValueError("duplicate player ids")
        if not 1 <= self.horizon <= 8:
            raise ValueError(f"horizon {self.horizon} is outside 1-8")
        stray = set(self.bench_ids) - set(self.player_ids)
        if stray:
            raise ValueError(f"bench ids not in the squad: {sorted(stray)}")


def analysis(request: SquadRequest, *, store: Storage | None = None) -> dict:
    """A squad's health over the horizon — the shape `analyse_squad` returns, plus what the caller asked.

    ⭐ **Reads the published board, and computes only if there is not one** (ADR-218). On a server that is a
    ~250 KB local read instead of 1.9 MB of history; the fallback exists because an empty board is a real
    state — a fresh project, or the snapshot served when Postgres cannot be read.
    """
    request.validate()
    own_store = store is None
    store = store or Storage()
    try:
        players = [dict(p) for p in store.get_players()]
        by_id = {p["id"]: p for p in players}
        missing = [i for i in request.player_ids if i not in by_id]
        if missing:
            # ⭐ Named, not silently dropped. A squad quietly analysed as fourteen players is a wrong answer
            # wearing the shape of a right one.
            raise ValueError(f"unknown player ids: {missing}")
        owned = [by_id[i] for i in request.player_ids]

        board = store.get_xp_board()
        # ⚠️ Only fetched when the board is empty. On a server the cost is small; the habit is not.
        history = store.get_history_by_code() if not board else None
        gw_history = store.get_gw_history_by_code() if not board else None
        ranked = ranked_for(board, players, store.get_upcoming_fixtures(), history, gw_history,
                            horizon=request.horizon)
        leaving = _reported_leavers(owned, players, store)
    finally:
        if own_store:
            store.close()

    xp_by_id = {r["id"]: r["xp"] for r in ranked}
    by_gameweek_by_id = {r["id"]: r["by_gameweek"] for r in ranked}
    weight_by_id = {r["id"]: r["minutes_weight"] for r in ranked}
    gameweeks = ranked[0]["gameweeks"] if ranked else []

    xi_ids = ([i for i in request.player_ids if i not in set(request.bench_ids)]
              if request.bench_ids else best_legal_xi(owned, xp_by_id))

    return analyse_squad(owned, xi_ids, xp_by_id, horizon=request.horizon,
                         by_gameweek_by_id=by_gameweek_by_id, gameweeks=gameweeks,
                         weight_by_id=weight_by_id, reported_out=leaving)


def _reported_leavers(owned, players, store) -> dict:
    """`{id: event}` for owned players the press says are leaving the league (ADR-153/155).

    ⭐⭐ **In the contract rather than in one view, because the alternative has already been measured.**
    ADR-151→156 is the record of this single fact being re-taught to six surfaces one at a time, every gap
    found by the owner using the product — a Health tab that reported *"Availability issues: 1"* on a squad
    whose most consequential problem was a player with an agreed move to Al-Hilal.

    ⚠️ It reaches further than the issues list: `analyse_squad` also drops a reported leaver from the
    *captainable* set. Left out here, a phone would recommend captaining a player the web app already knows
    is going, and nothing would look broken on either.

    ⚠️ `players` is the **whole board**, not the squad — the exodus threshold is the worst tenth of the live
    league distribution (ADR-210), and a tenth of fifteen owned players flags somebody every week.

    ⭐ Never load-bearing. A database built before the events table existed, or one whose headlines were
    never extracted, must answer exactly as it did before rather than fail.
    """
    try:
        from src.analytics.crowd import exodus_detector
        from src.analytics.headlines import leavers

        return leavers(owned, store.headline_events_by_id(), exodus_detector(players),
                       today=datetime.now(UTC).date())
    except Exception:                                    # noqa: BLE001 — a bonus, never a dependency
        return {}
