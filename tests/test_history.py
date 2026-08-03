"""Tests for past-season history ingestion (ADR-027).

Cover the model mapping, the storage round-trip, and the backfill's three
promises: idempotence, per-player degradation, and handling 0-season players.
All offline — a fake client, an in-memory DB, no throttle.
"""

from src import ingest
from src.api.client import FplApiError
from src.models import PlayerSeason
from src.storage import Storage


def _season(code, name, pts=100, mins=2000):
    """One canned `history_past` row (mixes string xG + int fields, like the API)."""
    return {
        "element_code": code, "season_name": name,
        "total_points": pts, "minutes": mins,
        "goals_scored": 10, "assists": 5, "clean_sheets": 3, "goals_conceded": 20,
        "expected_goals": "9.5", "expected_assists": "4.2",
        "expected_goal_involvements": "13.7", "expected_goals_conceded": "18.0",
        "defensive_contribution": 0, "starts": 25,
        "start_cost": 115, "end_cost": 120,
    }


class FakeClient:
    """Returns canned element-summary payloads; raises for ids in `fail_ids`."""

    def __init__(self, past_by_id, fail_ids=()):
        self.past_by_id = past_by_id
        self.fail_ids = set(fail_ids)
        self.calls = []

    def get_element_summary(self, element_id):
        self.calls.append(element_id)
        if element_id in self.fail_ids:
            raise FplApiError(f"boom {element_id}")
        return {
            "fixtures": [], "history": [],
            "history_past": self.past_by_id.get(element_id, []),
        }


def _backfill(store, client, ids):
    # sleep_between=0 → no throttle, so the tests run instantly.
    return ingest.backfill_history(store, client=client, ids=ids, sleep_between=0)


# ---- model ------------------------------------------------------------------

def test_player_season_from_api_maps_and_converts():
    s = PlayerSeason.from_api(_season(223094, "2022/23", pts=272, mins=2767))
    assert s.element_code == 223094 and s.season_name == "2022/23"
    assert s.total_points == 272 and s.minutes == 2767
    assert s.expected_goals == 9.5              # string → float
    assert s.start_cost == 11.5                 # tenths → £m (115 → 11.5)
    assert s.defensive_contribution == 0


# ---- storage round-trip -----------------------------------------------------

def test_save_and_get_history_past():
    store = Storage(":memory:")
    store.save_history_past([PlayerSeason.from_api(_season(1, "2024/25"))])
    rows = store.get_history_past(1)
    assert len(rows) == 1 and rows[0]["season_name"] == "2024/25"
    store.close()


# ---- backfill: stores seasons ----------------------------------------------

def test_backfill_stores_seasons():
    store = Storage(":memory:")
    client = FakeClient({1: [_season(101, "2023/24"), _season(101, "2024/25")]})
    processed, seasons, failures = _backfill(store, client, ids=[1])
    assert (processed, seasons, failures) == (1, 2, 0)
    assert len(store.get_history_past(101)) == 2
    store.close()


# ---- backfill: idempotent ---------------------------------------------------

def test_backfill_is_idempotent():
    store = Storage(":memory:")
    client = FakeClient({1: [_season(101, "2023/24"), _season(101, "2024/25")]})
    _backfill(store, client, ids=[1])
    _backfill(store, client, ids=[1])          # re-run
    assert store.count_history_past() == 2      # upsert, not duplicate
    store.close()


# ---- backfill: per-player degrade ------------------------------------------

def test_backfill_skips_a_failing_player_and_continues():
    store = Storage(":memory:")
    client = FakeClient(
        {1: [_season(101, "2024/25")], 3: [_season(303, "2024/25")]},
        fail_ids=[2],
    )
    processed, seasons, failures = _backfill(store, client, ids=[1, 2, 3])
    assert (processed, seasons, failures) == (2, 2, 1)   # 2 ok, id 2 skipped
    assert store.get_history_past(101) and store.get_history_past(303)
    store.close()


# ---- backfill: a player with no past seasons -------------------------------

def test_backfill_handles_zero_season_player():
    store = Storage(":memory:")
    client = FakeClient({7: []})               # a young player, no history
    processed, seasons, failures = _backfill(store, client, ids=[7])
    assert (processed, seasons, failures) == (1, 0, 0)   # counted, nothing stored
    assert store.count_history_past() == 0
    store.close()
