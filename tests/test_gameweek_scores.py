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
    """⭐ A season that has not started is a fact, not a failure.

    ⚠️ **The clock is pinned, and it has to be** (ADR-354): the seed holds a whole season, so "nothing
    played" is only true on a date before any of it. ⭐ *Clearing the flags used to be enough; now the
    kick-off times mean what they say*, and a test reading the real clock would start passing and failing
    by the calendar.
    """
    from datetime import UTC, datetime
    for f in store.get_all_fixtures():
        _set(store, f["id"], started=0, finished=0, team_h_score=None, team_a_score=None)
    out = gameweek_scores(GameweekScoresRequest(), store=store,
                          now=datetime(2026, 8, 1, tzinfo=UTC))
    assert out == {"gameweek": None, "live": False, "yours_known": False,
                   "clubs": {}, "people": {}, "squad": [], "matches": []}


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


class _Picks:
    """FPL's picks for a past gameweek — the only source that knows whose team a player was in."""

    def __init__(self, ids): self.ids, self.asked = ids, []

    def get_entry_picks(self, entry, gameweek):
        self.asked.append((entry, gameweek))
        return {"picks": [{"element": i} for i in self.ids]}


def _week_with_history(store):
    gw = store.conn.execute(
        "SELECT round FROM player_history GROUP BY round ORDER BY COUNT(*) DESC LIMIT 1").fetchone()["round"]
    codes = [r["element_code"] for r in store.conn.execute(
        "SELECT DISTINCT element_code FROM player_history WHERE round = ? LIMIT 12", (gw,)).fetchall()]
    ids = [p["id"] for p in store.get_players() if p["code"] in set(codes)]
    with store.conn:
        store.conn.execute("UPDATE fixtures SET finished = 1, started = 1 WHERE event = ?", (gw,))
    return gw, ids


def test_a_played_week_uses_the_squad_that_actually_played_it(store):
    """🔴🔴 **The bug the owner found.** He saw *Calafiori* and *Haaland* credited with points in GW6, a
    week he held *Gabriel* and *Calvert-Lewin* — ⚠️⚠️ *and the card totalled them, so a fiction carried a
    confident number.* The squad a caller holds today is not the squad that played last week.
    """
    gw, real = _week_with_history(store)
    # What he holds now — deliberately nothing to do with that week.
    now = [p["id"] for p in store.get_players() if p["id"] not in set(real)][:15]
    picks = _Picks(real)

    out = gameweek_scores(
        GameweekScoresRequest(player_ids=now, manager_id=2885974, gameweek=gw),
        store=store, client=picks)

    assert picks.asked == [(2885974, gw)], "FPL was not asked whose team it was"
    named = {a["player"]["id"] for m in out["matches"] for a in m["yours"]}
    assert named, "nobody was named at all"
    assert named <= set(real), "a player he did not own that week was credited"
    assert not (named & set(now) - set(real)), "today's squad leaked into a played week"


def test_a_played_week_with_no_manager_names_nobody(store):
    """⚠️ **Never falls back to the current squad.** ⭐ *A wrong attribution is worse than none*, and a
    fallback would restore the exact bug this exists to fix, silently."""
    gw, real = _week_with_history(store)
    out = gameweek_scores(
        GameweekScoresRequest(player_ids=real, gameweek=gw), store=store, client=_Picks(real))
    assert out["yours_known"] is False
    assert all(m["yours"] == [] for m in out["matches"])


def test_a_failed_picks_fetch_names_nobody_rather_than_guessing(store):
    gw, real = _week_with_history(store)

    class _Broken:
        def get_entry_picks(self, entry, gameweek): raise RuntimeError("FPL is down")

    out = gameweek_scores(
        GameweekScoresRequest(player_ids=real, manager_id=1, gameweek=gw), store=store, client=_Broken())
    assert out["yours_known"] is False
    assert all(m["yours"] == [] for m in out["matches"])


