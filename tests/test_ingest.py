"""Tests for the ingestion service (fetch → map → store).

Uses fake clients (no network) and a temporary database, so it's fully offline.
"""

import json
from pathlib import Path

import pytest

from src import ingest
from src.api.clubelo import ClubEloError
from src.storage import Storage

FIXTURES_DIR = Path(__file__).parent / "fixtures"
BOOTSTRAP = FIXTURES_DIR / "bootstrap_static_sample.json"
FIXTURES = FIXTURES_DIR / "fixtures_sample.json"

# A small Elo CSV whose clubs match the bootstrap sample teams (Arsenal, Aston Villa).
ELO_CSV = (
    "Rank,Club,Country,Level,Elo,From,To\n"
    "1,Arsenal,ENG,1,2000.0,2026-05-31,2026-08-21\n"
    "2,Aston Villa,ENG,1,1900.0,2026-05-31,2026-08-21\n"
)


class FakeClient:
    """Stands in for FplClient — returns saved payloads instead of calling the API."""

    def __init__(self, bootstrap: dict, fixtures: list):
        self._bootstrap = bootstrap
        self._fixtures = fixtures

    def get_bootstrap_static(self) -> dict:
        return self._bootstrap

    def get_fixtures(self) -> list:
        return self._fixtures


class FakeEloClient:
    def __init__(self, csv_text: str):
        self._csv = csv_text

    def get_elo_csv(self, date=None) -> str:
        return self._csv


class FailingEloClient:
    def get_elo_csv(self, date=None) -> str:
        raise ClubEloError("ClubElo down")


def _fpl():
    return FakeClient(json.loads(BOOTSTRAP.read_text()), json.loads(FIXTURES.read_text()))


def test_refresh_maps_and_stores_including_elo(tmp_path):
    bootstrap = json.loads(BOOTSTRAP.read_text())
    fixtures = json.loads(FIXTURES.read_text())
    store = Storage(db_path=str(tmp_path / "test.db"))

    n_players, n_teams, n_fixtures, n_elo = ingest.refresh(
        store,
        client=FakeClient(bootstrap, fixtures),
        elo_client=FakeEloClient(ELO_CSV),
    )

    assert n_players == len(bootstrap["elements"])
    assert n_fixtures == len(fixtures)
    assert n_elo == 2                                       # both teams got Elo
    row = store.conn.execute("SELECT elo FROM teams WHERE id = 1").fetchone()
    assert row["elo"] == 2000.0
    store.close()


def test_refresh_is_graceful_when_clubelo_fails(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))

    # FPL succeeds, ClubElo fails — the refresh must complete, not crash.
    n_players, n_teams, n_fixtures, n_elo = ingest.refresh(
        store, client=_fpl(), elo_client=FailingEloClient()
    )

    assert n_players > 0 and n_teams > 0 and n_fixtures > 0   # FPL data still loaded
    assert n_elo == 0                                          # Elo skipped, no crash
    store.close()
