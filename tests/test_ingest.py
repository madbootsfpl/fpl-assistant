"""Tests for the ingestion service (fetch → map → store).

Uses fake clients (no network) and a temporary database, so it's fully offline.
"""

import json
from pathlib import Path

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


# ⭐ **The sample payload holds 2 players and 2 teams, and a real FPL response never could.** ADR-211 2c
# added validation to `refresh` — unconditionally, because an opt-out on a shared helper is how one call site
# ends up behaving differently from every other (ADR-181) — and these tests promptly failed, which is the
# validation working: they had been exercising the ingest path on a payload production cannot produce.
#
# ⚠️ **The fixture is padded, not the check loosened.** The named players and teams the tests assert on are
# kept exactly as they were and the rest is filler, so every assertion below still means what it meant —
# the payload merely stops being one validation would (correctly) refuse.
# ⭐ *A fixture that models less than reality will confirm a broken mechanism.*
def _realistic(bootstrap: dict) -> dict:
    """The sample payload, padded to a plausible size: 20 teams and 650 players."""
    teams = list(bootstrap["teams"])
    for i in range(len(teams) + 1, 21):
        teams.append({"id": i, "name": f"Club {i}", "short_name": f"C{i:02d}"})
    elements = list(bootstrap["elements"])
    next_id = max(e["id"] for e in elements) + 1
    for i in range(len(elements), 650):
        elements.append({"id": next_id + i, "first_name": "Filler", "second_name": f"Player {i}",
                         "web_name": f"Filler{i}", "team": 1, "element_type": 3,
                         "now_cost": 45, "total_points": 0})
    return {**bootstrap, "teams": teams, "elements": elements}


def _fpl():
    return FakeClient(_realistic(json.loads(BOOTSTRAP.read_text())), json.loads(FIXTURES.read_text()))


def test_refresh_maps_and_stores_including_elo(tmp_path):
    bootstrap = _realistic(json.loads(BOOTSTRAP.read_text()))
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


def _fpl_with_codes():
    """⚠️ **The shared bootstrap sample carries no `code`**, and availability is keyed on it.

    Left alone, the wiring test below would assert "every player has an observation" against **zero** players
    and pass whatever the code did — ⭐ *a fixture that cannot express the field under test turns the guard
    into decoration.* Real payloads always carry `code` (0 nulls in 659 live rows), so the fixture is the thing
    that is wrong here, not the expectation.
    """
    bootstrap = _realistic(json.loads(BOOTSTRAP.read_text()))
    for i, element in enumerate(bootstrap["elements"], start=1):
        element["code"] = 100000 + i
    return FakeClient(bootstrap, json.loads(FIXTURES.read_text())), len(bootstrap["elements"])


def test_refresh_records_an_availability_observation(tmp_path):
    """⭐ **Testing a component is not testing that anything uses it.**

    `save_availability` has its own tests (`test_availability_log.py`) and every one of them passed with the
    call absent from `refresh` — a perfectly-tested recorder that never runs is the same as no recorder, and
    the data it fails to capture is gone for good (ADR-203). This pins the wiring, not the writer.
    """
    client, n_players = _fpl_with_codes()
    store = Storage(db_path=str(tmp_path / "test.db"))
    try:
        ingest.refresh(store, client=client, elo_client=FailingEloClient(), now="2026-09-17T09:00:00+00:00")
        rows = store.conn.execute("SELECT element_code, observed_at FROM player_availability").fetchall()
        assert len(rows) == n_players > 0, "every player in the payload should have an observation"
        assert {r["observed_at"] for r in rows} == {"2026-09-17T09:00:00+00:00"}
    finally:
        store.close()


def test_a_second_refresh_does_not_duplicate_an_unchanged_observation(tmp_path):
    """The volume guard, at the level a user actually triggers it — `refresh` twice in a day."""
    client, _ = _fpl_with_codes()
    store = Storage(db_path=str(tmp_path / "test.db"))
    try:
        ingest.refresh(store, client=client, elo_client=FailingEloClient(), now="2026-09-17T09:00:00+00:00")
        before = store.conn.execute("SELECT COUNT(*) AS n FROM player_availability").fetchone()["n"]
        ingest.refresh(store, client=client, elo_client=FailingEloClient(), now="2026-09-17T18:00:00+00:00")
        after = store.conn.execute("SELECT COUNT(*) AS n FROM player_availability").fetchone()["n"]
        assert before > 0 and after == before, "an unchanged squad must not double the table every refresh"
        assert store.conn.execute(
            "SELECT DISTINCT last_seen_at FROM player_availability").fetchone()[0] == "2026-09-17T18:00:00+00:00", (
            "…but the window must show we confirmed it again")
    finally:
        store.close()


def test_a_player_with_no_code_does_not_abort_the_refresh(tmp_path):
    """⭐ *The failure path of a side-record is the side-record.* The shared sample has no codes at all, so it
    is exactly the payload that would have crashed the lifeline — and every other ingest test with it."""
    store = Storage(db_path=str(tmp_path / "test.db"))
    try:
        n_players, _, n_fixtures, _ = ingest.refresh(
            store, client=_fpl(), elo_client=FailingEloClient(), now="2026-09-17T09:00:00+00:00")
        assert n_players > 0 and n_fixtures > 0, "the refresh must complete"
        assert store.conn.execute(
            "SELECT COUNT(*) AS n FROM player_availability").fetchone()["n"] == 0, (
            "…and record nothing it cannot key")
    finally:
        store.close()
