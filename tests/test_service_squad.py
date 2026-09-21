"""The contract layer: `src/service` and its HTTP wrapper (Phase 3, mobile audit §4.2).

⭐⭐ **What this file is really guarding is that there is ONE product, not two.** The audit proposed
Streamlit migrate onto the HTTP API so the contract would have a real consumer — *"a contract with one
consumer is a guess"* — and we kept the principle while changing the mechanism: plain functions, imported
in-process by Streamlit and wrapped in FastAPI for Flutter. That buys back the round trip, and it costs
exactly one thing: **nothing now forces the two transports to agree**. So a test does.

⚠️ The interesting failures here are all *plausible answers*, never crashes: a squad of nine analysed as
nine, a bench that quietly excludes a player who is not in the squad, an HTTP path that computes a
marginally different total from the in-process one. Each would read as working.
"""

import json
import shutil

import pytest
from fastapi.testclient import TestClient

from src import config, pipeline
from src.service import SquadRequest, analysis
from src.service import inputs as service_inputs
from src.service.http import app
from src.storage import Storage

STAMP = "2026-09-21T09:00:00+00:00"


@pytest.fixture
def store(tmp_path, monkeypatch):
    """A seeded store on whichever backend the suite is pointed at.

    ⚠️ Pointing `config.SEED_DB_PATH` at the copy is load-bearing on Postgres, not tidiness: the harness
    seeds itself only when a caller asks for that path, and a bare `tmp_path` reads as *"this test builds
    its own fixture"* — see `tests/test_xp_board.py`, where that cost twelve green-on-SQLite tests.
    """
    target = tmp_path / "service.db"
    shutil.copy(config.SEED_DB_PATH, target)
    target.chmod(0o644)
    monkeypatch.setattr(config, "SEED_DB_PATH", str(target))
    s = Storage(config.SEED_DB_PATH)
    yield s
    s.close()


def _squad(store, size=15):
    """Fifteen players nobody would pick, but that FPL would allow — at most three per club."""
    picked, per_club = [], {}
    for p in store.get_players():
        if per_club.get(p["team"], 0) < 3 and len(picked) < size:
            picked.append(p["id"])
            per_club[p["team"]] = per_club.get(p["team"], 0) + 1
    return picked


# ---- validate: the checks whose absence produces a plausible answer --------------------

def test_a_well_formed_request_validates():
    SquadRequest(player_ids=[1, 2, 3], bench_ids=[3], horizon=5).validate()


@pytest.mark.parametrize("request_, expected", [
    (SquadRequest(player_ids=[]), "no players"),
    (SquadRequest(player_ids=[1, 2, 1]), "duplicate"),
    (SquadRequest(player_ids=[1], horizon=0), "outside 1-8"),
    (SquadRequest(player_ids=[1], horizon=9), "outside 1-8"),
    (SquadRequest(player_ids=[1, 2], bench_ids=[3]), "not in the squad"),
])
def test_requests_the_engine_would_mis_answer_are_refused(request_, expected):
    """⭐ Each of these returns *something* from `analyse_squad` if it gets through. A bench id that is not
    in the squad is the sharpest: it silently benches nobody and fields all fifteen."""
    with pytest.raises(ValueError, match=expected):
        request_.validate()


def test_the_boundary_horizons_are_allowed():
    """⚠️ The off-by-one that a `0 < h < 8` would introduce is invisible — horizon 8 is the UI's own slider
    maximum, so the app would refuse its own top setting."""
    for horizon in (1, 8):
        SquadRequest(player_ids=[1], horizon=horizon).validate()


# ---- analysis: the shape, and who decides the XI ---------------------------------------

def test_analysis_answers_the_horizon_that_was_asked_for(store):
    for horizon in (1, 3, 8):
        result = analysis(SquadRequest(player_ids=_squad(store), horizon=horizon), store=store)
        assert result["horizon"] == horizon
        assert len(result["gameweeks"]) == horizon, "the answer must cover the window it claims to"