def test_a_week_still_in_play_uses_the_squad_the_caller_holds(store):
    """⭐ FPL locks picks at the deadline, so for a week in progress the caller's own side is the right
    one — ⚠️ *and asking FPL for picks it has not published yet would answer nothing.*"""
    gw, real = _week_with_history(store)
    with store.conn:
        store.conn.execute("UPDATE fixtures SET finished = 0, started = 1 WHERE event = ?", (gw,))

    class _NeverAsked:
        def get_entry_picks(self, entry, gameweek):
            raise AssertionError("a live week must not ask FPL for picks")

    out = gameweek_scores(
        GameweekScoresRequest(player_ids=real, manager_id=1, gameweek=gw),
        store=store, client=_NeverAsked())
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


# ── the live gate reads the clock, not a flag (ADR-354) ──────────────────────────────────────────

_KO = "2026-10-17T11:30:00Z"


def _gw7_as_stored(store, gw):
    """GW7 exactly as the database holds it before any refresh: known fixtures, nothing started."""
    for f in store.get_all_fixtures():
        _set(store, f["id"], started=0, finished=0, team_h_score=None, team_a_score=None)
    for f in [x for x in store.get_all_fixtures() if x["event"] == gw]:
        store.conn.execute("UPDATE fixtures SET kickoff_time = ? WHERE id = ?", (_KO, f["id"]))
    store.conn.commit()


def test_a_match_that_has_kicked_off_goes_live_before_the_pipeline_says_so(store):
    """🔴🔴 **The bug, in production, during GW7.** At 12:32 UTC — an hour after EVE-CHE kicked off — the
    endpoint answered `gameweek=6, live=False`: last week's finished results, on a matchday.

    ⭐⭐ `in_flight` read `started`, which only the **hourly pipeline** writes, so the live path was gated
    behind the very process it was designed not to depend on. ⚠️ *The fetch did not go near the pipeline
    and the decision to fetch did*, and the module's docstring claimed the first while meaning the second.
    """
    from datetime import UTC, datetime
    gw = 7
    _gw7_as_stored(store, gw)

    class _Live:
        """FPL's own feed, which knows perfectly well that the match is on."""
        def __init__(self): self.asked = 0
        def get_fixtures(self):
            self.asked += 1
            return [{"id": f["id"], "event": gw, "team_h_score": 1, "team_a_score": 0,
                     "minutes": 62, "started": True, "finished": False}
                    for f in store.get_all_fixtures() if f["event"] == gw]

    live = _Live()
    out = gameweek_scores(GameweekScoresRequest(), store=store, client=live,
                          now=datetime(2026, 10, 17, 12, 32, tzinfo=UTC))

    assert out["gameweek"] == gw, "the screen was still on last week"
    assert out["live"] is True
    assert live.asked == 1, "FPL was never asked"
    assert out["matches"][0]["status"] == "62'"


def test_before_kick_off_nothing_is_fetched(store):
    """⭐ The economy the gate was for: a week that has not begun makes **no** upstream call."""
    from datetime import UTC, datetime
    _gw7_as_stored(store, 7)

    class _Boom:
        def get_fixtures(self): raise AssertionError("FPL was asked before kick-off")

    out = gameweek_scores(GameweekScoresRequest(), store=store, client=_Boom(),
                          now=datetime(2026, 10, 17, 11, 29, tzinfo=UTC))
    assert out["live"] is False


def test_a_fixture_the_feed_never_finished_does_not_poll_for_ever(store):
    """⚠️⚠️ **An unbounded "since kick-off" is a condition that becomes permanently true.** A postponed or
    abandoned match keeps `finished = 0`, and the first version of this gate would have held the screen on
    that dead week and polled FPL about it indefinitely. 🔴 Two existing tests went red against the seed —
    whose fixtures are months old — which is how it was caught."""
    from datetime import UTC, datetime
    _gw7_as_stored(store, 7)

    class _Boom:
        def get_fixtures(self): raise AssertionError("still polling a match from last month")

    out = gameweek_scores(GameweekScoresRequest(gameweek=7), store=store, client=_Boom(),
                          now=datetime(2026, 11, 20, tzinfo=UTC))
    assert out["live"] is False


