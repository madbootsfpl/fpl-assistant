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


# ⭐⭐ **Each loader fetches only itself, and that reverses a change made two hours earlier.**
#
# A bundle was introduced so one connection filled the whole cache, on the reasoning that six connections at
# ~1,950 ms each were the cold load. Production then showed the cold load **unchanged at 10.786 s** — so
# handshakes were never the cost. The real figure is **2.41 MB at about 1.8 Mbps**, and a bundle cannot make
# a payload smaller. What it *did* do was force every page to fetch everything, which is exactly what stops
# a page from not fetching what it does not read.
#
# ⭐ *An optimisation that was never measured to work, and which blocks the one that does, is not a
# trade-off — it is just in the way.*
def _rows(fetch):
    """Open one connection, fetch, close."""
    store = Storage()
    try:
        return fetch(store)
    finally:
        store.close()


@st.cache_data(ttl=TTL, show_spinner=False)
def players() -> list[dict]:
    """Every player, with their club short name. ~518 KB."""
    return _rows(lambda s: [dict(r) for r in s.get_players()])


@st.cache_data(ttl=TTL, show_spinner=False)
def teams() -> list[dict]:
    """The twenty clubs. ~2 KB."""
    return _rows(lambda s: [dict(r) for r in s.get_teams()])


@st.cache_data(ttl=TTL, show_spinner=False)
def upcoming_fixtures() -> list[dict]:
    """Fixtures still to be played. ~58 KB."""
    return _rows(lambda s: [dict(r) for r in s.get_upcoming_fixtures()])


@st.cache_data(ttl=TTL, show_spinner=False)
def all_fixtures() -> list[dict]:
    """Every fixture, played and upcoming."""
    return _rows(lambda s: [dict(r) for r in s.get_all_fixtures()])


@st.cache_data(ttl=TTL, show_spinner=False)
def history_by_code() -> dict:
    """Past-season history, keyed by player code. **~747 KB** — ask for it only if you read it."""
    return _rows(lambda s: {c: [dict(r) for r in rows] for c, rows in s.get_history_by_code().items()})


@st.cache_data(ttl=TTL, show_spinner=False)
def gw_history_by_code() -> dict:
    """Per-gameweek history, keyed by player code. **~1.2 MB** — the biggest read in the app."""
    return _rows(lambda s: {c: [dict(r) for r in rows] for c, rows in s.get_gw_history_by_code().items()})


@st.cache_data(ttl=TTL, show_spinner=False)
def xp_board() -> list[dict]:
    """The published xP board — ~250 KB, against the 1.9 MB of history it replaces.

    ⭐⭐ **The pipeline already computed this.** `analytics.board.ranked_from_board` reassembles
    `decision_xp`'s row shape from it — verified field-for-field identical at every horizon 1–8.
    """
    return _rows(lambda s: s.get_xp_board())


@st.cache_data(ttl=TTL, show_spinner=False)
def headline_events_by_id() -> dict:
    """ADR-151's stored headline events, keyed by player id."""
    return _rows(lambda s: {k: list(v) for k, v in s.headline_events_by_id().items()})


@st.cache_data(ttl=TTL, show_spinner=False)
def freshness() -> tuple[int | None, str]:
    """The sidebar caption's two values — cached **with the same TTL as the board, on purpose**.

    ⭐⭐ **A caption must describe what is on the screen.** Reading the timestamp live while serving a cached
    board would let it announce a refresh whose data the reader cannot see — the *fresh-looking but stale*
    failure ADR-211 exists to prevent, arriving from the opposite direction.
    """
    from src.web_streamlit import status
    return _rows(status.freshness_from)


def clear() -> None:
    """Drop every cached read — for the local "🔄 Refresh data" button, which would otherwise refresh the
    database and then render the previous five minutes back at you."""
    for fn in (players, teams, upcoming_fixtures, all_fixtures, history_by_code,
               gw_history_by_code, xp_board, headline_events_by_id, freshness):
        fn.clear()
