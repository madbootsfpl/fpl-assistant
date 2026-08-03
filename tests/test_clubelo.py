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
        # A connection error is transient, so it retries — inject a no-op sleep so the
        # test stays instant.
        EloClient(sleep=lambda s: None).get_elo_csv(date="2026-08-02")


# --- retry-with-backoff (ADR-020) ---

class FakeResp:
    """A stand-in requests.Response: raise_for_status raises HTTPError on a 4xx/5xx."""

    def __init__(self, status=200, text=CSV):
        self.status_code = status
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            resp = requests.Response()
            resp.status_code = self.status_code
            raise requests.HTTPError(response=resp)


def sequence_get(items):
    """A fake requests.get yielding `items` (FakeResp or Exception) in order."""
    it = iter(items)

    def _get(*a, **k):
        item = next(it)
        if isinstance(item, Exception):
            raise item
        return item

    return _get


def test_is_transient_classifies_errors():
    from src.api.retry import is_transient

    def http(code):
        resp = requests.Response()
        resp.status_code = code
        return requests.HTTPError(response=resp)

    assert is_transient(http(502)) and is_transient(http(503)) and is_transient(http(504))
    assert not is_transient(http(404))          # permanent — a retry won't help
    assert not is_transient(http(500))          # not in the gateway set
    assert is_transient(requests.Timeout()) and is_transient(requests.ConnectionError())


def test_get_elo_csv_retries_transient_then_succeeds(monkeypatch):
    sleeps = []
    monkeypatch.setattr(
        "src.api.clubelo.requests.get",
        sequence_get([FakeResp(502), FakeResp(200)]),
    )
    # ClubElo is best-effort → fail fast (default 1 retry): a blip is still retried once.
    out = EloClient(sleep=sleeps.append).get_elo_csv(date="2026-08-02")

    assert "Arsenal" in out            # succeeded on the 2nd attempt
    assert sleeps == [0.5]             # a single backoff (1 retry)


def test_get_elo_csv_does_not_retry_permanent(monkeypatch):
    sleeps = []
    monkeypatch.setattr("src.api.clubelo.requests.get", sequence_get([FakeResp(404)]))
    with pytest.raises(ClubEloError) as exc:
        EloClient(sleep=sleeps.append).get_elo_csv(date="2026-08-02")

    assert "after 1 attempt" in str(exc.value)   # failed fast
    assert sleeps == []                          # no retry on a permanent error


def test_get_elo_csv_exhausts_retries_then_raises(monkeypatch):
    sleeps = []
    monkeypatch.setattr("src.api.clubelo.requests.get", sequence_get([FakeResp(502)] * 3))
    with pytest.raises(ClubEloError) as exc:
        EloClient(sleep=sleeps.append).get_elo_csv(date="2026-08-02")

    # Fail fast: 1 retry = 2 attempts, then degrade (down from ~31s in Sprint 019).
    assert "after 2 attempt" in str(exc.value)
    assert sleeps == [0.5]
