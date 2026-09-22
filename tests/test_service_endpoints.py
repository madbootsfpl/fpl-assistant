"""The other five squad endpoints (ADR-220) — transfers · captain · gameweek-plan · route · build.

⭐⭐ **What this file mostly guards is ARGUMENTS, not answers.** The engine functions are covered by their
own tests; what is new here is the *wiring*, and every bug this layer can introduce is a silent opt-out —
an optional argument not passed, so the ranking still returns and simply names a different player. ADR-181
named that species; ADR-220 found it live on the web app's Transfer tab, where ADR-209's `window` and
`horizon_xp` had never been threaded.

⚠️ So the tests below assert *what the engine was told*. A test that only checked the shape of the answer
would have passed against the defect that prompted this file.
"""

import json
import shutil

import pytest
from fastapi.testclient import TestClient

from src import config
from src.service import (
    BuildRequest,
    CaptainRequest,
    ChipsRequest,
    FeedbackRequest,
    GameweekRequest,
    MyTeamRequest,
    PlayersRequest,
    ReplacementsRequest,
    RouteRequest,
    SignalsRequest,
    SquadRequest,
    TransfersRequest,
)
from src.service import answers as svc
from src.service import inputs as service_inputs
from src.service.http import app
from src.storage import Storage


@pytest.fixture
def store(tmp_path, monkeypatch):
    """A seeded store on whichever backend the suite is pointed at (see `tests/test_xp_board.py` for why
    `config.SEED_DB_PATH` has to be the thing pointed at, rather than a bare `tmp_path`)."""
    target = tmp_path / "endpoints.db"
    shutil.copy(config.SEED_DB_PATH, target)
    target.chmod(0o644)
    monkeypatch.setattr(config, "SEED_DB_PATH", str(target))
    s = Storage(config.SEED_DB_PATH)
    yield s
    s.close()


def _squad(store, size=15):
    """A legal-shaped fifteen: the FPL position split, at most three per club."""
    need = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}
    picked, per_club = [], {}
    for p in store.get_players():
        pos = p["position"]
        if need.get(pos, 0) and per_club.get(p["team"], 0) < 3 and len(picked) < size:
            picked.append(p["id"])
            need[pos] -= 1
            per_club[p["team"]] = per_club.get(p["team"], 0) + 1
    return picked


@pytest.fixture
def client(store, monkeypatch):
    monkeypatch.setattr(service_inputs, "Storage", lambda: Storage(config.SEED_DB_PATH))
    return TestClient(app)


# ---- transfers: the arguments ADR-209 exists for ---------------------------------------

def test_the_transfer_search_is_told_which_window_it_is_ranking(store, monkeypatch):
    """⭐⭐⭐ **The guard for the defect that prompted this work.** `window` sizes the tie-break band, and it
    defaults to five — so a one-gameweek ranking passed no window gets a band built for five gameweeks, and
    ADR-209 measured that band as *silently deciding every one-GW recommendation*.

    ⚠️ Nothing about the answer's shape reveals it. The ranking returns either way; it simply names a
    different player, which is why this asserts the call and not the result.
    """
    seen = {}
    real = svc.suggest_transfers
    monkeypatch.setattr(svc, "suggest_transfers",
                        lambda *a, **kw: (seen.update(kw), real(*a, **kw))[1])

    svc.transfers(TransfersRequest(player_ids=_squad(store), horizon=1, bank=2.0), store=store)
    assert seen["window"] == 1, "the band must be sized for the window the xP map actually covers"


def test_a_near_tie_gets_the_longer_view_to_break_it(store, monkeypatch):
    """⭐⭐ ADR-209's other half, and the one that moves expected points. Two moves worth +1.2 apiece over
    one gameweek are a dead heat on the number being ranked; the owner's week had one worth −1.5 over five
    and the other +3.1, and the app **had that number and never let it choose**.

    ⚠️ `_horizon_gain` returns 0.0 when no wider map is supplied, so omitting it does not fail — it makes
    the first tie-break key a constant and quietly hands the decision to the next one.
    """
    seen = {}
    real = svc.suggest_transfers

    def _spy(*args, **kwargs):
        # ⚠️ **Positional args captured too, and that is not tidiness.** `xp_by_id` is the third positional
        # argument, so an earlier version of this test compared `horizon_xp` against `kwargs["xp_by_id"]` —
        # which was always `None`, making the assertion `wider is not None` wearing the costume of a
        # comparison. ⭐ *A hedge is not a weaker assertion; it is the absence of one* (ADR-180).
        seen["ranked_on"] = args[2]
        seen.update(kwargs)
        return real(*args, **kwargs)

    monkeypatch.setattr(svc, "suggest_transfers", _spy)

    svc.transfers(TransfersRequest(player_ids=_squad(store), horizon=1), store=store)
    wider = seen["horizon_xp"]
    assert wider, "a one-gameweek question must carry the five-gameweek map"
    assert wider != seen["ranked_on"], (
        "…and it must be a genuinely WIDER map — built at five gameweeks, not the ranking's own numbers "
        "handed back to break their own tie"
    )


def test_at_the_wide_horizon_there_is_no_wider_view_to_consult(store, monkeypatch):
    """⭐ The symmetry worth pinning: at five gameweeks the longer view *is* the ranking, so supplying it
    would be asking the same number to break its own tie."""
    seen = {}
    real = svc.suggest_transfers
    monkeypatch.setattr(svc, "suggest_transfers",
                        lambda *a, **kw: (seen.update(kw), real(*a, **kw))[1])

    result = svc.transfers(TransfersRequest(player_ids=_squad(store), horizon=5), store=store)
    assert seen["horizon_xp"] is None
    assert result["longer_window"] is None, "…and the answer says so, rather than implying a wider read"


def test_a_departure_reaches_the_transfer_ranking(store, monkeypatch):
    seen = {}
    real = svc.suggest_transfers
    monkeypatch.setattr(svc, "suggest_transfers",
                        lambda *a, **kw: (seen.update(kw), real(*a, **kw))[1])
    picked = _squad(store)

    from src.analytics import headlines
    monkeypatch.setattr(headlines, "leavers",
                        lambda owned, events, exodus_for, *, today: {picked[0]: {"kind": "transfer"}})
    svc.transfers(TransfersRequest(player_ids=picked), store=store)
    assert seen["reported_out"] == {picked[0]: {"kind": "transfer"}}


def test_more_than_one_move_is_a_coordinated_plan_not_a_menu(store):
    """⚠️ ADR-191 — two *alternatives* each priced against the same bank double-count the money, so the
    gains do not add up. A plan threads the bank through."""
    picked = _squad(store)
    plan = svc.transfers(TransfersRequest(player_ids=picked, count=2, bank=3.0), store=store)
    menu = svc.transfers(TransfersRequest(player_ids=picked, count=1, limit=2, bank=3.0), store=store)
    assert plan["coordinated"] is True
    assert menu["coordinated"] is False
    if len(plan["moves"]) == 2:
        out_ids = [m["out"]["id"] for m in plan["moves"]]
        assert len(set(out_ids)) == 2, "a plan must not sell the same player twice"


# ---- captain ----------------------------------------------------------------------------

def test_the_captain_is_always_next_gameweek(store):
    """⚠️ Captaincy is a one-week bet whatever window the client sent. ⭐ The request accepts `horizon` so
    one client-side squad object serves every endpoint — it must not quietly become a five-week pick."""
    picked = _squad(store)
    one = svc.captain(CaptainRequest(player_ids=picked, horizon=1), store=store)
    five = svc.captain(CaptainRequest(player_ids=picked, horizon=5), store=store)
    assert [p["id"] for p in one["picks"]] == [p["id"] for p in five["picks"]]


