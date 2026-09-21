"""The app's cached read path (spike 017).

⭐⭐ **Streamlit re-runs the whole script on every interaction**, so before this every click re-fetched the
board. That cost nothing against a local SQLite file and a great deal against Supabase: production's
`data_load` p50 went from **16 ms** to **3,026 ms** when the app switched to Postgres on 2026-09-20, and the
cause was **volume** — 2.41 MB per render — not round-trips.

So the fix is not to make the fetch faster. It is to stop doing it on every click.

⚠️ **Rows become dicts here, and they have to.** `st.cache_data` pickles what it returns and `sqlite3.Row`
cannot be pickled. Checked before relying on it: nothing in the app indexes a player, team or fixture row
positionally, so `dict` is a drop-in for `Row` at every call site.

⭐ **Mutation is safe, and that was verified rather than assumed**: `st.cache_data` hands each caller its own
copy, so `render_build`'s `p["xp"] = …` cannot poison the cache for the next visitor. (The optimiser also
returns fresh dicts, so it never touches these lists at all — belt and braces, both checked.)
"""

import streamlit as st

from src.storage import Storage

# ⭐⭐ **The freshness trade, stated as a number.** The pipeline refreshes at most every 10 minutes even
# mid-gameweek (ADR-211's cadence: in-play 10 min · the hour before a deadline 15 min · ordinary 1 h ·
# overnight 6 h). At 5 minutes a reader is never more than half a tick behind what was published, and the
# first visitor after expiry pays the fetch on everyone's behalf.
#
# ⚠️ **This is a product decision wearing a constant.** Lower it and the app is slower and fresher; raise it
# and the reverse. It is one number, in one place, deliberately.
TTL = 300


# ⭐⭐ **One connection fills the cache, not six.** Each loader used to open its own `Storage`, which cost
# nothing locally and **~1,950 ms per connection** from Streamlit Cloud — measured from production, after
# ADR-217 priced the same trade at ~30 ms using a laptop. Six opens turned a 3-second cold load into an
# 11-second one.
#
# ⚠️ **The cost of bundling, stated:** a cold miss now fetches all 2.41 MB even if the visitor landed on
# Signals or Trending, which need only 0.5 MB of it. That is ~1.5 s of transfer against ~7.8 s of
# handshakes, once per TTL, and four of the six pages need the whole thing anyway.
#
# ⭐ The per-dataset functions below stay cached individually, so a **warm** call unpickles only its own
# slice — `teams()` costs 2 KB, not 2.41 MB.
@st.cache_data(ttl=TTL, show_spinner=False)
def _everything() -> dict:
    """Every board-wide read, over a single connection. The cold path, and the only thing that opens one."""
    from src.web_streamlit import status

    store = Storage()
    try:
        return {
            "players": [dict(r) for r in store.get_players()],
            "teams": [dict(r) for r in store.get_teams()],
            "upcoming_fixtures": [dict(r) for r in store.get_upcoming_fixtures()],
            "all_fixtures": [dict(r) for r in store.get_all_fixtures()],
            "history_by_code": {c: [dict(r) for r in rows]
                                for c, rows in store.get_history_by_code().items()},
            "gw_history_by_code": {c: [dict(r) for r in rows]
                                   for c, rows in store.get_gw_history_by_code().items()},
            "headline_events_by_id": {k: list(v) for k, v in store.headline_events_by_id().items()},
            "freshness": status.freshness_from(store),
        }
    finally:
        store.close()


@st.cache_data(ttl=TTL, show_spinner=False)
def players() -> list[dict]:
    """Every player, with their club short name. ~518 KB."""
    return _everything()["players"]


@st.cache_data(ttl=TTL, show_spinner=False)
def teams() -> list[dict]:
    """The twenty clubs. ~2 KB."""
    return _everything()["teams"]


@st.cache_data(ttl=TTL, show_spinner=False)
def upcoming_fixtures() -> list[dict]:
    """Fixtures still to be played. ~58 KB."""
    return _everything()["upcoming_fixtures"]


@st.cache_data(ttl=TTL, show_spinner=False)
def all_fixtures() -> list[dict]:
    """Every fixture, played and upcoming."""
    return _everything()["all_fixtures"]


@st.cache_data(ttl=TTL, show_spinner=False)
def history_by_code() -> dict:
    """Past-season history, keyed by player code. ~747 KB."""
    return _everything()["history_by_code"]


@st.cache_data(ttl=TTL, show_spinner=False)
def gw_history_by_code() -> dict:
    """Per-gameweek history, keyed by player code. ~1.2 MB — the biggest single read."""
    return _everything()["gw_history_by_code"]


@st.cache_data(ttl=TTL, show_spinner=False)
def headline_events_by_id() -> dict:
    """ADR-151's stored headline events, keyed by player id."""
    return _everything()["headline_events_by_id"]


@st.cache_data(ttl=TTL, show_spinner=False)
def freshness() -> tuple[int | None, str]:
    """The sidebar caption's two values — cached **with the same TTL as the board, on purpose**.

    ⭐⭐ **A caption must describe what is on the screen.** Reading the timestamp live while serving a cached
    board would let it announce a refresh whose data the reader cannot see — which is precisely the
    "fresh-looking but stale" failure ADR-211 exists to prevent, arriving from the opposite direction.
    """
    return _everything()["freshness"]


def clear() -> None:
    """Drop every cached read — for the local "🔄 Refresh data" button, which would otherwise refresh the
    database and then render the previous five minutes back at you."""
    for fn in (_everything, players, teams, upcoming_fixtures, all_fixtures,
               history_by_code, gw_history_by_code, headline_events_by_id, freshness):
        fn.clear()
