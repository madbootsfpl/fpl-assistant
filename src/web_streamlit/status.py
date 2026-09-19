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
import sqlite3

import streamlit as st

from src import config, ingest
from src.storage import Storage, fallback_reason


def _data_as_of() -> str:
    """When the data was last refreshed — a date, or "unknown".

    ⭐ **Two sources, because the answer stopped being a file** (ADR-211 2b). Against SQLite this is the
    snapshot's mtime, exactly as before. Against Postgres there is no file, and an mtime would be the wrong
    question anyway: it records when something *wrote*, never whether the write was any good. So Postgres
    reports `data_status.refreshed_at` — the last refresh that actually passed — and falls back to "unknown"
    until the scheduled pipeline starts writing it in 2c.
    """
    if config.DATABASE_URL and not fallback_reason():
        try:
            store = Storage()
            try:
                row = store.data_status()
            finally:
                store.close()
            if row and row["refreshed_at"]:
                return str(row["refreshed_at"])[:10]
        except Exception:                      # noqa: BLE001 — a caption must never take the page down
            return "unknown"
        return "unknown"
    try:
        return datetime.date.fromtimestamp(os.path.getmtime(config.DB_PATH)).isoformat()
    except OSError:
        return "unknown"


def _player_count() -> int | None:
    """How many players the current DB holds — shown so a stale snapshot is obvious (US-219).

    A testers' seed can hold fewer players than a fresh CLI refresh; surfacing the count is what makes
    "the app is on the snapshot, not your fresh cache" visible at a glance. Cheap (a COUNT), best-effort.
    """
    try:
        store = Storage()
        try:
            return store.count_players()
        finally:
            store.close()
    except sqlite3.Error:
        return None


def is_local() -> bool:
    """A local run (the runner set `FPL_LOCAL`) against a writable cache — not the read-only seed."""
    return os.environ.get("FPL_LOCAL") == "1" and config.DB_PATH != config.SEED_DB_PATH


def render_data_status() -> None:
    """The sidebar data status: a freshness caption always; a local-only refresh button (ADR-056)."""
    with st.sidebar:
        count = _player_count()
        prefix = f"{count} players · " if count is not None else ""
        st.caption(f"📅 {prefix}data as of {_data_as_of()}")
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