def test_the_window_outlasts_the_pipeline_not_the_match(store):
    """⭐⭐ 24h is sized against **the refresh**, not the 90 minutes. A game is over ~2h after kick-off but
    `finished` only flips when the pipeline next runs, and the observed gaps reach five hours — ⚠️ *closing
    the window first would replace a live score with "not started"*, which is worse than either truth."""
    from datetime import UTC, datetime
    gw = 7
    _gw7_as_stored(store, gw)

    class _Live:
        def get_fixtures(self):
            return [{"id": f["id"], "event": gw, "team_h_score": 2, "team_a_score": 1,
                     "minutes": 90, "started": True, "finished": True}
                    for f in store.get_all_fixtures() if f["event"] == gw]

    # five hours after kick-off: the match is over, the pipeline has not run, the DB still says nothing
    out = gameweek_scores(GameweekScoresRequest(), store=store, client=_Live(),
                          now=datetime(2026, 10, 17, 16, 30, tzinfo=UTC))
    assert out["gameweek"] == gw
    assert out["matches"][0]["status"] == "Full time"
    assert (out["matches"][0]["home_score"], out["matches"][0]["away_score"]) == (2, 1)


# ── the referee and the accountant (ADR-356) ─────────────────────────────────────────────────────

def test_full_time_is_the_whistle_not_the_bonus_points(store):
    """🔴 **A match that ended at 13:20 printed "90'" all afternoon.** FPL has two finished flags:
    `finished_provisional` flips at the whistle, `finished` waits until **bonus is confirmed** for the
    whole gameweek — hours later, sometimes the next day. Reading only the second, the card captioned a
    finished match as if it were still being played.

    ⭐ ADR-123 already refuses `finished` for the fixture horizon for this exact reason. The reasoning sat
    in one module and never reached the card.
    """
    from datetime import UTC, datetime
    gw = 7
    _gw7_as_stored(store, gw)

    class _Live:
        """FPL at 13:25: the whistle has gone, the bonus has not landed."""
        def get_fixtures(self):
            return [{"id": f["id"], "event": gw, "team_h_score": 0, "team_a_score": 2,
                     "minutes": 90, "started": True,
                     "finished": False, "finished_provisional": True}
                    for f in store.get_all_fixtures() if f["event"] == gw]

    out = gameweek_scores(GameweekScoresRequest(), store=store, client=_Live(),
                          now=datetime(2026, 10, 17, 13, 25, tzinfo=UTC))
    m = out["matches"][0]
    assert m["status"] == "Full time", "a finished match is still being described as in play"
    # ⚠️ And `finished` still means settled — the payload does not start claiming the bonus is in.
    assert m["finished"] is False


def test_a_match_actually_in_play_still_shows_the_minute(store):
    """⚠️ The guard on the other side: ⭐ *a fix that captions everything "Full time" passes the test
    above and breaks the feature.*"""
    from datetime import UTC, datetime
    gw = 7
    _gw7_as_stored(store, gw)

    class _Live:
        def get_fixtures(self):
            return [{"id": f["id"], "event": gw, "team_h_score": 0, "team_a_score": 1,
                     "minutes": 62, "started": True,
                     "finished": False, "finished_provisional": False}
                    for f in store.get_all_fixtures() if f["event"] == gw]

    out = gameweek_scores(GameweekScoresRequest(), store=store, client=_Live(),
                          now=datetime(2026, 10, 17, 12, 32, tzinfo=UTC))
    assert out["matches"][0]["status"] == "62'"


def test_a_stored_row_without_the_column_behaves_as_it_always_did(store):
    """⚠️⚠️ **The flag is read live and never stored** (ADR-356), so every database row lacks the key —
    and `sqlite3.Row` raises `IndexError` for a missing one where a dict returns None. ⭐ *The degrade is
    exactly today's behaviour*, which is what makes not storing it affordable."""
    from datetime import UTC, datetime
    gw = 6
    for f in store.get_all_fixtures():
        _set(store, f["id"], started=0, finished=0, team_h_score=None, team_a_score=None)
    for f in [x for x in store.get_all_fixtures() if x["event"] == gw]:
        _set(store, f["id"], started=1, finished=1, team_h_score=1, team_a_score=0)

    out = gameweek_scores(GameweekScoresRequest(gameweek=gw), store=store,
                          now=datetime(2026, 10, 17, 18, 0, tzinfo=UTC))
    assert out["matches"][0]["status"] == "Full time"


