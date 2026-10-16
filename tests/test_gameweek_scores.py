"""Match scores for a gameweek, and the squad join (ADR-346).

⭐⭐ **The two things worth guarding are both about not lying.** A score of `0-0` and a match that has not
kicked off are different facts that an unwary implementation renders identically; and so are *"none of
your players featured"* and *"we do not know yet"*, which an empty list cannot tell apart.

⚠️ Both were found by running this against the real database rather than by designing for them.
"""

import shutil

import pytest
from fastapi.testclient import TestClient

from src import config
from src.service import GameweekScoresRequest, gameweek_scores
from src.service.answers import scores as mod
from src.service.http.app import app
from src.storage import Storage


@pytest.fixture
def store(tmp_path, monkeypatch):
    """A copy of the committed snapshot — never the file in git, which `Storage()` would migrate."""
    target = tmp_path / "scores.db"
    shutil.copy(config.SEED_DB_PATH, target)
    target.chmod(0o644)
    monkeypatch.setattr(config, "SEED_DB_PATH", str(target))
    s = Storage(config.SEED_DB_PATH)
    yield s
    s.close()


@pytest.fixture(autouse=True)
def _no_stale_cache():
    mod.forget_live()
    yield
    mod.forget_live()


def _squad(store, n=15):
    return [p["id"] for p in store.get_players()][:n]


def _set(store, fixture_id, **cols):
    sets = ", ".join(f"{k} = ?" for k in cols)
    with store.conn:
        store.conn.execute(f"UPDATE fixtures SET {sets} WHERE id = ?",
                           (*cols.values(), fixture_id))


def _fixtures_for(store, event):
    """⚠️ `get_fixtures_by_event` does not select `f.id` — it was written for the calibration backtest,
    which does not need one. `get_all_fixtures` is `SELECT *`, which is what the answer uses too."""
    return [f for f in store.get_all_fixtures() if f["event"] == event]


def _event_with_fixtures(store):
    row = store.conn.execute(
        "SELECT event FROM fixtures WHERE event IS NOT NULL GROUP BY event ORDER BY event LIMIT 1"
    ).fetchone()
    return row["event"]


# ── a score is not a zero, and a zero is not a blank ─────────────────────────────────────────────

def test_a_goalless_draw_is_not_the_same_as_not_played(store):
    """⚠️⚠️ **The failure this nullability exists for.** `0-0` and *"no kick-off yet"* both look like
    "nothing" to a renderer that defaults a missing score to zero — ⭐ *and they are opposite facts on the
    one screen built to tell them apart.*"""
    gw = _event_with_fixtures(store)
    ids = [f["id"] for f in _fixtures_for(store, gw)]
    _set(store, ids[0], team_h_score=0, team_a_score=0, started=1, finished=1, minutes=90)
    _set(store, ids[1], team_h_score=None, team_a_score=None, started=0, finished=0, minutes=0)

    got = {m["fixture"]: m for m in gameweek_scores(
        GameweekScoresRequest(gameweek=gw), store=store)["matches"]}

    drawn, unplayed = got[ids[0]], got[ids[1]]
    assert (drawn["home_score"], drawn["away_score"]) == (0, 0)
    assert drawn["started"] is True
    assert unplayed["home_score"] is None and unplayed["away_score"] is None
    assert unplayed["started"] is False


def test_a_finished_match_counts_as_started_even_when_the_column_says_otherwise(store):
    """⚠️ Every fixture stored before ADR-346 has `started` NULL and `finished` already set, so a played
    match read as *"not started but finished"* — and no gameweek looked playable. ⭐ *A derived truth is
    cheaper than a backfill and cannot drift.*"""
    gw = _event_with_fixtures(store)
    fid = _fixtures_for(store, gw)[0]["id"]
    _set(store, fid, started=None, finished=1, team_h_score=2, team_a_score=1)

    out = gameweek_scores(GameweekScoresRequest(gameweek=gw), store=store)
    assert next(m for m in out["matches"] if m["fixture"] == fid)["started"] is True


# ── which gameweek ───────────────────────────────────────────────────────────────────────────────

def test_a_gameweek_in_flight_wins_over_a_finished_one(store):
    """⭐ *"Current or last"* is two questions with one answer — the live week while there is one."""
    events = sorted({f["event"] for f in store.get_all_fixtures() if f["event"]})[:2]
    done, live = events
    for f in _fixtures_for(store, done):
        _set(store, f["id"], started=1, finished=1, team_h_score=1, team_a_score=0)
    for f in _fixtures_for(store, live):
        _set(store, f["id"], started=1, finished=0, team_h_score=0, team_a_score=0, minutes=31)
    for f in store.get_all_fixtures():
        if f["event"] not in (done, live):
            _set(store, f["id"], started=0, finished=0)

    out = gameweek_scores(GameweekScoresRequest(), store=store, client=_NoClient())
    assert out["gameweek"] == live and out["live"] is True


def test_with_nothing_played_the_answer_is_empty_rather_than_an_error(store):
    """⭐ A season that has not started is a fact, not a failure."""
    for f in store.get_all_fixtures():
        _set(store, f["id"], started=0, finished=0, team_h_score=None, team_a_score=None)
    out = gameweek_scores(GameweekScoresRequest(), store=store)
    assert out == {"gameweek": None, "live": False, "yours_known": False,
                   "clubs": {}, "matches": []}


# ── the join, and what it must not claim ─────────────────────────────────────────────────────────

