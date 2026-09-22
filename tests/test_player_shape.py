"""Every player, in every answer, is the same shape (ADR-227).

⚠️⚠️ **There were four.** `analysis` returned eleven curated keys, `transfers` five, `route.target` six,
and `build` / `route.blocked[].out` the **whole database row** — 45 columns of `cbi`,
`cost_change_event`, `scout_news_link`, shipped to a phone.

That was not untidiness:

* **It cost bytes** — `build` was 12.2 KB where 3.4 will do, on the client whose entire architecture was
  justified by measuring payload (spike 017).
* **It made the database schema part of the API contract** — rename a column and the mobile response
  changes, with nothing in between to notice.
* ⭐ **And it bit.** The five-key shape carries no `status`, so ADR-226's manual-transfer list could not
  flag a doubtful player — *a doubt hidden is a doubt priced at certainty* (ADR-206).

⭐⭐ **So this sweeps for the claim rather than checking the places I thought of** (ADR-184). A fifth shape
added later fails here, in the suite CI runs — which is the only way a rule about *every* call site stays
true.
"""

import shutil

import pytest

from src import config, service
from src.storage import Storage

#: The one shape. ⭐ A player is described by what a manager needs to judge him — not by what the database
#: happens to hold, and not by the subset one caller happened to need.
SHAPE = {
    "id", "web_name", "team", "position", "price", "xp",
    "status", "chance", "minutes_weight", "leaving", "by_gameweek",
}

#: Keys an endpoint may add because they are **answers, not raw data** — the solver decided `bench`, the
#: caller asked for `forced`, and neither exists on a player row.
ALLOWED_EXTRAS = {
    "bench", "forced",                      # the solver decided one, the caller asked for the other
    "affordable", "over_by",                # a replacement's price against *your* budget
    "opponent", "venue", "difficulty", "penalty_taker",   # facts about the fixture, not the player
}


@pytest.fixture(scope="module")
def store(tmp_path_factory):
    target = tmp_path_factory.mktemp("shape") / "shape.db"
    shutil.copy(config.SEED_DB_PATH, target)
    target.chmod(0o644)
    s = Storage(str(target))
    yield s
    s.close()


def _squad(store):
    need = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}
    picked, per_club = [], {}
    for p in store.get_players():
        if need.get(p["position"], 0) and per_club.get(p["team"], 0) < 3 and len(picked) < 15:
            picked.append(p["id"])
            need[p["position"]] -= 1
            per_club[p["team"]] = per_club.get(p["team"], 0) + 1
    return picked


def _players_in(value, path="", found=None):
    """Every object in a response that looks like a player, with where it was found.

    ⭐ Identified by `id` + `web_name` rather than by a list of known locations: a new endpoint that nests
    a player somewhere unexpected is exactly the case a hand-written list of paths would miss.
    """
    found = [] if found is None else found
    if isinstance(value, dict):
        if "id" in value and "web_name" in value:
            found.append((path or "root", value))
        for key, inner in value.items():
            _players_in(inner, f"{path}.{key}" if path else key, found)
    elif isinstance(value, list):
        for i, inner in enumerate(value[:3]):        # three is plenty; they are homogeneous
            _players_in(inner, f"{path}[{i}]", found)
    return found


#: What `_answers` exercises. ⭐ Named separately so the completeness test can read it without running
#: every endpoint, which would make a missing-coverage failure hide behind an unrelated error.
COVERED = {"analysis", "chips", "transfers", "captain", "gameweek", "route", "build",
           "replacements", "players", "signals"}