def test_analysis_returns_the_whole_squad_split_into_an_xi_and_a_bench(store):
    result = analysis(SquadRequest(player_ids=_squad(store)), store=store)
    assert len(result["xi"]) == 11
    assert len(result["bench"]) == 4
    assert {p["id"] for p in result["xi"]} & {p["id"] for p in result["bench"]} == set()


def test_a_declared_bench_is_honoured_rather_than_re_optimised(store):
    """⭐ The engine picks the *best legal* XI, which is usually not the one the manager picked. A client
    that sends its own bench is stating a fact about their team, not asking for advice."""
    picked = _squad(store)
    bench = picked[-4:]
    result = analysis(SquadRequest(player_ids=picked, bench_ids=bench), store=store)
    assert {p["id"] for p in result["bench"]} == set(bench)


def test_an_absent_bench_is_derived_and_is_legal(store):
    """⚠️ Not merely "eleven players": the derived XI has to satisfy FPL's formation rules, which is the
    part a naive top-11-by-xP gets wrong."""
    result = analysis(SquadRequest(player_ids=_squad(store)), store=store)
    positions = [p["position"] for p in result["xi"]]
    assert positions.count("GK") == 1
    assert 3 <= positions.count("DEF") <= 5
    assert 1 <= positions.count("FWD") <= 3


def test_an_unknown_player_id_is_named_not_dropped(store):
    """⭐ A squad quietly analysed as fourteen players is a wrong answer wearing the shape of a right one —
    the projected total is simply lower, and nothing says why."""
    with pytest.raises(ValueError, match=r"unknown player ids: \[999999\]"):
        analysis(SquadRequest(player_ids=[*_squad(store, 14), 999999]), store=store)


# ---- one recipe: the board and the fallback must agree ---------------------------------

def test_reading_the_board_and_computing_from_history_give_the_same_answer(store):
    """⭐⭐ **The guard that makes ADR-218's shortcut safe.** An empty board is a real state — a fresh
    project, or the seed served when Postgres cannot be reached — so the fallback runs in production, not
    only in tests. If it drifted, two users would get different numbers for the same squad and neither
    would see an error.

    ⚠️ Computed *first*, because `decision_xp` prices a doubt against today (ADR-206 §2/§3): publish a board
    at one instant and compute at another and they legitimately differ, which would read as drift.
    """
    request = SquadRequest(player_ids=_squad(store))
    computed = analysis(request, store=store)          # board is empty → the fallback path
    pipeline.publish_board(store, computed_at=STAMP)
    from_board = analysis(request, store=store)        # → the read path

    assert store.get_xp_board(), "the board must actually be published, or this test compares nothing"
    assert from_board["projected_xp"] == computed["projected_xp"]
    assert [p["id"] for p in from_board["xi"]] == [p["id"] for p in computed["xi"]]
    assert from_board["weakest"] == computed["weakest"]


def test_the_board_path_does_not_read_the_history_tables(store, monkeypatch):
    """⭐ The point of ADR-218 is *not fetching 1.9 MB*, so the saving is what gets asserted — a version
    that reads the board and loads the history anyway passes every other test in this file."""
    pipeline.publish_board(store, computed_at=STAMP)

    def _forbidden(*args, **kwargs):
        raise AssertionError("the board was published; history must not be read")

    monkeypatch.setattr(store, "get_history_by_code", _forbidden)
    monkeypatch.setattr(store, "get_gw_history_by_code", _forbidden)
    assert analysis(SquadRequest(player_ids=_squad(store)), store=store)["projected_xp"] > 0


# ---- whose connection is it -------------------------------------------------------------

def test_a_callers_store_is_left_open(store):
    """⚠️ Streamlit passes a **cached** connection (ADR-217). Closing it would work once and then fail on
    every subsequent rerun — the failure arrives one interaction after the cause."""
    analysis(SquadRequest(player_ids=_squad(store)), store=store)
    assert store.get_players(), "the connection the caller owns must survive the call"


