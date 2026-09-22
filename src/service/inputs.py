"""What every squad question needs loading before it can be answered.

⭐⭐ **One assembly, because the alternative has a name in this repo.** ADR-041 is *"one xP recipe"*; ADR-181
is what happens when a shared helper grows an optional argument and one call site quietly opts out. Six
endpoints each assembling their own inputs is that failure waiting with six chances to happen — so the
assembly is here, once, and an endpoint chooses *what to load*, never *how*.

⚠️ **Loading is opt-in per dataset, and that is a cost decision, not tidiness.** `history` + `gw_history` are
1.9 MB (spike 017 measured them at roughly eight of a cold load's eleven seconds). Transfers and routes read
the published board instead (ADR-218); captain and the gameweek plan genuinely need the raw rows, because
`captain_picks` reprices at horizon 1 through `player_xp` rather than reading a precomputed total.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

from src.analytics.board import ranked_for
from src.storage import Storage

# ⭐ The window a one-gameweek tie-break gets to consult (ADR-209/173). Five, because that is the window the
# app's longer read is expressed in everywhere else — and a tie-break that consulted a *different* window
# from the one the page prints would be deciding on a number the reader cannot see.
WIDE = 5

#: ⭐ How many upcoming fixtures a pitch card shows. Three, because a manager deciding whether to hold a
#: player is asking about his **run**, not his Saturday — and because three fits a 70px card without the
#: numbers becoming decoration.
RUN = 3


@dataclass(frozen=True)
class Loaded:
    """The rows and maps an endpoint answers from. Everything optional is `None` when it was not asked for,
    rather than empty — ⭐ *an absent dataset and an empty one must not look the same*, or a missing load
    reads as a squad with no history."""

    players: list
    by_id: dict
    owned: list
    upcoming: list
    ranked: list
    xp_by_id: dict
    horizon_xp: dict | None
    leaving: dict
    history: dict | None = None
    gw_history: dict | None = None
    events: dict | None = None


def reported_leavers(owned, players, store) -> dict:
    """`{id: event}` for owned players the press says are leaving the league (ADR-153/155).

    ⭐⭐ **In the shared layer, because the alternative has been measured.** ADR-151→156 is the record of this
    one fact being re-taught to six surfaces one at a time, every gap found by the owner using the product.

    ⚠️ It reaches further than any "issues" list: `analyse_squad` drops a reported leaver from the
    *captainable* set, `suggest_transfers` prices him out, and `route_to_player` re-ranks around him. An
    endpoint that skipped it would answer confidently and differently from the web app.

    ⚠️ `players` is the **whole board**, not the squad — ADR-210's exodus threshold is the worst tenth of the
    live league distribution, and a tenth of fifteen flags somebody every week.

    ⭐ Never load-bearing. A database built before the events table existed must answer as it did before.
    """
    try:
        from src.analytics.crowd import exodus_detector
        from src.analytics.headlines import leavers

        return leavers(owned, store.headline_events_by_id(), exodus_detector(players),
                       today=datetime.now(UTC).date())
    except Exception:                                    # noqa: BLE001 — a bonus, never a dependency
        return {}


def load(player_ids, horizon, store, *, need_history=False, need_events=False) -> Loaded:
    """Resolve `player_ids` against the market and price everything the horizon needs.

    ⚠️ Raises on an unknown id rather than dropping it. ⭐ *A squad quietly analysed as fourteen players is a
    wrong answer wearing the shape of a right one* — the total is simply lower, and nothing says why.
    """
    players = [dict(p) for p in store.get_players()]
    by_id = {p["id"]: p for p in players}
    missing = [i for i in player_ids if i not in by_id]
    if missing:
        raise ValueError(f"unknown player ids: {missing}")
    owned = [by_id[i] for i in player_ids]

    upcoming = store.get_upcoming_fixtures()
    board = store.get_xp_board()
    # ⚠️ Fetched when the board is empty **or** when a caller needs the raw rows for its own reasons. An
    # empty board is a real state: a fresh project, or the seed served when Postgres cannot be reached.
    want_rows = need_history or not board
    history = store.get_history_by_code() if want_rows else None
    gw_history = store.get_gw_history_by_code() if want_rows else None

    ranked = ranked_for(board, players, upcoming, history, gw_history, horizon=horizon)
    xp_by_id = {r["id"]: r["xp"] for r in ranked}

    # ⭐⭐ **The longer view, supplied so a near-tie can consult it (ADR-209).** Two moves worth +1.2 apiece
    # over one gameweek are a dead heat on the number being ranked; one of them was worth −1.5 over five and
    # the other +3.1. ⚠️ *Deliberately the same squad re-priced, never a second search* — re-running the
    # search could name a different move, and then the two numbers answer different questions (ADR-173).
    horizon_xp = ({r["id"]: r["xp"] for r in
                   ranked_for(board, players, upcoming, history, gw_history, horizon=WIDE)}
                  if horizon < WIDE else None)

    return Loaded(
        players=players, by_id=by_id, owned=owned, upcoming=upcoming,
        ranked=ranked, xp_by_id=xp_by_id, horizon_xp=horizon_xp,
        leaving=reported_leavers(owned, players, store),
        history=history, gw_history=gw_history,
        events=store.headline_events_by_id() if need_events else None,
    )


def opened(store: Storage | None) -> tuple[Storage, bool]:
    """`(store, ours)` — so a caller's connection is never closed underneath it.

    ⚠️ Streamlit passes a **cached** store (ADR-217/219). Closing it would work once and fail on every
    subsequent rerun, one interaction after the cause.
    """
    return (store, False) if store is not None else (Storage(), True)