# ── what happened in the match, not just what you got (ADR-360) ──────────────────────────────────

def _a_played_fixture(store, gw=5):
    """A real fixture from the snapshot with goals in it, and its history rows."""
    row = store.conn.execute(
        "SELECT fixture FROM player_history WHERE round = ? AND goals_scored > 0 LIMIT 1", (gw,)).fetchone()
    return row["fixture"]


def test_the_card_carries_everyones_events_not_only_yours(store):
    """⭐⭐ **No new data and no upstream call.** `player_history` already holds goals, assists, cards,
    bonus and BPS **keyed by fixture**, so a card for a gameweek months old is one local query."""
    out = gameweek_scores(GameweekScoresRequest(gameweek=5, player_ids=[]), store=store)
    scored = [m for m in out["matches"] if m["events"]["goals"]]
    assert scored, "a played gameweek produced no goals at all"

    m = scored[0]
    # ⚠️ The squad is empty, so every name here belongs to somebody else — which is the point.
    assert out["yours_known"] is False
    assert all(str(g["player"]) in out["people"] for g in m["events"]["goals"])
    # ⚠️ `<=`, not `==`: an own goal counts on the scoreline and not in anyone's `goals_scored`.
    # ⭐ *The first draft of this line ended `or True`, which asserts nothing at all.*
    assert sum(g["count"] for g in m["events"]["goals"]) <= m["home_score"] + m["away_score"]


def test_goals_and_assists_stay_two_lists(store):
    """⚠️⚠️ **FPL links them to nothing.** Liverpool scored twice and two different players assisted;
    which set up which is not in the data. ⭐ *Pairing two sorted lists is the ADR-351 mistake*, so the
    payload offers no pairing to render — the lists are siblings, never nested."""
    out = gameweek_scores(GameweekScoresRequest(gameweek=5, player_ids=[]), store=store)
    for m in out["matches"]:
        for g in m["events"]["goals"]:
            assert set(g) == {"player", "count"}, f"a goal carries an assist: {g}"


def test_a_sending_off_is_red_not_yellow(store):
    """⭐ A second yellow is recorded as **both** a yellow and a red. The card shows one card per player
    and it is the red — ⚠️ *a dismissal shown as a booking is the wrong fact.*"""
    fid = _a_played_fixture(store)
    code = store.conn.execute(
        "SELECT element_code FROM player_history WHERE fixture = ? LIMIT 1", (fid,)).fetchone()["element_code"]
    with store.conn:
        store.conn.execute(
            "UPDATE player_history SET yellow_cards = 1, red_cards = 1 WHERE fixture = ? AND element_code = ?",
            (fid, code))

    out = gameweek_scores(GameweekScoresRequest(gameweek=5, player_ids=[]), store=store)
    m = next(x for x in out["matches"] if x["fixture"] == fid)
    pid = next(p["id"] for p in store.get_players() if p["code"] == code)
    his = [c for c in m["events"]["cards"] if c["player"] == pid]
    assert his == [{"player": pid, "colour": "red"}], his


def test_the_bonus_race_is_ordered_by_bps_and_carries_the_award(store):
    """⭐⭐ The one thing no livescore app has. ⚠️ Ordered by **BPS**, not by bonus: while the award is
    provisional (ADR-356 measured 96 minutes) the bonus column is still empty and the order is the story."""
    out = gameweek_scores(GameweekScoresRequest(gameweek=5, player_ids=[]), store=store)
    m = next(x for x in out["matches"] if x["bonus_race"])
    bps = [b["bps"] for b in m["bonus_race"]]
    assert bps == sorted(bps, reverse=True), bps
    assert len(m["bonus_race"]) <= mod.BONUS_RACE
    assert all({"player", "bonus", "bps"} == set(b) for b in m["bonus_race"])


