"""Tests for the ingestion service (fetch → map → store).

Uses a fake client (no network) and a temporary database, so it's fully offline.
"""

import json
from pathlib import Path

from src import ingest
from src.storage import Storage

FIXTURE = Path(__file__).parent / "fixtures" / "bootstrap_static_sample.json"


class FakeClient:
    """Stands in for FplClient — returns a saved payload instead of calling the API."""

    def __init__(self, payload: dict):
        self._payload = payload

    def get_bootstrap_static(self) -> dict:
        return self._payload


def test_refresh_maps_and_stores(tmp_path):
    payload = json.loads(FIXTURE.read_text())
    store = Storage(db_path=str(tmp_path / "test.db"))

    n_players, n_teams = ingest.refresh(store, client=FakeClient(payload))

    # Counts reported match the payload...
    assert n_players == len(payload["elements"])
    assert n_teams == len(payload["teams"])
    # ...and the data actually landed in the database and is readable.
    assert store.count_players() == n_players
    assert store.get_players()[0]["team"] in {"ARS", "AVL"}
    store.close()