def test_a_store_the_service_opened_is_closed(monkeypatch):
    """⭐ The other half: a leak here is invisible until the connection pool is exhausted, which happens
    under load and never in a test."""
    closed = []

    class _Store:
        def get_players(self): return []
        def get_xp_board(self): return []
        def get_history_by_code(self): return {}
        def get_gw_history_by_code(self): return {}
        def get_upcoming_fixtures(self): return []
        def headline_events_by_id(self): return {}
        def close(self): closed.append(True)

    monkeypatch.setattr(service_inputs, "Storage", _Store)
    with pytest.raises(ValueError):                      # unknown ids — an empty store knows nobody
        analysis(SquadRequest(player_ids=[1]))
    assert closed == [True], "the store must be closed even when the analysis raises"


# ---- the HTTP transport -----------------------------------------------------------------

@pytest.fixture
def client(store, monkeypatch):
    """The wrapper, pointed at the same seeded store.

    ⚠️ `Storage()`'s default argument was bound at import, so patching `config.DB_PATH` would do nothing —
    the seam has to be the name the service module actually calls.
    """
    monkeypatch.setattr(service_inputs, "Storage", lambda: Storage(config.SEED_DB_PATH))
    return TestClient(app)


def test_health_answers_without_touching_the_database(client, monkeypatch):
    """⭐ A health check that fails when the database is slow reports on the database, not the service —
    and would take the app out of rotation for a dependency it can survive."""
    monkeypatch.setattr(service_inputs, "Storage", lambda: 1 / 0)
    assert client.get("/api/v1/health").json() == {"ok": True}


def test_the_two_transports_return_the_same_answer(client, store):
    """⭐⭐⭐ **The whole reason both exist.** Streamlit imports the function; Flutter posts JSON. Nothing
    but this test stops them becoming two products that disagree about your team.

    ⭐ Compared against the in-process answer **serialised**, rather than against the answer itself. JSON has
    no integer object keys, so `by_gameweek` crosses the wire as `{"6": ...}` — an *encoding* difference,
    forgiven here by construction. Every difference that is not JSON's own still fails, which is the part
    worth keeping: a field the wrapper drops, rounds, renames or recomputes breaks this test.
    """
    picked = _squad(store)
    over_http = client.post("/api/v1/squad/analysis",
                            json={"player_ids": picked, "horizon": 5}).json()
    in_process = analysis(SquadRequest(player_ids=picked, horizon=5), store=store)
    assert over_http == json.loads(json.dumps(in_process))


def test_gameweek_keys_cross_the_wire_as_strings(client, store):
    """⚠️ **Pinned because a client that ignores it misreads the board**, exactly as `storage.py` warns of
    the published `by_gameweek` — and silently: sorting `{"10", "6", "7"}` as text puts GW10 first, so the
    prefix sum for "the next 2 gameweeks" would quietly answer for the wrong two.

    ⭐ The Flutter slice already does the right thing (`int.parse` into a `Map<int, double>`, then sort), and
    it does it against **PostgREST serving this same column** — so this is the established shape rather than
    a new one. The test states it so a future client author reads it as a contract, not a surprise.
    """
    body = client.post("/api/v1/squad/analysis",
                       json={"player_ids": _squad(store), "horizon": 3}).json()
    weeks = body["xi"][0]["by_gameweek"]
    assert all(isinstance(k, str) for k in weeks)
    assert sorted(int(k) for k in weeks) == body["gameweeks"], (
        "the keys must be the gameweeks the answer covers, so a client can pair them without guessing"
    )


def test_a_bad_squad_is_the_callers_mistake_not_a_server_fault(client):
    """⭐ 400, with the reason. A 500 tells a client author to retry something that will never work."""
    response = client.post("/api/v1/squad/analysis", json={"player_ids": [999999]})
    assert response.status_code == 400
    assert "999999" in response.json()["detail"]


