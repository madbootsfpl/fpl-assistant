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


@st.cache_data(ttl=TTL, show_spinner=False)
def players() -> list[dict]:
    """Every player, with their club short name. ~518 KB."""
    store = Storage()
    try:
        return [dict(r) for r in store.get_players()]
    finally:
        store.close()


@st.cache_data(ttl=TTL, show_spinner=False)
def teams() -> list[dict]:
    """The twenty clubs. ~2 KB."""
    store = Storage()
    try:
        return [dict(r) for r in store.get_teams()]
    finally:
        store.close()


@st.cache_data(ttl=TTL, show_spinner=False)
def upcoming_fixtures() -> list[dict]:
    """Fixtures still to be played. ~58 KB."""
    store = Storage()
    try:
        return [dict(r) for r in store.get_upcoming_fixtures()]
    finally:
        store.close()


@st.cache_data(ttl=TTL, show_spinner=False)
def all_fixtures() -> list[dict]:
    """Every fixture, played and upcoming."""
    store = Storage()
    try:
        return [dict(r) for r in store.get_all_fixtures()]
    finally:
        store.close()


@st.cache_data(ttl=TTL, show_spinner=False)
def history_by_code() -> dict:
    """Past-season history, keyed by player code. ~747 KB — the second-biggest read."""
    store = Storage()
    try:
        return {code: [dict(r) for r in rows] for code, rows in store.get_history_by_code().items()}
    finally:
        store.close()


@st.cache_data(ttl=TTL, show_spinner=False)
def gw_history_by_code() -> dict:
    """Per-gameweek history, keyed by player code. ~1.2 MB — the biggest single read in the app."""
    store = Storage()
    try:
        return {code: [dict(r) for r in rows] for code, rows in store.get_gw_history_by_code().items()}
    finally:
        store.close()


@st.cache_data(ttl=TTL, show_spinner=False)
def headline_events_by_id() -> dict:
    """ADR-151's stored headline events, keyed by player id. Small, but it was the last read left opening a
    connection on every render of Signals."""
    store = Storage()
    try:
        return {k: list(v) for k, v in store.headline_events_by_id().items()}
    finally:
        store.close()


@st.cache_data(ttl=TTL, show_spinner=False)
def freshness() -> tuple[int | None, str]:
    """The sidebar caption's two values — cached **with the same TTL as the board, on purpose**.

    ⭐⭐ **A caption must describe what is on the screen.** Reading the timestamp live while serving a cached
    board would let it announce a refresh whose data the reader cannot see — which is precisely the
    "fresh-looking but stale" failure ADR-211 exists to prevent, arriving from the opposite direction.
    Sharing the window keeps the claim and the data in step.
    """
    from src.web_streamlit import status
    return status._freshness()


def clear() -> None:
    """Drop every cached read — for the local "🔄 Refresh data" button, which would otherwise refresh the
    database and then render the previous five minutes back at you."""
    for fn in (players, teams, upcoming_fixtures, all_fixtures, history_by_code,
               gw_history_by_code, headline_events_by_id, freshness):
        fn.clear()