def _answers(store):
    ids = _squad(store)
    dearest = max((p for p in store.get_players() if p["id"] not in set(ids)),
                  key=lambda p: p["price"])
    return {
        "analysis": service.analysis(service.SquadRequest(player_ids=ids, horizon=1), store=store),
        "chips": service.chips(service.ChipsRequest(player_ids=ids, bank=2.0), store=store),
        "players": service.players(service.PlayersRequest(horizon=1, limit=5), store=store),
        "signals": service.signals(service.SignalsRequest(player_ids=ids, horizon=1), store=store),
        "transfers": service.transfers(
            service.TransfersRequest(player_ids=ids, horizon=1, bank=3.0), store=store),
        "captain": service.captain(service.CaptainRequest(player_ids=ids), store=store),
        "gameweek": service.gameweek(
            service.GameweekRequest(player_ids=ids, horizon=1, bank=3.0, free=1), store=store),
        "route": service.route(
            service.RouteRequest(player_ids=ids, target_id=dearest["id"], bank=0.0), store=store),
        "build": service.build(service.BuildRequest(budget=100.0, horizon=1), store=store),
        "replacements": service.replacements(
            service.ReplacementsRequest(player_ids=ids, out_id=ids[0], bank=2.0, horizon=1),
            store=store),
    }


#: Functions whose answers contain no players, so the sweep has nothing to check in them.
NO_PLAYERS = {
    "my_team",      # composes `analysis`, which is swept in its own right
    "feedback",     # relays a tester's note; there is no player in it
}


def test_the_sweep_covers_every_endpoint():
    """⚠️⚠️ **A guard covers the surfaces it was pointed at.** The chips endpoint was written after this
    sweep and immediately shipped a raw 45-column database row as its triple-captain pick — the exact thing
    the sweep exists to prevent, in a corner it could not see.

    ⭐ *A guard that requires manual registration is a guard that will be forgotten*, so this fails when a
    public service function is not exercised above. It cannot build the request for you — every endpoint
    takes a different DTO — but it can refuse to let you forget.
    """
    public = {
        name for name in service.__all__
        if callable(getattr(service, name)) and not name.endswith("Request")
    }
    swept = set(_answers.__annotations__.get("covers", ())) or COVERED
    missing = public - swept - NO_PLAYERS
    assert not missing, (
        f"{sorted(missing)} are service endpoints that this sweep never calls. Add them to `_answers()` "
        f"(and to COVERED), or to NO_PLAYERS with a reason."
    )


def test_the_sweep_actually_finds_players():
    """⭐ A sweep that finds nothing passes. If the detector stops matching, every assertion below becomes
    vacuously true and the guard is gone with no test going red."""
    sample = {"xi": [{"id": 1, "web_name": "A"}], "nested": {"out": {"id": 2, "web_name": "B"}}}
    assert len(_players_in(sample)) == 2


def test_every_answer_describes_a_player_the_same_way(store):
    """⚠️ **Not "has at least these keys" — exactly these keys.** A superset is how the database row crept
    back in last time: every assertion about the curated fields passed while 34 extra columns rode along."""
    wrong = []
    for endpoint, answer in _answers(store).items():
        for path, player in _players_in(answer):
            extra = set(player) - SHAPE - ALLOWED_EXTRAS
            missing = SHAPE - set(player)
            if extra or missing:
                wrong.append(f"{endpoint}.{path}: missing {sorted(missing)}, unexpected {sorted(extra)}")

    assert not wrong, (
        "these players are not the shared shape:\n  " + "\n  ".join(wrong)
        + "\n\n⭐ Build them with `player_summary()`. A new field belongs in SHAPE, not in one endpoint."
    )


def test_a_doubtful_player_can_be_flagged_from_any_answer(store):
    """⭐⭐ **The concrete reason this matters.** ADR-226's manual list could not flag a doubt because the
    shape it used carried no `status` — and a doubt hidden is a doubt priced at certainty (ADR-206).
    Every answer must now carry enough to judge a player, not merely enough to name him."""
    for endpoint, answer in _answers(store).items():
        for path, player in _players_in(answer):
            assert "status" in player, f"{endpoint}.{path} cannot say whether he can play"
            assert "chance" in player, f"{endpoint}.{path} cannot say how likely he is to"
            assert "leaving" in player, f"{endpoint}.{path} cannot say he has agreed a move"
