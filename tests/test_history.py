"""Tests for history ingestion — past-season (ADR-027) and per-GW (ADR-060).

Cover the model mapping, the storage round-trip, and the backfill's promises: idempotence,
per-player degradation, 0-season players, and that per-GW history rides the same walk (empty
preseason). All offline — a fake client, an in-memory DB, no throttle.
"""

from src import ingest
from src.api.client import FplApiError
from src.models import PlayerGameweek, PlayerSeason
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


def _gw(element_id, rnd, pts=6, mins=90, home=True, opp=5):
    """One canned per-GW `history` row (carries `element`, the season id — not the stable code)."""
    return {
        "element": element_id, "round": rnd, "total_points": pts, "minutes": mins,
        "was_home": home, "opponent_team": opp, "fixture": 100 + rnd,
        "kickoff_time": f"2026-08-{rnd:02d}T14:00:00Z",
    }


def _seed_players(store, code_by_id):
    """Seed the players table with just id + code (per-GW ingest keys by code, via an id→code map)."""
    with store.conn:
        store.conn.executemany(
            "INSERT INTO players (id, code, web_name) VALUES (?, ?, ?)",
            [(pid, code, f"P{pid}") for pid, code in code_by_id.items()],
        )


class FakeClient:
    """Returns canned element-summary payloads; raises for ids in `fail_ids`."""

    def __init__(self, past_by_id, fail_ids=(), gw_by_id=None):
        self.past_by_id = past_by_id
        self.gw_by_id = gw_by_id or {}
        self.fail_ids = set(fail_ids)
        self.calls = []

    def get_element_summary(self, element_id):
        self.calls.append(element_id)
        if element_id in self.fail_ids:
            raise FplApiError(f"boom {element_id}")
        return {
            "fixtures": [], "history": self.gw_by_id.get(element_id, []),
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
    processed, seasons, gameweeks, failures = _backfill(store, client, ids=[1])
    assert (processed, seasons, gameweeks, failures) == (1, 2, 0, 0)
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
    processed, seasons, gameweeks, failures = _backfill(store, client, ids=[1, 2, 3])
    assert (processed, seasons, gameweeks, failures) == (2, 2, 0, 1)   # 2 ok, id 2 skipped
    assert store.get_history_past(101) and store.get_history_past(303)
    store.close()


# ---- backfill: a player with no past seasons -------------------------------

def test_backfill_handles_zero_season_player():
    store = Storage(":memory:")
    client = FakeClient({7: []})               # a young player, no history
    processed, seasons, gameweeks, failures = _backfill(store, client, ids=[7])
    assert (processed, seasons, gameweeks, failures) == (1, 0, 0, 0)   # counted, nothing stored
    assert store.count_history_past() == 0
    store.close()


# ---- per-GW (ADR-060): model + storage round-trip --------------------------

def test_player_gameweek_from_api_maps_with_passed_code():
    # the per-GW row carries `element` (season id); the stable code is passed in
    gw = PlayerGameweek.from_api(_gw(1, rnd=3, pts=8, mins=88, home=False, opp=12), element_code=101)
    assert gw.element_code == 101 and gw.round == 3
    assert gw.total_points == 8 and gw.minutes == 88
    assert gw.was_home == 0 and gw.opponent_team == 12    # bool → 1/0


def test_save_and_get_history_per_gw():
    store = Storage(":memory:")
    store.save_history([PlayerGameweek.from_api(_gw(1, 1), 101),
                        PlayerGameweek.from_api(_gw(1, 2), 101)])
    rows = store.get_history(101)
    assert [r["round"] for r in rows] == [1, 2]           # earliest round first
    assert store.count_history() == 2
    store.close()


# ---- per-GW: rides the same walk, keyed by code ----------------------------

def test_backfill_stores_per_gw_history_by_code():
    store = Storage(":memory:")
    _seed_players(store, {1: 101})                        # id 1 → code 101
    client = FakeClient(
        past_by_id={1: [_season(101, "2024/25")]},
        gw_by_id={1: [_gw(1, 1), _gw(1, 2)]},
    )
    processed, seasons, gameweeks, failures = _backfill(store, client, ids=[1])
    assert (processed, seasons, gameweeks, failures) == (1, 1, 2, 0)
    assert [r["round"] for r in store.get_history(101)] == [1, 2]
    assert 101 in store.get_gw_history_by_code()          # retrievable by the stable code
    store.close()


def test_backfill_per_gw_is_idempotent():
    store = Storage(":memory:")
    _seed_players(store, {1: 101})
    client = FakeClient({}, gw_by_id={1: [_gw(1, 1), _gw(1, 2)]})
    _backfill(store, client, ids=[1])
    _backfill(store, client, ids=[1])                     # re-run
    assert store.count_history() == 2                     # upsert on (code, round), not duplicate
    store.close()


def test_backfill_per_gw_is_empty_preseason():
    # the real preseason case: history is [] → 0 per-GW rows, no error
    store = Storage(":memory:")
    _seed_players(store, {1: 101})
    client = FakeClient({1: [_season(101, "2024/25")]})   # gw_by_id empty → history []
    processed, seasons, gameweeks, failures = _backfill(store, client, ids=[1])
    assert (gameweeks, failures) == (0, 0)
    assert store.count_history() == 0
    store.close()