def test_the_captain_reads_minutes_from_this_seasons_history(store, monkeypatch):
    """⭐⭐ ADR-173, and the owner found it by using the product: *"different recommendations from My Squad
    'what should I do this week' and captaincy."* Every other caller passed the per-gameweek minutes weight;
    the captain tab never did, so two surfaces answered one question from two models."""
    seen = {}
    real = svc.captain_picks
    monkeypatch.setattr(svc, "captain_picks",
                        lambda *a, **kw: (seen.update(kw), real(*a, **kw))[1])

    svc.captain(CaptainRequest(player_ids=_squad(store)), store=store)
    assert seen["minutes_weight"] is not None, "a rotation risk must not out-rank a nailed-on starter"
    assert seen["history_by_code"], "…and the raw rows reach `player_xp`"
    assert seen["baseline_by_code"], (
        "…and the per-club baseline rates are derived from that same history, not defaulted away"
    )


def test_the_captain_reads_history_even_when_a_board_is_published(store, monkeypatch):
    """⭐⭐ **The board is not a substitute here, and the seed cannot show that.** `captain_picks` reprices
    at horizon 1 through `player_xp`; reading a stored multi-gameweek total instead would be a second recipe
    for the same number (ADR-041).

    ⚠️ **The board is published inside the test on purpose.** With an empty board the loader fetches history
    regardless, so every assertion here passes vacuously — a mutation removing the `need_history` flag
    survived precisely because the seed contains no board. ⭐ *The tell is always: does the population
    contain the case?*
    """
    from src import pipeline
    pipeline.publish_board(store, computed_at="2026-09-21T09:00:00+00:00")
    assert store.get_xp_board(), "the board must exist, or this test asserts nothing"

    seen = []
    real = store.get_history_by_code
    monkeypatch.setattr(store, "get_history_by_code", lambda: (seen.append(1), real())[1])
    svc.captain(CaptainRequest(player_ids=_squad(store)), store=store)
    assert seen, "captain must still read the raw history when a board exists"


def test_transfers_skip_the_history_when_a_board_is_published(store, monkeypatch):
    """⭐ The other side of the same decision (ADR-218): the transfer search ranks on a total the pipeline
    already computed, so it reads ~250 KB instead of 1.9 MB. ⚠️ Asserting the *saving*, because a version
    that reads the board and loads the history anyway passes every other test in this file."""
    from src import pipeline
    pipeline.publish_board(store, computed_at="2026-09-21T09:00:00+00:00")

    def _forbidden():
        raise AssertionError("the board was published; history must not be read")

    monkeypatch.setattr(store, "get_history_by_code", _forbidden)
    monkeypatch.setattr(store, "get_gw_history_by_code", _forbidden)
    assert svc.transfers(TransfersRequest(player_ids=_squad(store), bank=2.0), store=store)["moves"]


def test_the_captain_shortlist_is_capped_by_the_request(store):
    picks = svc.captain(CaptainRequest(player_ids=_squad(store), limit=3), store=store)["picks"]
    assert len(picks) <= 3


def test_a_goalkeeper_is_never_offered_as_captain(store):
    picks = svc.captain(CaptainRequest(player_ids=_squad(store), limit=15), store=store)["picks"]
    assert all(p.get("position") != "GK" for p in picks)


# ---- the gameweek plan ------------------------------------------------------------------

def test_the_plan_answers_every_part_of_the_week(store):
    plan = svc.gameweek(GameweekRequest(player_ids=_squad(store), bank=2.0, free=1, horizon=1), store=store)
    assert {"captain", "lineup", "transfers", "timing", "flags", "free", "bank"} <= set(plan)


def test_the_plan_states_the_position_it_assumed(store):
    """⭐ ADR-191 — `free` and `bank` had been hard-coded while the Transfer tab collected them three tabs
    away, so the surface a manager reads was advising a position he was not in. ⭐ *A stated assumption can
    be corrected where a silent one cannot.*"""
    plan = svc.gameweek(GameweekRequest(player_ids=_squad(store), bank=4.5, free=2), store=store)
    assert plan["free"] == 2
    assert plan["bank"] == 4.5


def test_the_plan_recommends_as_many_moves_as_the_manager_holds(store):
    plan = svc.gameweek(GameweekRequest(player_ids=_squad(store), bank=6.0, free=2), store=store)
    assert len(plan["transfers"]) <= 2


def test_the_exodus_threshold_is_read_from_the_league_not_the_squad(store, monkeypatch):
    """⚠️ ADR-210's threshold is the worst tenth of the **live league** distribution. A tenth of fifteen is
    one or two players, every single week — a manufactured departure rumour that looks like a feature."""
    seen = []
    from src.analytics import crowd
    real = crowd.exodus_detector
    monkeypatch.setattr(crowd, "exodus_detector", lambda pop: (seen.append(len(pop)), real(pop))[1])

    picked = _squad(store)
    svc.gameweek(GameweekRequest(player_ids=picked), store=store)
    assert seen and min(seen) > len(picked)


# ---- route (ADR-207) --------------------------------------------------------------------

def test_a_route_names_the_target_and_its_price(store):
    picked = _squad(store)
    target = next(p["id"] for p in store.get_players() if p["id"] not in picked)
    answer = svc.route(RouteRequest(player_ids=picked, target_id=target, bank=3.0), store=store)
    assert answer["target"]["id"] == target
    assert answer["target"]["price"] > 0


def test_a_target_already_owned_is_said_plainly(store):
    """⭐ The question *"what would it take?"* has an answer when you already hold him, and it is not an
    empty route list."""
    picked = _squad(store)
    answer = svc.route(RouteRequest(player_ids=picked, target_id=picked[0]), store=store)
    assert answer["owned"] is True
    assert answer["routes"] == []


def test_an_unaffordable_target_reports_the_shortfall_rather_than_nothing(store):
    """⭐⭐ **A blocked route is information, not an absence.** *"Short by £0.6m"* answers the question; an
    empty list looks like the question was not understood."""
    picked = _squad(store)
    dearest = max((p for p in store.get_players() if p["id"] not in picked), key=lambda p: p["price"])
    answer = svc.route(RouteRequest(player_ids=picked, target_id=dearest["id"], bank=0.0), store=store)
    assert answer["routes"] or answer["blocked"], "one or the other, never silence"


def test_an_unknown_target_is_named(store):
    """⚠️ On a **valid** squad — with a bad squad the earlier check fires first, and a test written that way
    passes while the target is never checked at all. (It was; the mutation survived.)"""
    with pytest.raises(ValueError, match=r"unknown player ids: \[999998\]"):
        svc.route(RouteRequest(player_ids=_squad(store), target_id=999998), store=store)


def test_a_departure_re_ranks_the_route(store, monkeypatch):
    """⚠️ The CLI never passed `reported_out` here. Without it a manager is routed *through* a player the
    rest of the app knows is leaving — ADR-155's species, one function along."""
    seen = {}
    real = svc.route_to_player
    monkeypatch.setattr(svc, "route_to_player",
                        lambda *a, **kw: (seen.update(kw), real(*a, **kw))[1])
    picked = _squad(store)
    target = next(p["id"] for p in store.get_players() if p["id"] not in picked)

    from src.analytics import headlines
    monkeypatch.setattr(headlines, "leavers",
                        lambda owned, events, exodus_for, *, today: {picked[0]: {"kind": "transfer"}})
    svc.route(RouteRequest(player_ids=picked, target_id=target), store=store)
    assert seen["reported_out"] == {picked[0]: {"kind": "transfer"}}


# ---- build ------------------------------------------------------------------------------

