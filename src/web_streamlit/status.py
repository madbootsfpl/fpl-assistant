"""Data-status controls for the Streamlit edge (ADR-056), shown in the sidebar on every tab.

A **"N players · data as of <date>"** freshness caption (always — the player count makes a stale snapshot
obvious, US-219). On the **cloud** a second caption notes it's a snapshot (updates on redeploy). Plus —
**only when running locally** (the `python -m src.web_streamlit` runner sets `FPL_LOCAL=1`; the read-only
cloud doesn't) and against a real writable cache (not the committed seed) — a **"🔄 Refresh data"** button
that reuses the CLI's `ingest.refresh`. The cloud shows the captions only; it never writes.
"""

import datetime
import os
import sqlite3

import streamlit as st

from src import config, ingest
from src.storage import Storage


def _data_as_of() -> str:
    """The DB file's date — the last refresh locally, or the deploy snapshot's date on the cloud."""
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
        if not is_local():
            # The cloud serves the committed snapshot (ADR-053) — a local refresh never reaches it.
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
