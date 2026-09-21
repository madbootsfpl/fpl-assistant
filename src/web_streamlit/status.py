"""Data-status controls for the Streamlit edge (ADR-056), shown in the sidebar on every tab.

A **"N players · data as of <date>"** freshness caption (always — the player count makes a stale snapshot
obvious, US-219). On the **cloud** a second caption says how the data gets there: a committed snapshot that
moves on redeploy, or — once `FPL_DATABASE_URL` is set — the pipeline refreshing it through the day
(ADR-211 2f). ⚠️ A third appears as a **warning** when a configured database could not be read. Plus —
**only when running locally** (the `python -m src.web_streamlit` runner sets `FPL_LOCAL=1`; the read-only
cloud doesn't) and against a real writable cache (not the committed seed) — a **"🔄 Refresh data"** button
that reuses the CLI's `ingest.refresh`. The cloud shows the captions only; it never writes.
"""

import datetime
import os

import streamlit as st

from src import config, ingest
from src.storage import Storage, fallback_reason


def _freshness() -> tuple[int | None, str]:
    """The caption's two values — the player count and the refresh date — from **one connection**.

    ⭐⭐ **They used to open one each, and this line renders on every page.** `_player_count` opened a
    `Storage`, counted, closed; `_data_as_of` opened another, read `data_status`, closed. Against a local
    SQLite file that is free. Against Supabase each open is a DNS lookup, a TCP handshake and a TLS
    handshake before any data moves — measured at **50-80 ms more than a warm connection** — and Streamlit
    re-runs the whole script on every click.

    ⚠️ Spike 017 traced three connections per page render and **two of them were this caption**. One line of
    sidebar text was costing two thirds of the connection overhead of the entire page.

    ⭐ The date still has two sources, because the answer stopped being a file (ADR-211 2b): against Postgres
    it is `data_status.refreshed_at` — the last refresh that actually *passed* — and against SQLite it is the
    snapshot's mtime. The SQLite path needs no query at all, so it still makes none.
    """
    count: int | None = None
    as_of: str | None = None
    from_db = bool(config.DATABASE_URL and not fallback_reason())

    try:
        store = Storage()
        try:
            count = store.count_players()
            if from_db:
                row = store.data_status()
                as_of = str(row["refreshed_at"])[:10] if row and row["refreshed_at"] else "unknown"
        finally:
            store.close()
    except Exception:              # noqa: BLE001 — a caption must never take the page down
        pass

    if as_of is None:
        # ⚠️ Not an error path. On SQLite this is the normal route, and an mtime needs no connection. On
        # Postgres `DB_PATH` is a DSN, `getmtime` raises, and "unknown" is the honest answer.
        try:
            as_of = datetime.date.fromtimestamp(os.path.getmtime(config.DB_PATH)).isoformat()
        except OSError:
            as_of = "unknown"

    return count, as_of


def is_local() -> bool:
    """A local run (the runner set `FPL_LOCAL`) against a writable cache — not the read-only seed."""
    return os.environ.get("FPL_LOCAL") == "1" and config.DB_PATH != config.SEED_DB_PATH


def render_data_status() -> None:
    """The sidebar data status: a freshness caption always; a local-only refresh button (ADR-056)."""
    with st.sidebar:
        count, as_of = _freshness()
        prefix = f"{count} players · " if count is not None else ""
        st.caption(f"📅 {prefix}data as of {as_of}")
        # ⭐⭐ **A configured database we could not reach must never degrade quietly.** Serving the committed
        # snapshot is the right thing to do — the app keeps working — but doing it *silently* would leave a
        # dead pipeline looking exactly like a healthy one, which is the failure ADR-211 exists to remove.
        # A caption is not enough for this one: it is a warning.
        if (why := fallback_reason()):
            st.warning(
                "⚠️ **Showing the last snapshot.** The live database could not be read, so this data may be "
                "out of date.", icon="⚠️")
            st.caption(f"Reason: {why}")
        if not is_local():
            # ⭐ **Tell the truth in both states** (ADR-211 2f). Before the cutover the cloud serves the
            # committed snapshot and only a redeploy moves it (ADR-053). After it, the pipeline refreshes the
            # database every few minutes and *"updates when the app is redeployed"* is simply false — a
            # sentence the app would still be saying about itself while behaving differently.
            if config.DATABASE_URL and not fallback_reason():
                st.caption("🔄 Updated automatically — the data pipeline refreshes this through the day.")
            else:
                st.caption("🌐 A data snapshot — updates when the app is redeployed.")
        if is_local() and st.button("🔄 Refresh data"):
            try:
                with st.spinner("Fetching the latest FPL data…"):
                    store = Storage()
                    try:
                        n_players, n_teams, n_fixtures, _ = ingest.refresh(store)
                    finally:
                        store.close()
            except ingest.FplApiError as exc:
                st.error(f"Couldn't refresh: {exc}")
            else:
                st.success(f"Refreshed {n_players} players, {n_teams} teams, {n_fixtures} fixtures.")
                st.rerun()