@pytest.mark.parametrize("body", [
    {"player_ids": []},
    {"player_ids": [1], "horizon": 0},
    {"player_ids": [1], "horizon": 9},
    {"horizon": 5},
])
def test_a_malformed_body_is_refused_before_the_database_is_opened(client, monkeypatch, body):
    """⚠️ Validation at the edge is not duplication of `SquadRequest.validate()` — it is what stops a
    garbage request costing a connection. The same checks live in the dataclass for the in-process caller,
    which never passes through here."""
    monkeypatch.setattr(service_inputs, "Storage", lambda: 1 / 0)
    assert client.post("/api/v1/squad/analysis", json=body).status_code == 422


def test_the_response_is_json_a_client_can_hold(client, store):
    """⭐ §4.1's budget is about bytes on a phone. A squad answer that arrived as a megabyte would push the
    client back towards computing its own — which is the thing this layer exists to prevent."""
    response = client.post("/api/v1/squad/analysis", json={"player_ids": _squad(store), "horizon": 5})
    assert response.status_code == 200
    assert len(response.content) < 50_000, "a squad answer should be a few KB, not a payload"
    assert set(response.json()) >= {"projected_xp", "xi", "bench", "issues", "club_counts"}


# ---- the fact that took six surfaces to learn --------------------------------------------

def test_a_reported_departure_reaches_the_contract(store, monkeypatch):
    """⭐⭐ **ADR-151→156 is the record of this one fact being re-taught to six surfaces**, every gap found
    by the owner using the product. It belongs in the layer both transports share, or the seventh surface
    is a phone.

    ⚠️ **Constructed, not sampled.** Whether today's seed happens to contain a reported leaver is an
    accident of the snapshot, and a fixture that cannot reach the case would confirm a broken wiring —
    this codebase has four root causes of exactly that shape.
    """
    picked = _squad(store)
    clean = analysis(SquadRequest(player_ids=picked), store=store)
    going = clean["top_pick"]["id"]                       # the best player on it — so the effect is visible

    from src.analytics import headlines
    monkeypatch.setattr(headlines, "leavers",
                        lambda owned, events, exodus_for, *, today: {going: {"kind": "transfer"}})
    flagged = analysis(SquadRequest(player_ids=picked), store=store)

    assert going in {p["id"] for p in flagged["issues"]}, "a departure is an availability issue"
    assert flagged["top_pick"]["id"] != going, (
        "⭐ it reaches past the issues list: `analyse_squad` drops a reported leaver from the captainable "
        "set, so omitting it would have a phone recommending the captaincy the web app already withholds"
    )
    assert next(p for p in flagged["xi"] + flagged["bench"]
                if p["id"] == going)["leaving"] == {"kind": "transfer"}


def test_a_store_without_headlines_still_answers(store, monkeypatch):
    """⭐ The departure signal is a bonus on top of the snapshot, never a dependency — a database built
    before the events table existed must analyse a squad exactly as it did before."""
    monkeypatch.setattr(store, "headline_events_by_id",
                        lambda: (_ for _ in ()).throw(RuntimeError("no such table: headline_events")))
    assert analysis(SquadRequest(player_ids=_squad(store)), store=store)["projected_xp"] > 0


def test_the_exodus_threshold_is_read_from_the_league_not_the_squad(store):
    """⚠️ **A tenth of fifteen is one or two players, every single week.** ADR-210's threshold is the worst
    tenth of the *live league* distribution, so handing it the squad would manufacture a departure rumour
    for somebody's worst forward on a quiet Tuesday — and it would look like a working feature.

    ⭐ Found by mutation: swapping `players` for `owned` passed every other test here, because they stub
    `leavers` and never reach the argument.
    """
    seen = []

    from src.analytics import crowd
    real = crowd.exodus_detector

    def _spy(population):
        seen.append(len(population))
        return real(population)

    crowd.exodus_detector = _spy
    try:
        picked = _squad(store)
        analysis(SquadRequest(player_ids=picked), store=store)
    finally:
        crowd.exodus_detector = real

    assert seen, "the detector must actually be built, or this asserts nothing"
    assert seen[0] > len(picked), (
        f"the threshold saw {seen[0]} players; the squad is {len(picked)} — it must read the whole league"
    )