def test_an_empty_yours_says_whether_it_knows(store):
    """⚠️⚠️ **Scores land before player history does.** `fixtures` is filled by the refresh and
    `player_history` by the backfill, so after full time the score is known and nobody's week is.
    🔴 *"None of your players played" and "we do not know yet" are opposite facts and an empty list cannot
    tell them apart* — found against the real database, where GW6 had ten scores and no history.
    """
    gw = _event_with_fixtures(store)
    with store.conn:
        store.conn.execute("DELETE FROM player_history WHERE round = ?", (gw,))
    out = gameweek_scores(GameweekScoresRequest(player_ids=_squad(store), gameweek=gw), store=store)
    assert out["yours_known"] is False
    assert all(m["yours"] == [] for m in out["matches"])


def test_a_week_with_history_reports_its_players(store):
    gw = store.conn.execute(
        "SELECT round FROM player_history GROUP BY round ORDER BY COUNT(*) DESC LIMIT 1").fetchone()["round"]
    codes = [r["element_code"] for r in store.conn.execute(
        "SELECT DISTINCT element_code FROM player_history WHERE round = ? LIMIT 12", (gw,)).fetchall()]
    ids = [p["id"] for p in store.get_players() if p["code"] in set(codes)]
    assert ids, "the snapshot must carry players with history for this to mean anything"

    out = gameweek_scores(GameweekScoresRequest(player_ids=ids, gameweek=gw), store=store)
    assert out["yours_known"] is True
    assert sum(len(m["yours"]) for m in out["matches"]) > 0


def test_the_scores_come_back_without_a_squad_at_all(store):
    """⭐ A scoreline is a fact about the league. *A screen that refuses to draw without a squad is a
    screen that breaks on first launch.*"""
    gw = _event_with_fixtures(store)
    out = gameweek_scores(GameweekScoresRequest(gameweek=gw), store=store)
    assert out["matches"] and out["yours_known"] is False


# ── the live path ────────────────────────────────────────────────────────────────────────────────

class _NoClient:
    def get_fixtures(self):
        raise AssertionError("FPL must not be called for a finished gameweek")


class _Counting:
    def __init__(self, rows): self.rows, self.calls = rows, 0
    def get_fixtures(self):
        self.calls += 1
        return self.rows


def test_a_finished_gameweek_never_reaches_upstream(store):
    """⭐⭐ The whole economics: a played score never changes, so it is served from the database forever."""
    gw = _event_with_fixtures(store)
    for f in _fixtures_for(store, gw):
        _set(store, f["id"], started=1, finished=1, team_h_score=1, team_a_score=1)
    gameweek_scores(GameweekScoresRequest(gameweek=gw), store=store, client=_NoClient())


def test_a_live_score_overlays_the_stored_one(store):
    gw = _event_with_fixtures(store)
    fid = _fixtures_for(store, gw)[0]["id"]
    for f in _fixtures_for(store, gw):
        _set(store, f["id"], started=1, finished=0, team_h_score=0, team_a_score=0, minutes=5)
    client = _Counting([{"id": fid, "event": gw, "team_h_score": 3, "team_a_score": 2,
                         "minutes": 77, "started": True, "finished": False}])

    out = gameweek_scores(GameweekScoresRequest(gameweek=gw), store=store, client=client)
    m = next(x for x in out["matches"] if x["fixture"] == fid)
    assert (m["home_score"], m["away_score"], m["minutes"]) == (3, 2, 77)
    assert out["live"] is True


def test_the_live_fetch_is_cached_so_refreshing_does_not_hammer_fpl(store):
    """⭐⭐ *A rate limit bounds one caller; a cache bounds everyone* — which is what an undocumented
    upstream actually needs when nine people refresh during a kick-off."""
    gw = _event_with_fixtures(store)
    for f in _fixtures_for(store, gw):
        _set(store, f["id"], started=1, finished=0, team_h_score=0, team_a_score=0)
    client = _Counting([])
    for _ in range(5):
        gameweek_scores(GameweekScoresRequest(gameweek=gw), store=store, client=client)
    assert client.calls == 1, f"{client.calls} upstream calls for five requests"


def test_a_failed_live_fetch_falls_back_to_the_stored_score(store):
    """⚠️ *A screen showing a half-hour-old score is working; a screen showing an error is not.*"""
    gw = _event_with_fixtures(store)
    fid = _fixtures_for(store, gw)[0]["id"]
    for f in _fixtures_for(store, gw):
        _set(store, f["id"], started=1, finished=0, team_h_score=1, team_a_score=4)

    class _Broken:
        def get_fixtures(self): raise RuntimeError("upstream down")

    out = gameweek_scores(GameweekScoresRequest(gameweek=gw), store=store, client=_Broken())
    m = next(x for x in out["matches"] if x["fixture"] == fid)
    assert (m["home_score"], m["away_score"]) == (1, 4)


# ── the wire ─────────────────────────────────────────────────────────────────────────────────────

def test_the_endpoint_answers_without_a_squad(store):
    c = TestClient(app)
    r = c.post("/api/v1/gameweek/scores", json={})
    assert r.status_code == 200
    assert {"gameweek", "live", "yours_known", "matches"} <= set(r.json())


def test_the_endpoint_refuses_an_impossible_gameweek(store):
    assert TestClient(app).post("/api/v1/gameweek/scores", json={"gameweek": 99}).status_code == 422
