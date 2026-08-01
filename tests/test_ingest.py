"""Tests for the ingestion service (fetch → map → store).

Uses a fake client (no network) and a temporary database, so it's fully offline.
"""

import json
from pathlib import Path

from src import ingest
from src.storage import Storage

FIXTURES_DIR = Path(__file__).parent / "fixtures"
BOOTSTRAP = FIXTURES_DIR / "bootstrap_static_sample.json"
FIXTURES = FIXTURES_DIR / "fixtures_sample.json"


class FakeClient:
    """Stands in for FplClient — returns saved payloads instead of calling the API."""

    def __init__(self, bootstrap: dict, fixtures: list):
        self._bootstrap = bootstrap
        self._fixtures = fixtures

    def get_bootstrap_static(self) -> dict:
        return self._bootstrap

    def get_fixtures(self) -> list:
        return self._fixtures


def test_refresh_maps_and_stores(tmp_path):
    bootstrap = json.loads(BOOTSTRAP.read_text())
    fixtures = json.loads(FIXTURES.read_text())
    store = Storage(db_path=str(tmp_path / "test.db"))

    n_players, n_teams, n_fixtures = ingest.refresh(
        store, client=FakeClient(bootstrap, fixtures)
    )

    # Counts reported match the payloads...
    assert n_players == len(bootstrap["elements"])
    assert n_teams == len(bootstrap["teams"])
    assert n_fixtures == len(fixtures)
    # ...and the data actually landed in the database.
    assert store.count_players() == n_players
    assert store.count_fixtures() == n_fixtures
    store.close()