def test_the_sidecar_names_only_the_players_it_references(store):
    """🔴 **The first version named every player with a history row** — all 667 across a gameweek, a
    sidecar of **126 KB** on a phone. ⭐ *That is the ADR-227 payload sin inside the change that cites it*,
    and only counting the bytes found it."""
    out = gameweek_scores(GameweekScoresRequest(gameweek=5, player_ids=[]), store=store)
    referenced = {
        e["player"]
        for m in out["matches"]
        for key in ("goals", "assists", "cards")
        for e in m["events"][key]
    } | {b["player"] for m in out["matches"] for b in m["bonus_race"]}

    assert {int(i) for i in out["people"]} == referenced
    assert len(out["people"]) < 200, f"{len(out['people'])} players named — the sidecar has run away"


def test_a_future_week_shows_who_is_involved_not_an_empty_card(store):
    """⭐⭐ **The owner's question: do future fixtures work?** They do — all 380 are scheduled with
    kick-off times — but `yours` is built from `player_history`, which does not exist before a match, so
    every forward card came back empty. ⚠️ Team membership answers *who is involved*; it never claims who
    will start, and it carries no points because there are none to carry."""
    from datetime import UTC, datetime, timedelta
    gw = 6
    later = datetime.now(UTC) + timedelta(days=7)
    with store.conn:
        store.conn.execute("DELETE FROM player_history WHERE round = ?", (gw,))
        store.conn.execute(
            "UPDATE fixtures SET started = 0, finished = 0, team_h_score = NULL, team_a_score = NULL, "
            "kickoff_time = ? WHERE event = ?", (later.isoformat(), gw))

    out = gameweek_scores(GameweekScoresRequest(gameweek=gw, player_ids=_squad(store)), store=store)
    involved = [m for m in out["matches"] if m["yours"]]
    assert involved, "a future week named none of the manager's players"

    for m in out["matches"]:
        assert m["events"] == {"goals": [], "assists": [], "cards": []}
        assert m["bonus_race"] == []
        assert m["status"] == "" and m["home_score"] is None
        for y in m["yours"]:
            # ⚠️ No points, no minutes: ⭐ *a nil return and a match not yet played must not look alike.*
            assert y["points"] is None and y["minutes"] is None and y["goals"] is None
            assert y["player"] is not None, "a slot with nobody in it"


def test_a_player_is_only_involved_in_his_own_clubs_fixture(store):
    """⚠️ The guard on the forward view: ⭐ *a fix that lists your whole squad under every match passes
    the test above and is useless.*"""
    from datetime import UTC, datetime, timedelta
    gw = 6
    later = datetime.now(UTC) + timedelta(days=7)
    with store.conn:
        store.conn.execute("DELETE FROM player_history WHERE round = ?", (gw,))
        store.conn.execute(
            "UPDATE fixtures SET started = 0, finished = 0, kickoff_time = ? WHERE event = ?",
            (later.isoformat(), gw))

    squad = _squad(store)
    out = gameweek_scores(GameweekScoresRequest(gameweek=gw, player_ids=squad), store=store)
    clubs = {t["short_name"]: t["id"] for t in store.get_teams()}
    by_id = {p["id"]: p for p in store.get_players()}

    for m in out["matches"]:
        sides = {clubs[m["home"]], clubs[m["away"]]}
        for y in m["yours"]:
            pid = y["player"]["id"]
            assert by_id[pid]["team_id"] in sides, f"{by_id[pid]['web_name']} is not in {m['home']}-{m['away']}"
    # ⭐ And nobody is listed twice across the week: a player has one fixture in a normal gameweek.
    listed = [y["player"]["id"] for m in out["matches"] for y in m["yours"]]
    assert len(listed) == len(set(listed)), "a player was involved in two matches"


# ── the current gameweek, before the backfill reaches it (ADR-361) ───────────────────────────────