def test_a_built_squad_is_legal_and_within_budget(store):
    result = svc.build(BuildRequest(budget=100.0), store=store)
    assert result["status"] == "Optimal"
    assert len(result["selected"]) == 15
    assert result["total_cost"] <= 100.0
    positions = [p["position"] for p in result["selected"]]
    assert positions.count("GK") == 2
    assert positions.count("DEF") == 5
    assert positions.count("MID") == 5
    assert positions.count("FWD") == 3


def test_a_forced_player_is_in_the_squad(store):
    wanted = store.get_players()[30]["id"]
    result = svc.build(BuildRequest(budget=100.0, include_ids=[wanted]), store=store)
    assert wanted in {p["id"] for p in result["selected"]}


def test_an_excluded_player_is_not(store):
    first = svc.build(BuildRequest(budget=100.0), store=store)
    banned = first["selected"][0]["id"]
    result = svc.build(BuildRequest(budget=100.0, exclude_ids=[banned]), store=store)
    assert banned not in {p["id"] for p in result["selected"]}


def test_an_impossible_budget_says_so_rather_than_returning_an_empty_squad(store):
    """⭐ The solver's own word, surfaced. Swallowing `Infeasible` would leave a client showing an empty
    squad with no reason — *nothing fits these constraints* is an answer, not a failure."""
    result = svc.build(BuildRequest(budget=10.0), store=store)
    assert result["status"] != "Optimal"
    assert result["selected"] == []


def test_the_build_optimises_the_horizon_it_was_asked_for(store, monkeypatch):
    """⚠️ Without the xP map the solver still returns a legal, affordable, correctly-shaped fifteen — it
    just optimises last season's total points instead. ⭐ *Every structural assertion in this file passes
    against a squad chosen on the wrong objective*, which is why this asserts the objective itself."""
    seen = {}
    real = svc.select_squad
    monkeypatch.setattr(svc, "select_squad", lambda *a, **kw: (seen.update(kw), real(*a, **kw))[1])

    svc.build(BuildRequest(budget=100.0, horizon=1), store=store)
    one = seen["scores"]
    svc.build(BuildRequest(budget=100.0, horizon=5), store=store)
    five = seen["scores"]

    assert one and five, "the solver must be given an xP map to rank on"
    assert one != five, "…and it must be the map for the horizon asked for, not one fixed window"


def test_a_player_both_forced_in_and_ruled_out_is_refused(store):
    """⚠️ Without this the solver simply returns nothing, and *"Infeasible"* reads as *your budget is too
    low* rather than *you asked for a player you also banned*."""
    with pytest.raises(ValueError, match="both included and excluded"):
        svc.build(BuildRequest(include_ids=[1], exclude_ids=[1]), store=store)


# ---- validation -------------------------------------------------------------------------

@pytest.mark.parametrize("request_, expected", [
    (TransfersRequest(player_ids=[1], bank=-1.0), "bank cannot be negative"),
    (TransfersRequest(player_ids=[1], count=4), "count 4 is outside"),
    (TransfersRequest(player_ids=[1], limit=0), "limit must be at least 1"),
    (CaptainRequest(player_ids=[1], limit=0), "limit must be at least 1"),
    (GameweekRequest(player_ids=[1], free=9), "free transfers 9 is outside"),
    (GameweekRequest(player_ids=[1], bank=-0.1), "bank cannot be negative"),
    (RouteRequest(player_ids=[1]), "no target player given"),
    (BuildRequest(budget=0), "budget must be positive"),
])
def test_requests_that_would_produce_a_plausible_wrong_answer_are_refused(request_, expected):
    with pytest.raises(ValueError, match=expected):
        request_.validate()


# ---- one contract, two transports -------------------------------------------------------

@pytest.mark.parametrize("path, body, call", [
    ("analysis", {}, lambda ids: (SquadRequest(player_ids=ids), "analysis")),
    ("transfers", {"bank": 2.0, "horizon": 1}, lambda ids: (TransfersRequest(player_ids=ids, bank=2.0, horizon=1), "transfers")),
    ("captain", {}, lambda ids: (CaptainRequest(player_ids=ids), "captain")),
    ("gameweek-plan", {"bank": 2.0, "free": 1}, lambda ids: (GameweekRequest(player_ids=ids, bank=2.0, free=1), "gameweek")),
])
def test_every_endpoint_returns_over_http_what_it_returns_in_process(client, store, path, body, call):
    """⭐⭐⭐ **The whole reason both transports exist** (ADR-219). Streamlit imports the function; Flutter
    posts JSON. Nothing but this stops them becoming two products that disagree about your team.

    ⭐ Compared against the in-process answer **serialised**: JSON has no integer object keys, so
    `by_gameweek` crosses as `{"6": …}`. That encoding is forgiven by construction; a field the wrapper
    drops, rounds, renames or recomputes still fails.
    """
    import src.service as service

    picked = _squad(store)
    over_http = client.post(f"/api/v1/squad/{path}", json={"player_ids": picked, **body}).json()
    request_, fn = call(picked)
    in_process = getattr(service, fn)(request_, store=store)
    assert over_http == json.loads(json.dumps(in_process))


def test_route_returns_over_http_what_it_returns_in_process(client, store):
    import src.service as service

    picked = _squad(store)
    target = next(p["id"] for p in store.get_players() if p["id"] not in picked)
    over_http = client.post("/api/v1/squad/route",
                            json={"player_ids": picked, "target_id": target, "bank": 2.0}).json()
    in_process = service.route(RouteRequest(player_ids=picked, target_id=target, bank=2.0), store=store)
    assert over_http == json.loads(json.dumps(in_process))


def test_build_returns_over_http_what_it_returns_in_process(client, store):
    import src.service as service

    over_http = client.post("/api/v1/squad/build", json={"budget": 100.0}).json()
    in_process = service.build(BuildRequest(budget=100.0), store=store)
    assert over_http == json.loads(json.dumps(in_process))


@pytest.mark.parametrize("path, body", [
    ("transfers", {"player_ids": [1], "bank": -1}),
    ("transfers", {"player_ids": [1], "count": 9}),
    ("captain", {"player_ids": []}),
    ("gameweek-plan", {"player_ids": [1], "free": 99}),
    ("route", {"player_ids": [1]}),
    ("build", {"budget": -5}),
])
def test_a_malformed_body_is_refused_before_the_database_is_opened(client, monkeypatch, path, body):
    """⚠️ Edge validation is not duplication of the dataclass — it is what stops a garbage request costing a
    connection. The dataclass still guards the in-process caller, which never passes through here."""
    monkeypatch.setattr(service_inputs, "Storage", lambda: 1 / 0)
    assert client.post(f"/api/v1/squad/{path}", json=body).status_code == 422


def test_an_unknown_player_is_the_callers_mistake_on_every_endpoint(client):
    for path, body in [("transfers", {}), ("captain", {}), ("gameweek-plan", {}),
                       ("route", {"target_id": 999998})]:
        response = client.post(f"/api/v1/squad/{path}", json={"player_ids": [999999], **body})
        assert response.status_code == 400, f"{path} should name the bad id, not fail"
        assert "999999" in response.json()["detail"]


# ---- a browser has to be able to call this ----------------------------------------------

