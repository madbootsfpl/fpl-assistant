"""Data-status controls for the Streamlit edge (ADR-056), shown in the sidebar on every tab.

A **"Data as of <date>"** freshness caption (always), plus — **only when running locally** (the
`python -m src.web_streamlit` runner sets `FPL_LOCAL=1`; the read-only cloud doesn't) and against a real
writable cache (not the committed seed) — a **"🔄 Refresh data"** button that reuses the CLI's
`ingest.refresh`. The cloud shows the caption only; it never writes.
"""

import datetime
import os

import streamlit as st

from src import config, ingest
from src.storage import Storage


def _data_as_of() -> str:
    """The DB file's date — the last refresh locally, or the deploy snapshot's date on the cloud."""
    try:
        return datetime.date.fromtimestamp(os.path.getmtime(config.DB_PATH)).isoformat()
    except OSError:
        return "unknown"


def is_local() -> bool:
    """A local run (the runner set `FPL_LOCAL`) against a writable cache — not the read-only seed."""
    return os.environ.get("FPL_LOCAL") == "1" and config.DB_PATH != config.SEED_DB_PATH


def render_data_status() -> None:
    """The sidebar data status: a freshness caption always; a local-only refresh button (ADR-056)."""
    with st.sidebar:
        st.caption(f"📅 Data as of {_data_as_of()}")
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