def test_a_played_match_with_no_stored_history_reads_the_live_payload(store):
    """🔴🔴 **The current gameweek was blank, and it is the one that matters.** `backfill_due` fetches a
    round's history only once **every** fixture in it is complete — one request per player makes that
    deliberately rare (ADR-211 2d) — so GW7's Saturday matches carried no goals, no cards and no bonus
    race until the Monday night match settled the week.

    ⭐⭐ The data was already in hand: `/fixtures/` carries a `stats` block per match, and this module
    already fetched it. ⚠️ *The fix was to stop throwing it away.*
    """
    from datetime import UTC, datetime, timedelta
    gw = 6
    now = datetime(2026, 10, 18, 13, 0, tzinfo=UTC)
    # ⚠️⚠️ **Finished, and kicked off two days ago.** The first version of this test left the matches
    # unfinished three hours old, so `_playing` was true, the ordinary live fetch ran, and the fallback
    # was never reached — ⭐ *the mutation deleting the fallback passed it.* GW7's Saturday matches were
    # finished and outside the live window; that is the state to reproduce.
    ko = (now - timedelta(days=2)).isoformat()
    with store.conn:
        # the week is in the database; its history is not — exactly the live gameweek's state
        store.conn.execute("DELETE FROM player_history WHERE round = ?", (gw,))
        store.conn.execute(
            "UPDATE fixtures SET started = 1, finished = 1, team_h_score = 2, team_a_score = 1, "
            "kickoff_time = ? WHERE event = ?", (ko, gw))
    fixtures = [f for f in store.get_all_fixtures() if f["event"] == gw]
    ids = [p["id"] for p in store.get_players()][:4]

    class _Live:
        """FPL's own payload, carrying the stats the backfill has not yet stored."""
        def get_fixtures(self):
            return [{
                "id": f["id"], "event": gw, "team_h_score": 2, "team_a_score": 1,
                "minutes": 90, "started": True, "finished": True, "finished_provisional": True,
                "stats": [
                    {"identifier": "goals_scored", "h": [{"element": ids[0], "value": 2}], "a": []},
                    {"identifier": "assists", "h": [], "a": [{"element": ids[1], "value": 1}]},
                    {"identifier": "yellow_cards", "h": [{"element": ids[2], "value": 1}], "a": []},
                    {"identifier": "red_cards", "h": [], "a": [{"element": ids[3], "value": 1}]},
                    {"identifier": "bonus", "h": [{"element": ids[0], "value": 3}], "a": []},
                    {"identifier": "bps", "h": [{"element": ids[0], "value": 44}],
                     "a": [{"element": ids[1], "value": 31}]},
                ],
            } for f in fixtures]

    out = gameweek_scores(GameweekScoresRequest(gameweek=gw), store=store, client=_Live(), now=now)
    m = out["matches"][0]

    assert m["events"]["goals"] == [{"player": ids[0], "count": 2}]
    assert m["events"]["assists"] == [{"player": ids[1], "count": 1}]
    assert m["bonus_race"][0] == {"player": ids[0], "bonus": 3, "bps": 44}
    # ⭐ The sidecar is filled from this path too, or every name would draw as a dash.
    assert str(ids[0]) in out["people"]


def test_a_second_yellow_is_a_red_in_the_live_payload_too(store):
    """⚠️ The live payload records a dismissal as **both** a yellow and a red, exactly as history does.
    ⭐ *A rule that holds in one source and not the other is half a rule.*"""
    from datetime import UTC, datetime, timedelta
    gw = 6
    now = datetime(2026, 10, 18, 13, 0, tzinfo=UTC)
    with store.conn:
        store.conn.execute("DELETE FROM player_history WHERE round = ?", (gw,))
        store.conn.execute(
            "UPDATE fixtures SET started = 1, finished = 0, team_h_score = 1, team_a_score = 0, "
            "kickoff_time = ? WHERE event = ?", ((now - timedelta(hours=3)).isoformat(), gw))
    fixtures = [f for f in store.get_all_fixtures() if f["event"] == gw]
    sent_off = store.get_players()[0]["id"]

    class _Live:
        def get_fixtures(self):
            return [{
                "id": f["id"], "event": gw, "team_h_score": 1, "team_a_score": 0,
                "minutes": 90, "started": True, "finished": False,
                "stats": [
                    {"identifier": "yellow_cards", "h": [{"element": sent_off, "value": 1}], "a": []},
                    {"identifier": "red_cards", "h": [{"element": sent_off, "value": 1}], "a": []},
                ],
            } for f in fixtures]

    out = gameweek_scores(GameweekScoresRequest(gameweek=gw), store=store, client=_Live(), now=now)
    cards = out["matches"][0]["events"]["cards"]
    assert cards == [{"player": sent_off, "colour": "red"}], cards


