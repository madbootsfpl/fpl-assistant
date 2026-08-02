"""Tests for the ClubElo client, parsing and team-name mapping (offline)."""

from pathlib import Path

import pytest
import requests

from src.api.clubelo import (
    ClubEloError,
    EloClient,
    map_elo_to_teams,
    parse_english_elo,
)

CSV = (Path(__file__).parent / "fixtures" / "clubelo_sample.csv").read_text()


def test_parse_english_elo_filters_to_top_division_english():
    elo = parse_english_elo(CSV)

    assert elo["Arsenal"] == 2063.7
    assert "Wrexham" not in elo       # level 2 excluded
    assert "Real Madrid" not in elo   # non-English excluded


def test_map_elo_to_teams_resolves_exact_and_mapped_names():
    teams = [
        {"id": 1, "name": "Arsenal"},          # exact
        {"id": 2, "name": "Nott'm Forest"},    # via mapping (Forest)
        {"id": 3, "name": "Spurs"},            # via mapping (Tottenham)
        {"id": 4, "name": "Hull City"},        # via mapping (Hull)
    ]
    elo_by_club = {"Arsenal": 2063.7, "Forest": 1822.0, "Tottenham": 1777.0, "Hull": 1533.0}

    elo_by_team, unmapped = map_elo_to_teams(elo_by_club, teams)

    assert elo_by_team == {1: 2063.7, 2: 1822.0, 3: 1777.0, 4: 1533.0}
    assert unmapped == []


def test_map_elo_to_teams_reports_unmapped_clubs():
    teams = [{"id": 1, "name": "Arsenal"}]
    elo_by_team, unmapped = map_elo_to_teams(
        {"Arsenal": 2000.0, "Mystery FC": 1500.0}, teams
    )

    assert elo_by_team == {1: 2000.0}
    assert unmapped == ["Mystery FC"]


def test_get_elo_csv_returns_text(monkeypatch):
    class FakeResponse:
        text = CSV

        def raise_for_status(self):
            pass

    monkeypatch.setattr("src.api.clubelo.requests.get", lambda *a, **k: FakeResponse())
    out = EloClient().get_elo_csv(date="2026-08-02")
    assert "Arsenal" in out


def test_get_elo_csv_wraps_network_errors(monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError("no network")

    monkeypatch.setattr("src.api.clubelo.requests.get", boom)
    with pytest.raises(ClubEloError):
        EloClient().get_elo_csv(date="2026-08-02")