def test_a_browser_can_call_the_api(client):
    """⭐ **Flutter's first runnable target is the web one.** `flutter doctor` reports Chrome ✓ while Xcode
    is still incomplete, so the first calls the mobile client makes will come from a browser — and without
    CORS every one of them fails.

    ⚠️ **The failure would not have read as CORS.** The browser reports an opaque network error and the
    server logs a perfectly ordinary 200, so the obvious place to look is the client. This is cheap to pin
    and expensive to diagnose.
    """
    preflight = client.options("/api/v1/squad/analysis", headers={
        "Origin": "http://localhost:8080",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert preflight.status_code == 200
    assert preflight.headers.get("access-control-allow-origin") == "*"


def test_any_port_is_allowed_because_flutter_picks_its_own(client, store):
    """⚠️ `flutter run -d chrome` binds a **random** port unless told otherwise, so an origin allow-list
    written today would break tomorrow with no code change. ⭐ Allowed because these endpoints serve *ids in,
    analysis out* — nothing a hostile page could read that it could not read by calling the API itself."""
    response = client.post("/api/v1/squad/analysis",
                           json={"player_ids": _squad(store)},
                           headers={"Origin": "http://localhost:59123"})
    assert response.headers.get("access-control-allow-origin") == "*"


def test_credentials_are_never_echoed(client, store):
    """🔴 **The guard that outlives the reason.** `allow_credentials` with `*` is forbidden by the spec, and
    Starlette enforces it by quietly refusing to echo the origin — so the failure mode is *an app that works
    until someone adds a cookie*, which is exactly when nobody is looking at CORS.

    ⭐ When Stage C makes an endpoint owner-scoped, this test should fail and be rewritten with a real
    allow-list — it is the tripwire on the assumption, not decoration.
    """
    response = client.post("/api/v1/squad/analysis",
                           json={"player_ids": _squad(store)},
                           headers={"Origin": "http://localhost:8080"})
    assert response.headers.get("access-control-allow-credentials") is None


# ---- my-team: the landing pitch (ADR-222) -----------------------------------------------

@pytest.fixture
def team(store, monkeypatch):
    """A manager whose squad is the seed's, with the FPL fetch stubbed out.

    ⚠️ **Stubbed because the real one calls FPL over the network.** A test that reaches the internet is not
    a test — it passes or fails on someone else's uptime, and this suite has an ADR about exactly that
    (`conftest.py`, the language-model stub). What is under test is the *composition*, not the fetch.
    """
    picked = _squad(store)
    squad = {"name": "RoboTS", "player_ids": picked, "bench_ids": picked[-4:],
             "captain_id": picked[0], "vice_captain_id": picked[1]}
    monkeypatch.setattr(svc, "fetch_manager_team", lambda entry_id, players: (squad, ""))
    return squad


def test_my_team_carries_everything_the_pitch_draws(store, team):
    """⭐⭐ **The reason this endpoint exists.** The pitch needs ten things `analysis` does not return — the
    gameweek, the deadline, both armbands, the kit, the opponent, the venue, the difficulty and the bench
    order. ⚠️ Without them a phone makes five round trips before it can draw anything.
    """
    answer = svc.my_team(MyTeamRequest(manager_id=2885974, horizon=1), store=store)

    assert answer["squad"]["captain_id"] == team["captain_id"]
    assert answer["squad"]["vice_captain_id"] == team["vice_captain_id"]
    assert answer["gameweek"]
    assert answer["deadline"]["label"] and answer["deadline"]["at"]
    assert answer["analysis"]["xi"] and answer["analysis"]["bench"]
    assert answer["kits"] and answer["fixtures"]
    assert set(answer["bench_roles"]) <= {"1st", "2nd", "3rd", "GK"}


def test_the_analysis_inside_is_the_same_analysis(store, team):
    """⭐ **One recipe** (ADR-041/181). A composing endpoint that quietly priced the squad differently from
    `/squad/analysis` would put two answers about one team in the same app — the failure this whole layer
    exists to prevent, arriving by the back door."""
    composed = svc.my_team(MyTeamRequest(manager_id=2885974, horizon=1), store=store)["analysis"]
    direct = svc.analysis(SquadRequest(player_ids=team["player_ids"], bench_ids=team["bench_ids"],
                                       horizon=1), store=store)
    assert composed == direct


def test_every_map_is_keyed_by_something_json_leaves_alone(store, team):
    """⚠️⚠️ **The trap this endpoint was shaped to avoid.** `by_gameweek` is keyed by integer gameweek and
    crosses the wire as `{"6": …}`, where sorting as text puts `"10"` first. ⭐ So kits and fixtures are
    keyed by **club short name** and bench roles by **role** — strings already, which JSON cannot change.

    Keying any of them by player id would have repeated the mistake on a new screen.
    """
    answer = svc.my_team(MyTeamRequest(manager_id=2885974), store=store)
    for field in ("kits", "fixtures", "bench_roles"):
        for key in answer[field]:
            assert isinstance(key, str), f"{field} is keyed by {type(key).__name__}, not str"
            assert not key.isdigit(), f"{field} key {key!r} is a number wearing a string"


def test_a_keeper_gets_the_keeper_kit(store, team):
    """⚠️ FPL serves a separate goalkeeper shirt (`_1`). Drawing the outfield kit on a keeper is wrong on
    every pitch in the game, and it is the sort of wrong nobody reports — it just looks cheap."""
    answer = svc.my_team(MyTeamRequest(manager_id=2885974), store=store)
    club, urls = next(iter(answer["kits"].items()))
    assert urls["gk"] != urls["outfield"], f"{club} serves one kit for both"
    assert "_1" in urls["gk"]


def test_the_bench_is_ordered_the_way_fpl_will_substitute(store, team):
    """⭐ Role → id, so the phone shows the order FPL will actually use. ⚠️ Without it a client invents an
    order and the first auto-sub proves it wrong, on the screen a manager checks most."""
    answer = svc.my_team(MyTeamRequest(manager_id=2885974), store=store)
    roles = answer["bench_roles"]
    assert set(roles.values()) <= set(team["bench_ids"])
    assert len(set(roles.values())) == len(roles), "no player may hold two bench roles"


def test_the_landing_pitch_looks_at_this_gameweek_by_default(store, team):
    """⭐ Every other endpoint defaults to five. A landing pitch is about the week you are in, and the
    default is where that decision lives — not in a caller that might forget."""
    answer = svc.my_team(MyTeamRequest(manager_id=2885974), store=store)
    assert answer["analysis"]["horizon"] == 1
    assert len(answer["analysis"]["gameweeks"]) == 1


def test_a_team_that_is_not_public_yet_says_so(store, monkeypatch):
    """⭐⭐ **FPL's own words, passed through.** A bad id, an unreachable API and a team that has not locked
    in yet are three different problems, and a client cannot tell them apart from a bare 400. ⚠️ The fetch
    never raises — it returns `(None, message)` — so swallowing the message loses the only diagnosis there
    is."""
    monkeypatch.setattr(svc, "fetch_manager_team",
                        lambda entry_id, players: (None, "That team isn't public yet — it locks in at GW1."))
    with pytest.raises(ValueError, match="isn't public yet"):
        svc.my_team(MyTeamRequest(manager_id=123), store=store)


@pytest.mark.parametrize("request_, expected", [
    (MyTeamRequest(), "no manager id"),
    (MyTeamRequest(manager_id=0), "no manager id"),
    (MyTeamRequest(manager_id=-4), "no manager id"),
    (MyTeamRequest(manager_id=1, horizon=0), "outside 1-8"),
])
def test_my_team_requests_that_cannot_be_answered_are_refused(request_, expected):
    with pytest.raises(ValueError, match=expected):
        request_.validate()


def test_my_team_returns_over_http_what_it_returns_in_process(client, store, team, monkeypatch):
    import src.service as service

    over_http = client.post("/api/v1/squad/my-team",
                            json={"manager_id": 2885974, "horizon": 1}).json()
    in_process = service.my_team(MyTeamRequest(manager_id=2885974, horizon=1), store=store)
    assert over_http == json.loads(json.dumps(in_process))


# ---- the money FPL does publish, and the number it does not ------------------------------

def test_the_bank_comes_from_fpl_in_pounds_not_tenths(store, monkeypatch):
    """⚠️⚠️ **FPL counts money in tenths** — `bank: 13` is £1.3m. A missing division hands a manager ten
    times his money, and every affordability answer downstream is wrong while looking entirely reasonable.

    ⚠️ **What this does NOT assert, and an earlier version wrongly did:** that `cost + bank == value`. That
    is a fact about *FPL's* payload — verified once against the live API (995 and 13 against a squad this
    code prices at £98.2m) — and it cannot be checked with a fabricated fixture, because the numbers here
    are invented and the squad is a different one. ⭐ *A constructed fixture cannot confirm someone else's
    arithmetic; it only confirms what you put in it.*
    """
    from src.manager import picks_to_squad

    picks = {
        "entry_history": {"bank": 13, "value": 995},
        "active_chip": "bboost",
        "picks": [{"element": i, "position": n + 1} for n, i in enumerate(_squad(store))],
    }
    squad = picks_to_squad(picks, store.get_players(), name="RoboTS")
    assert squad["bank"] == 1.3, "13 tenths is £1.3m, not £13m"
    assert squad["value"] == 99.5
    assert squad["active_chip"] == "bboost", "a chip in play changes what the week's advice means"


def test_an_unknown_bank_is_none_and_never_zero(store):
    """⭐⭐ **None and zero are different facts.** An empty bank is a real position a manager can be in;
    *"we could not read your bank"* is not. ⚠️ Defaulting the second to the first tells the affordability
    maths every transfer is unaffordable — and it would look like a settled squad, not a bug."""
    from src.manager import picks_to_squad

    picks = {"picks": [{"element": i, "position": n + 1} for n, i in enumerate(_squad(store))]}
    squad = picks_to_squad(picks, store.get_players(), name="No history")
    assert squad["bank"] is None
    assert squad["value"] is None


def test_my_team_carries_the_money_and_the_assumption(store, team, monkeypatch):
    """⭐ Bank and value come from FPL; free transfers do not exist in any public payload, so the client
    states it and the server echoes it back. ⚠️ A header showing a number the manager never set would be
    the app inventing his position (ADR-191)."""
    monkeypatch.setattr(svc, "fetch_manager_team",
                        lambda entry_id, players: ({**team, "bank": 1.3, "value": 99.5,
                                                    "cost": 98.2, "active_chip": None}, ""))
    answer = svc.my_team(MyTeamRequest(manager_id=1, free_transfers=2), store=store)
    assert answer["squad"]["bank"] == 1.3
    assert answer["squad"]["value"] == 99.5
    assert answer["free_transfers"] == 2, "the assumption must come back, or a header cannot state it"


@pytest.mark.parametrize("free", [-1, 6])
def test_an_impossible_number_of_free_transfers_is_refused(free):
    """⚠️ FPL caps banked transfers; a client sending 99 would get a plan recommending moves nobody can
    make, and the plan would look perfectly confident."""
    with pytest.raises(ValueError, match="free transfers"):
        MyTeamRequest(manager_id=1, free_transfers=free).validate()


# ---- the plan explains itself (ADR-224) --------------------------------------------------

def test_the_plan_ships_its_own_reasoning(store):
    """⭐⭐ **A recommendation without its reasoning is a different product.** ADR-182's mantra is
    *"Analytics decide. Logic explains. You make the call"* — a screen showing only the first clause has
    quietly dropped the other two, and the owner said so on seeing the phone's bare version.
    """
    plan = svc.gameweek(GameweekRequest(player_ids=_squad(store), bank=2.0, free=1, horizon=1), store=store)
    explanation = plan["explanation"]

    assert 0 < explanation["overall"]["confidence"] <= 99
    assert explanation["overall"]["band"] in {"High", "Medium", "Low"}
    assert explanation["overall"]["reasons"], "a confidence with no reasons is a number to be trusted, not checked"
    assert "fixed" in explanation["levers"], (
        "⭐ the ceiling must be stated: a score with no limit invites chasing something that cannot move"
    )


def test_the_explanation_is_plain_data_a_client_can_read(store):
    """⚠️ `explain_gameweek` returns dataclasses. Handing those to `json.dumps` raises, and the endpoint
    would 500 on the happy path — a failure that only appears over HTTP, never in process."""
    plan = svc.gameweek(GameweekRequest(player_ids=_squad(store), horizon=1), store=store)
    assert json.loads(json.dumps(plan["explanation"])) == plan["explanation"]


def test_a_broken_explanation_never_takes_the_plan_down(store, monkeypatch):
    """⭐⭐ **Commentary must not take down the match.** The explanation is a reading of a decision already
    made; if the sentence cannot be built, the plan is still the plan. ⚠️ Without this the richest screen in
    the app is also the most fragile, and it fails for a reason that changes no recommendation."""
    from src.analytics import explain

    monkeypatch.setattr(explain, "explain_gameweek",
                        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("boom")))
    plan = svc.gameweek(GameweekRequest(player_ids=_squad(store), horizon=1), store=store)
    assert plan["explanation"] is None
    assert plan["captain"] or plan["transfers"] is not None, "the decision survives"


def test_the_explanation_describes_the_window_that_was_actually_ranked(store):
    """⚠️ **A wrong horizon here is a wrong SENTENCE, not a wrong number.** `explain_transfer` writes its
    reason as *"+2.3 to your starting XI over 1 GW"* — hard-code the window and the app states, in words, a
    span it did not rank over. ⭐ The recommendation would be right and its justification false, which is
    worse than either alone.

    Found by mutation: swapping `request.horizon` for a literal 5 passed every other test in this file.
    """
    def reason_text(horizon):
        plan = svc.gameweek(GameweekRequest(player_ids=_squad(store), bank=3.0, horizon=horizon),
                            store=store)
        transfer = (plan["explanation"] or {}).get("transfer") or {}
        return " ".join(transfer.get("reasons") or [])

    one, three = reason_text(1), reason_text(3)
    assert "1 GW" in one, f"the one-gameweek plan explains itself as: {one!r}"
    assert "3 GW" in three, f"the three-gameweek plan explains itself as: {three!r}"


# ---- a drafted squad (ADR-225) -----------------------------------------------------------

def test_a_draft_prices_a_squad_fpl_does_not_hold(store, team, monkeypatch):
    """⭐⭐ **The question the product exists for is *what if?*** — and a phone that could only ever show
    the committed team could not answer it. The draft replaces the fifteen and nothing else."""
    picked = list(team["player_ids"])
    replacement = next(p["id"] for p in store.get_players() if p["id"] not in picked)
    drafted = [replacement if i == picked[0] else i for i in picked]

    real = svc.my_team(MyTeamRequest(manager_id=1), store=store)
    draft = svc.my_team(MyTeamRequest(manager_id=1, draft_player_ids=drafted,
                                      draft_bench_ids=team["bench_ids"]), store=store)

    assert real["draft"] is False
    assert draft["draft"] is True, "the SERVER says whether this is the real team — a client can forget"
    assert replacement in [p["id"] for p in draft["analysis"]["xi"] + draft["analysis"]["bench"]]
    assert picked[0] not in [p["id"] for p in draft["analysis"]["xi"] + draft["analysis"]["bench"]]


def test_a_draft_keeps_fpls_money_and_deadline(store, team, monkeypatch):
    """⚠️ **A draft that invented its own bank would let a manager plan a move he cannot afford**, and one
    that invented its own deadline would price the wrong gameweek. Only the players change."""
    monkeypatch.setattr(svc, "fetch_manager_team",
                        lambda entry_id, players: ({**team, "bank": 2.5, "value": 101.0}, ""))
    picked = list(team["player_ids"])
    drafted = [next(p["id"] for p in store.get_players() if p["id"] not in picked)
               if i == picked[0] else i for i in picked]
    answer = svc.my_team(MyTeamRequest(manager_id=1, draft_player_ids=drafted), store=store)

    assert answer["squad"]["bank"] == 2.5
    assert answer["squad"]["name"] == team["name"]
    assert answer["deadline"]["label"]


def test_a_draft_always_reports_the_real_squad_alongside_it(store, team):
    """⭐⭐ **`fpl_player_ids` is what lets a saved plan check itself against reality** rather than trusting
    that nothing moved while the app was closed. ⚠️ Without it a client cannot tell a plan it can still act
    on from one the manager already carried out."""
    picked = list(team["player_ids"])
    drafted = [next(p["id"] for p in store.get_players() if p["id"] not in picked)
               if i == picked[0] else i for i in picked]
    answer = svc.my_team(MyTeamRequest(manager_id=1, draft_player_ids=drafted), store=store)

    assert sorted(answer["fpl_player_ids"]) == sorted(picked), (
        "the real squad must come back even when a draft is being shown"
    )


def test_a_drafted_in_player_from_a_new_club_still_gets_a_kit(store, team):
    """⚠️ Kits are keyed by club and derived from the squad being **shown**. Deriving them from the FPL
    squad would leave a new signing shirtless on the pitch — the one surface a manager checks most."""
    picked = list(team["player_ids"])
    clubs = {p["team"] for p in store.get_players() if p["id"] in set(picked)}
    incomer = next((p for p in store.get_players()
                    if p["id"] not in set(picked) and p["team"] not in clubs), None)
    if incomer is None:
        pytest.skip("this seed squad already covers every club — the case cannot arise here")

    drafted = [incomer["id"] if i == picked[0] else i for i in picked]
    answer = svc.my_team(MyTeamRequest(manager_id=1, draft_player_ids=drafted), store=store)
    assert incomer["team"] in answer["kits"]
    assert answer["fixtures"].get(incomer["team"]) is not None


@pytest.mark.parametrize("ids, expected", [
    ([1] * 15, "duplicate player ids in the draft"),
    ([1, 2, 3], "needs 15 players"),
])
def test_a_malformed_draft_is_refused(ids, expected):
    """⚠️ A draft of fourteen analyses perfectly well and simply projects less — ⭐ *a wrong answer wearing
    the shape of a right one*, which is the check this codebase keeps having to add."""
    with pytest.raises(ValueError, match=expected):
        MyTeamRequest(manager_id=1, draft_player_ids=ids).validate()


def test_a_draft_bench_must_come_from_the_draft(store):
    with pytest.raises(ValueError, match="draft bench ids not in the draft squad"):
        MyTeamRequest(manager_id=1, draft_player_ids=list(range(1, 16)),
                      draft_bench_ids=[999]).validate()


# ---- manual transfers: over budget is flagged, never hidden (ADR-226) --------------------

def test_replacements_include_players_you_cannot_afford(store):
    """⭐⭐ **The owner's call:** *"can select a higher priced player, just flag it as over budget."*

    ⚠️ Filtering would be worse than unhelpful — *a candidate silently removed looks like a candidate that
    does not exist*, so a manager concludes the player is **ineligible** when he is merely dear. And FPL
    prices drift, so a move you cannot quite afford today is a plan, not an error. `apply_transfer` has
    always treated over-budget as a soft warning; this is the same rule at the point of choosing.
    """
    picked = _squad(store)
    answer = svc.replacements(
        ReplacementsRequest(player_ids=picked, out_id=picked[0], bank=0.0, horizon=1, limit=40),
        store=store)

    assert answer["candidates"], "there is always someone who could come in"
    dear = [c for c in answer["candidates"] if not c["affordable"]]
    assert dear, "a zero bank must still surface players above the sale price"
    assert all(c["over_by"] > 0 for c in dear), "…and each must say how far over"
    assert all(c["over_by"] == 0.0 for c in answer["candidates"] if c["affordable"]), (
        "⭐ 0.0 rather than None when affordable — one type to read, and a meaningful zero"
    )


def test_the_budget_is_stated_rather_than_left_to_the_reader(store):
    """⭐ Sale price **plus** bank. A screen that showed only the bank would make a manager add two numbers
    that appear on different rows, and get it wrong the first time."""
    picked = _squad(store)
    answer = svc.replacements(
        ReplacementsRequest(player_ids=picked, out_id=picked[0], bank=1.5, horizon=1), store=store)
    assert answer["budget"] == round(answer["out"]["price"] + 1.5, 1)


def test_every_replacement_obeys_fpls_rules(store):
    """⚠️ Affordability is the *only* rule relaxed. Position, ownership, availability and the ≤3-per-club
    cap still hold — an illegal squad is not a plan, it is a squad FPL will refuse."""
    picked = _squad(store)
    by_id = {p["id"]: p for p in store.get_players()}
    out = by_id[picked[0]]
    answer = svc.replacements(
        ReplacementsRequest(player_ids=picked, out_id=out["id"], bank=50.0, horizon=1, limit=200),
        store=store)

    for c in answer["candidates"]:
        assert c["position"] == out["position"], f"{c['web_name']} is a {c['position']}"
        assert c["id"] not in set(picked), f"{c['web_name']} is already owned"
        assert c["status"] not in {"i", "s", "u"}, f"{c['web_name']} cannot play"


def test_the_club_cap_survives_the_relaxed_budget(store):
    """⭐ The ≤3-per-club rule is checked against the squad **after** the swap, which is why selling a
    same-club player frees a slot. A manual screen relaxing budget must not quietly relax this too."""
    picked = _squad(store)
    by_id = {p["id"]: p for p in store.get_players()}
    counts = {}
    for i in picked:
        counts[by_id[i]["team"]] = counts.get(by_id[i]["team"], 0) + 1
    full = [club for club, n in counts.items() if n >= 3]
    if not full:
        pytest.skip("this seed squad holds no club three times — the case cannot arise")

    out = by_id[picked[0]]
    answer = svc.replacements(
        ReplacementsRequest(player_ids=picked, out_id=out["id"], bank=50.0, horizon=1, limit=200),
        store=store)
    for c in answer["candidates"]:
        if c["team"] in full and c["team"] != out["team"]:
            pytest.fail(f"{c['web_name']} would make a 4th from {c['team']}")


@pytest.mark.parametrize("request_, expected", [
    (ReplacementsRequest(player_ids=[1, 2]), "no player to replace"),
    (ReplacementsRequest(player_ids=[1, 2], out_id=99), "not in this squad"),
    (ReplacementsRequest(player_ids=[1, 2], out_id=1, bank=-1), "bank cannot be negative"),
])
def test_a_replacement_request_that_cannot_be_answered_is_refused(request_, expected):
    """⚠️ Searching against a player you do not own returns a perfectly plausible list — ⭐ *a wrong answer
    wearing the shape of a right one.*"""
    with pytest.raises(ValueError, match=expected):
        request_.validate()


def test_a_doubtful_replacement_says_so(store):
    """⚠️⚠️ **Offering a 25%-chance player with nothing to say he is doubtful prices the doubt at
    certainty** — ADR-206's exact failure, on a new screen.

    ⭐ Found while writing these tests: `transfer.py`'s summary is the **five-key minimal** player shape
    and carries no `status`, so a candidate list built from it alone could not flag anybody. That is the
    four-player-shapes problem (start-checklist 1b) arriving in practice rather than in principle.
    """
    picked = _squad(store)
    answer = svc.replacements(
        ReplacementsRequest(player_ids=picked, out_id=picked[0], bank=50.0, horizon=1, limit=200),
        store=store)

    assert all("status" in c and "position" in c for c in answer["candidates"]), (
        "every candidate must carry enough to be judged, not just enough to be listed"
    )

    # ⚠️ **Presence is not truth, and a presence check passes against a lie.** A mutation that hard-coded
    # every status to "a" survived the assertion above — so the real doubtful player in the market has to
    # be found and followed through, ⭐ *constructing the case rather than hoping the population holds it.*
    market = {p["id"]: p for p in store.get_players()}

    # ⚠️ **Every owned player is asked, rather than one chosen and assumed legal.** A first attempt picked
    # a doubtful player and asserted he must appear — and he did not, because FPL's ≤3-per-club cap
    # legitimately blocked him. ⭐ *The test had assumed a legality it had not checked*, which is the same
    # species as the bug it was written to catch.
    seen = []
    for out_id in picked:
        listing = svc.replacements(
            ReplacementsRequest(player_ids=picked, out_id=out_id, bank=50.0, horizon=1, limit=400),
            store=store)
        seen += [c for c in listing["candidates"] if c["status"] == "d"]

    # ⚠️⚠️ **Asserted, not skipped.** A first version skipped when `seen` was empty — and the mutation that
    # hard-codes every status to "a" makes it empty, so the mutation caused the *skip* and survived.
    # ⭐ *A test that skips is not a test that passes* (ADR-178), and the population was measured before
    # this line was written: the seed market holds 24 doubtful players, 99 of whom are legal replacements
    # for somebody in a normal squad. The case is real, so its absence is a failure and not a pass.
    assert seen, (
        "no doubtful player came back flagged. The seed contains 24 of them and they are legal "
        "replacements — so either availability stopped travelling with a candidate, or the market changed "
        "beyond recognition."
    )

    for candidate in seen:
        assert candidate["status"] == "d", "a doubt must arrive flagged, never as available"
        assert candidate["chance"] == market[candidate["id"]]["chance"], (
            "⭐ a doubt is a probability — the percentage is the fact, 'doubtful' is the rounding"
        )


# ---- chips: a season decision, not a weekly one (ADR-229) --------------------------------

def test_chips_look_to_their_own_deadline_not_the_callers_horizon(store):
    """⚠️⚠️ **ADR-166, and it is the whole design.** A chip expires at the end of each half-season, so the
    question is never *"is this week good?"* but *"is this week better than the weeks I have left?"* —
    ⭐ *and that is not a smaller version of the first question, it is a different one.*

    A caller asking for one gameweek must still get the chip's own window back.
    """
    picked = _squad(store)
    answer = svc.chips(ChipsRequest(player_ids=picked, horizon=1, bank=2.0), store=store)

    assert answer["window"] > 1, "a one-gameweek request must not produce a one-gameweek chip answer"
    assert len(answer["gameweeks"]) == answer["window"]
    assert answer["expires_after"] and answer["expires_after"] >= answer["gameweeks"][-1]


def test_the_window_it_used_comes_back(store):
    """⭐ Stated because it is **not** what the caller asked for. A client rendering "next 8 gameweeks"
    over a 3-gameweek answer would be describing someone else's question."""
    answer = svc.chips(ChipsRequest(player_ids=_squad(store), horizon=5), store=store)
    assert answer["window"] == len(answer["gameweeks"])


def test_every_chip_gets_an_answer(store):
    answer = svc.chips(ChipsRequest(player_ids=_squad(store), bank=1.0), store=store)
    assert set(answer["chips"]) == {"triple_captain", "bench_boost", "free_hit", "wildcard"}


def test_the_wildcard_says_what_it_is_worth_not_only_when(store):
    """⭐⭐ ADR-185, found by the owner from a two-team A/B he was 40 points ahead in: the advisor said
    *"Wildcard GW5-7, your weakest stretch"* while his squad already overlapped an optimal rebuild by 3 of
    15. ⚠️ *A recommendation that measures only WHEN presents itself as an answer to WHETHER.*"""
    answer = svc.chips(ChipsRequest(player_ids=_squad(store), bank=2.0), store=store)
    wildcard = answer["chips"]["wildcard"]

    # ⚠️ **Named exactly, because an `or` is a hedge.** A first version read
    # `"gain" in w or "margin" in w` — and `margin` is present with or without the valuation, so the
    # assertion reduced to its always-true half and a mutation dropping `rebuild=` survived.
    # ⭐ *A hedge is not a weaker assertion, it is the absence of one* — third time this week (ADR-180).
    for field in ("gain", "overlap", "current", "rebuilt"):
        assert field in wildcard, (
            f"the wildcard is missing `{field}` — without the rebuild it answers only WHEN, and "
            f"ADR-185 exists because that presented itself as an answer to WHETHER"
        )
    assert wildcard["squad_size"] >= wildcard["overlap"], (
        "the overlap cannot exceed the squad it is an overlap with"
    )


def test_the_triple_captain_pick_is_a_player_not_a_database_row(store):
    """⚠️ It arrived as a **45-column raw row** the first time this endpoint ran — ADR-227's problem in a
    corner the shape sweep could not see, because this endpoint did not exist when the sweep was written.
    ⭐ *A guard covers the surfaces it was pointed at.*"""
    answer = svc.chips(ChipsRequest(player_ids=_squad(store)), store=store)
    pick = answer["chips"]["triple_captain"]["player"]
    assert "status" in pick and "leaving" in pick
    assert "scout_news_link" not in pick, "the database row is back"


# ---- the market (ADR-230) ----------------------------------------------------------------

def test_the_player_list_is_ranked_by_expected_points(store):
    answer = svc.players(PlayersRequest(horizon=5), store=store)
    xps = [p["xp"] for p in answer["players"]]
    assert xps == sorted(xps, reverse=True), "a browse list nobody ranked is a database table"


def test_players_who_cannot_play_are_left_out(store):
    """⭐ **Excluded, not flagged.** A browse list is for finding someone to buy, and a player who cannot
    play is not a candidate — leaving him in makes the reader do the filtering the app exists to do.

    ⚠️ **Doubtful players stay.** A doubt is a probability, not a verdict (ADR-206), and a 75% player is
    often exactly who you want.
    """
    answer = svc.players(PlayersRequest(horizon=1, limit=1000), store=store)
    statuses = {p["status"] for p in answer["players"]}
    assert not statuses & {"i", "s", "u", "n"}, f"unavailable players are listed: {statuses}"

    market = store.get_players()
    if any(p["status"] == "d" for p in market):
        assert "d" in statuses, "a doubt is a probability — doubtful players belong in the list, flagged"


def test_the_total_is_reported_separately_from_the_page(store):
    """⭐ So a client can say *"481 of 667"* rather than implying the list is everyone."""
    answer = svc.players(PlayersRequest(horizon=1, limit=10), store=store)
    assert len(answer["players"]) == 10
    assert answer["total"] > 10


def test_the_whole_market_fits_in_one_sensible_payload(store):
    """⚠️ The design depends on this: **send everyone once, filter locally**. A round trip per keystroke is
    what this avoids, and it only holds while the payload stays reasonable — spike 017 measured the board
    at ~162 KB and made payload the thing this client is designed around."""
    answer = svc.players(PlayersRequest(horizon=5), store=store)
    size = len(json.dumps(answer))
    assert size < 400_000, f"the market is {size / 1024:.0f} KB — too big to send on every visit"


@pytest.mark.parametrize("request_, expected", [
    (PlayersRequest(horizon=0), "outside 1-8"),
    (PlayersRequest(limit=0), "limit must be at least 1"),
])
def test_a_bad_market_request_is_refused(request_, expected):
    with pytest.raises(ValueError, match=expected):
        request_.validate()


# ---- feedback: the server holds the secret, and never lies about sending (ADR-231) -------

def test_an_unconfigured_sink_is_reported_not_faked(monkeypatch):
    """⭐⭐ **`relay_result` exists because a blind "sent" was a real bug** — the web form said *sent* while
    the relay silently refused, because the target address had never been activated. ⚠️ *A success message
    that cannot fail is not a success message.*

    With no webhook there is nothing to send to, and that is an outcome, not a success.
    """
    monkeypatch.delenv("FPL_FEEDBACK_WEBHOOK", raising=False)
    answer = svc.feedback(FeedbackRequest(message="the pitch looks great"))
    assert answer["sent"] is False
    assert "configured" in answer["reason"]
    # ⭐ An honest failure with a way through: the client can offer an email instead.
    assert "@" in answer["email"]


def test_the_relays_own_verdict_is_passed_through(monkeypatch):
    """⚠️ A relay can answer **HTTP 200** and still refuse — FormSubmit replies `{"success": false}` when
    the target address is unactivated. ⭐ Reporting the status code alone would call that a success."""
    import requests

    class _Refused:
        status_code = 200

        @staticmethod
        def json():
            return {"success": False, "message": "address not activated"}

    monkeypatch.setenv("FPL_FEEDBACK_WEBHOOK", "https://example.invalid/hook")
    monkeypatch.setattr(requests, "post", lambda *a, **kw: _Refused())

    answer = svc.feedback(FeedbackRequest(message="something broke"))
    assert answer["sent"] is False
    assert "not activated" in answer["reason"], "the relay's own words must survive"


def test_a_successful_relay_says_so(monkeypatch):
    import requests

    class _Accepted:
        status_code = 200

        @staticmethod
        def json():
            return {"success": "true"}

    monkeypatch.setenv("FPL_FEEDBACK_WEBHOOK", "https://example.invalid/hook")
    monkeypatch.setattr(requests, "post", lambda *a, **kw: _Accepted())
    assert svc.feedback(FeedbackRequest(message="looks good"))["sent"] is True


def test_an_unreachable_sink_does_not_raise(monkeypatch):
    """⭐ A tester reporting a bug must not hit a second one. The failure is reported and the email
    fallback comes back with it."""
    import requests

    monkeypatch.setenv("FPL_FEEDBACK_WEBHOOK", "https://example.invalid/hook")

    def _boom(*args, **kwargs):
        raise requests.ConnectionError("no route")

    monkeypatch.setattr(requests, "post", _boom)
    answer = svc.feedback(FeedbackRequest(message="offline test"))
    assert answer["sent"] is False
    assert "could not reach" in answer["reason"]


def test_the_note_reaches_the_sink_unaltered(monkeypatch):
    """⚠️ Relayed **verbatim**. A server that trimmed, reformatted or interpreted a bug report would be
    editing the evidence."""
    import requests

    sent = {}

    class _Ok:
        status_code = 200

        @staticmethod
        def json():
            return {"success": "true"}

    monkeypatch.setenv("FPL_FEEDBACK_WEBHOOK", "https://example.invalid/hook")
    monkeypatch.setattr(requests, "post",
                        lambda url, json=None, **kw: (sent.update(json or {}), _Ok())[1])

    svc.feedback(FeedbackRequest(message="  the bench order looks wrong  ", screen="My team",
                                 contact="me@example.com", version="0.0.1"))
    assert sent["message"] == "the bench order looks wrong"
    assert sent["page"] == "My team"
    assert sent["source"] == "madboots-mobile", "the owner must be able to tell a phone report from a web one"


@pytest.mark.parametrize("request_, expected", [
    (FeedbackRequest(message="   "), "no message given"),
    (FeedbackRequest(message="x" * 5000), "longer than"),
    (FeedbackRequest(message="ok", contact="x" * 300), "contact is too long"),
])
def test_a_feedback_request_that_cannot_be_relayed_is_refused(request_, expected):
    with pytest.raises(ValueError, match=expected):
        request_.validate()


# ---- signals: what should I know, about MY fifteen (ADR-232) -----------------------------

def test_signals_are_ordered_by_how_much_the_source_knows(store, monkeypatch):
    """⭐⭐ **The ordering IS the design** (ADR-150). These sources are not equally reliable, and putting
    them in one list without saying so *"would present a Reddit rumour beside an injury FPL confirmed"*.

    ⚠️ Constructed, because a seed with only one kind of signal cannot show an ordering.
    """
    picked = _squad(store)
    from src.analytics import crowd, headlines

    # A departure on one player and an exodus on another, so at least three tiers are present.
    monkeypatch.setattr(headlines, "leavers",
                        lambda owned, events, exodus_for, *, today:
                            {picked[1]: {"title": "Agreed a move", "source": "Romano"}})
    monkeypatch.setattr(crowd, "exodus_detector",
                        lambda players: (lambda p: {"net": -9000, "pressure": -9000}
                                         if p["id"] == picked[2] else None))

    answer = svc.signals(SignalsRequest(player_ids=picked, horizon=1), store=store)
    kinds = [s["kind"] for s in answer["signals"]]
    assert kinds, "the constructed signals must actually appear, or this asserts nothing"

    rank = {"official": 1, "departure": 2, "exodus": 3, "headline": 4}
    assert [rank[k] for k in kinds] == sorted(rank[k] for k in kinds), (
        f"signals are out of evidentiary order: {kinds}"
    )


def test_every_signal_says_what_kind_of_claim_it_is(store):
    """⚠️ An FPL `news` string is a **fact**; an unexplained exodus is *"the crowd knows something and we
    do not"*. ⭐ A client cannot present them differently if the server does not distinguish them."""
    answer = svc.signals(SignalsRequest(player_ids=_squad(store), horizon=1), store=store)
    for signal in answer["signals"]:
        assert signal["kind"] in {"official", "departure", "exodus", "headline"}
        assert signal["headline"], "a signal with no headline is a row with nothing in it"
        assert signal["detail"], "…and the detail is what says how much the source actually knows"


def test_every_signal_has_a_stable_key(store):
    """⭐ So a client can remember which it has already shown. ⚠️ The server cannot answer *what changed
    since I last looked* — it has no idea when that was — but it can name each thing well enough that the
    client works it out."""
    picked = _squad(store)
    first = svc.signals(SignalsRequest(player_ids=picked, horizon=1), store=store)["signals"]
    again = svc.signals(SignalsRequest(player_ids=picked, horizon=1), store=store)["signals"]

    keys = [s["key"] for s in first]
    assert len(set(keys)) == len(keys), "two signals sharing a key would mark each other as seen"
    assert keys == [s["key"] for s in again], "a key that changes between calls is not a key"


def test_the_exodus_is_bound_to_the_league_not_the_squad(store, monkeypatch):
    """⚠️ ADR-210 — a tenth of fifteen flags somebody every week."""
    seen = []
    from src.analytics import crowd
    real = crowd.exodus_detector
    monkeypatch.setattr(crowd, "exodus_detector", lambda pop: (seen.append(len(pop)), real(pop))[1])

    picked = _squad(store)
    svc.signals(SignalsRequest(player_ids=picked, horizon=1), store=store)
    assert seen and min(seen) > len(picked)


def test_a_quiet_week_is_an_answer_not_an_empty_screen(store, monkeypatch):
    """⭐ `checked` says how many players were looked at, so *nothing to report* reads as news rather than
    as a screen that failed to load."""
    from src.analytics import crowd, headlines
    monkeypatch.setattr(headlines, "leavers", lambda *a, **kw: {})
    monkeypatch.setattr(crowd, "exodus_detector", lambda players: lambda p: None)

    answer = svc.signals(SignalsRequest(player_ids=_squad(store), horizon=1), store=store)
    assert answer["checked"] == 15