def test_a_week_that_has_its_history_asks_upstream_for_nothing(store):
    """⭐ The economy: every past gameweek is complete in the database, so the fallback must never fire
    for one. ⚠️ *A fallback that always runs is not a fallback, it is a second fetch.*"""
    from datetime import UTC, datetime

    # ⚠️⚠️ **A double that RAISES proves nothing here**: `_live_fixtures` catches every exception and
    # degrades, by design — so the first version of this test passed even with the fallback firing on
    # every request. ⭐ *A spy that records is the only kind this module cannot swallow.*
    class _Spy:
        def __init__(self): self.asked = 0
        def get_fixtures(self):
            self.asked += 1
            return []

    spy = _Spy()
    out = gameweek_scores(GameweekScoresRequest(gameweek=5), store=store, client=spy,
                          now=datetime(2026, 10, 18, 13, 0, tzinfo=UTC))
    assert spy.asked == 0, "FPL was asked about a week whose history is already stored"
    assert any(m["events"]["goals"] for m in out["matches"])


def test_the_answer_names_whose_team_it_was_that_week(store):
    """🔴 **GW7 showed no purple dots at all.** The card marked a scorer as yours from `yours`, which is
    built from `player_history` — and the current week has none until the backfill reaches it (ADR-361).
    ⭐⭐ So the squad travels in its own right.

    ⚠️⚠️ **Not the caller's list echoed back.** For a played week this is FPL's own answer (ADR-350),
    because *the squad held today did not play last Saturday* — echoing the request would re-create
    exactly the bug that ADR records."""
    from datetime import UTC, datetime, timedelta
    gw, now = 5, datetime(2026, 10, 18, 13, 0, tzinfo=UTC)
    # ⚠️ A week still in play — GW7's real state, with Monday's match to come. ⭐ For a week already
    # settled the answer is FPL's, and the test below covers the refusal when it cannot be asked.
    with store.conn:
        store.conn.execute(
            "UPDATE fixtures SET started = 1, finished = 1, kickoff_time = ? WHERE event = ?",
            ((now - timedelta(days=1)).isoformat(), gw))
        store.conn.execute(
            "UPDATE fixtures SET started = 0, finished = 0, kickoff_time = ? "
            "WHERE id = (SELECT MIN(id) FROM fixtures WHERE event = ?)",
            ((now + timedelta(days=1)).isoformat(), gw))

    ids = _squad(store)
    out = gameweek_scores(GameweekScoresRequest(gameweek=gw, player_ids=ids), store=store, now=now)
    assert out["squad"], "nothing to draw a dot from"
    assert set(out["squad"]) <= set(ids)


def test_a_played_week_without_a_manager_id_names_nobody(store):
    """⭐ The same refusal as `yours` (ADR-350): with no way to ask FPL whose team it was, the answer is
    **nobody**, never the squad held today. ⚠️ *A dot on the wrong player is a wrong attribution with a
    confident colour.*"""
    from datetime import UTC, datetime
    gw = 5
    with store.conn:
        store.conn.execute("UPDATE fixtures SET started = 1, finished = 1 WHERE event = ?", (gw,))
    out = gameweek_scores(GameweekScoresRequest(gameweek=gw, player_ids=_squad(store)), store=store,
                          now=datetime(2026, 10, 18, 13, 0, tzinfo=UTC))
    assert out["squad"] == []
