"""Tests for importing a manager's FPL team by id (Sprint 064, ADR-058).

`picks_to_squad` is a pure mapper (picks payload → squad dict); `fetch_manager_team` orchestrates the
public FPL fetch and **degrades gracefully** — a bad id / down API / not-yet-public picks → a clear
message, never a raise. The FPL client is faked, so no network.
"""

from src.api.client import FplApiError
from src.manager import fetch_manager_team, picks_to_squad

_PLAYERS = [{"id": i, "web_name": f"P{i}", "price": 5.0} for i in range(1, 16)]
_PICKS = {"picks": [
    {"element": i, "position": i, "is_captain": (i == 11), "is_vice_captain": (i == 10)}
    for i in range(1, 16)
]}


def test_picks_to_squad_maps_ids_bench_and_captain():
    sq = picks_to_squad(_PICKS, _PLAYERS, name="My FC")
    assert sq["name"] == "My FC" and sq["player_ids"] == list(range(1, 16))
    assert sq["bench_ids"] == [12, 13, 14, 15]          # positions 12–15 are the bench
    assert sq["captain_id"] == 11                       # the is_captain pick
    assert sq["cost"] == 75.0 and sq["player_names"][0] == "P1"


def test_picks_to_squad_none_when_a_pick_is_unknown():
    picks = {"picks": [{"element": 999, "position": 1}]}   # id not in the current players
    assert picks_to_squad(picks, _PLAYERS, name="x") is None
    assert picks_to_squad({"picks": []}, _PLAYERS, name="x") is None   # empty → None


class _FakeClient:
    def __init__(self, entry=None, picks=None, raise_on=None):
        self._entry, self._picks, self._raise_on = entry, picks, raise_on or set()

    def get_entry(self, entry_id):
        if "entry" in self._raise_on:
            raise FplApiError("boom")
        return self._entry

    def get_entry_picks(self, entry_id, gameweek):
        if "picks" in self._raise_on:
            raise FplApiError("404")
        return self._picks


def test_fetch_manager_team_imports_a_valid_team():
    client = _FakeClient(entry={"name": "Ada", "current_event": 3}, picks=_PICKS)
    squad, msg = fetch_manager_team(42, _PLAYERS, client=client)
    assert squad and squad["name"] == "Ada" and squad["captain_id"] == 11
    assert "Imported" in msg and "GW3" in msg


def test_fetch_manager_team_preseason_no_current_event():
    client = _FakeClient(entry={"name": "Ada", "current_event": None})
    squad, msg = fetch_manager_team(42, _PLAYERS, client=client)
    assert squad is None and "GW1 deadline" in msg           # not public until the deadline


def test_fetch_manager_team_bad_id_degrades():
    client = _FakeClient(raise_on={"entry"})
    squad, msg = fetch_manager_team(42, _PLAYERS, client=client)
    assert squad is None and "Couldn't reach FPL" in msg     # no raise — a clear message


def test_fetch_manager_team_picks_not_available_degrades():
    client = _FakeClient(entry={"name": "Ada", "current_event": 1}, raise_on={"picks"})
    squad, msg = fetch_manager_team(42, _PLAYERS, client=client)
    assert squad is None and "GW1 deadline" in msg           # 404 picks → the graceful message


def test_the_import_keeps_the_vice_captain_fpl_already_sent():
    """`is_vice_captain` sits beside `is_captain` in the same pick and was being discarded, so an imported
    team silently arrived having lost one of the two decisions its owner had made (2026-09-02)."""
    players = [{"id": i, "web_name": f"P{i}", "price": 5.0} for i in range(1, 16)]
    picks = {"picks": [{"element": i, "position": i,
                        "is_captain": i == 3, "is_vice_captain": i == 7} for i in range(1, 16)]}
    squad = picks_to_squad(picks, players, name="T")
    assert squad["captain_id"] == 3 and squad["vice_captain_id"] == 7


def test_a_team_with_no_vice_imports_cleanly():
    players = [{"id": i, "web_name": f"P{i}", "price": 5.0} for i in range(1, 16)]
    picks = {"picks": [{"element": i, "position": i, "is_captain": i == 3} for i in range(1, 16)]}
    assert picks_to_squad(picks, players, name="T")["vice_captain_id"] is None
