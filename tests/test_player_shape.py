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

import pathlib
import shutil
import sys

import pytest

from src import config, service
from src.storage import Storage

# ⚠️ The league endpoints call FPL over the network. ⭐ Reusing the sample generator's **canned client**
# rather than writing a second one: *two stubs of one upstream drift apart*, and this sweep is exactly the
# place a drifted stub would hide a raw row.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent
                       / "spikes" / "018-flutter-read-slice"))

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
    "recent",                               # a comparison's last-five form: an answer, not a stored field
    # ⚠️⚠️ **`photo` is deliberately NOT in `SHAPE`, and that is the whole point of it being here.**
    #
    # It is derived (a URL from the player's `code`), so it is an answer rather than a stored field — but
    # the real reason it cannot join the shared shape is ADR-084: the **pitch** must show the club kit,
    # never the mugshot, because FPL's photo CDN lags a transfer by weeks while the kit updates instantly.
    # Putting `photo` in `SHAPE` would put a face on every XI card's payload and invite one onto the pitch.
    #
    # ⭐ So it appears only where a **name already is** — Boot Battle's two sides here, and as a top-level
    # sibling on `player` and `player_dna`. *An allowlist entry is a decision; this one is ADR-255's.*
    "photo",
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
COVERED = {"analysis", "trending", "league", "gameweek_result", "head_to_head", "chips", "compare", "transfers", "captain", "gameweek", "route", "build",
           "replacements", "players", "player", "player_dna", "signals", "chatter"}


class _FakeReddit:
    """An RSS feed naming real players, so the sweep sees real rows."""

    def __init__(self, store):
        names = [p["web_name"] for p in store.get_players()
                 if len(p["web_name"]) > 5 and p["web_name"].isalpha()][:3]
        entries = "".join(
            f"<entry><title>{n} thread</title><content>{n} {n}</content>"
            f'<link href="https://reddit.com/{i}"/></entry>'
            for i, n in enumerate(names)
        )
        self._xml = ('<?xml version="1.0" encoding="UTF-8"?>'
                     '<feed xmlns="http://www.w3.org/2005/Atom">' + entries + "</feed>")

    def get_subreddit_rss(self) -> str:
        return self._xml


def _compare_two(store):
    """Two same-position players, whoever they are — the sweep cares about shape, not who wins."""
    mids = [p for p in store.get_players() if p["position"] == "MID"][:2]
    return service.compare(
        service.CompareRequest(a_id=mids[0]["id"], b_id=mids[1]["id"], horizon=1), store=store)


def _league(store, ids):
    from regenerate_samples import _league as build
    return build(store, ids)


def _h2h(store, ids):
    from regenerate_samples import _h2h as build
    return build(store, ids)


def _gameweek_result(store, ids):
    """A played gameweek, stubbed at the FPL boundary like `_league` and `_h2h`.

    ⭐ In the sweep proper, not in NO_PLAYERS: **a past week comes with its player**, and the first
    version of this endpoint invented a flat `{web_name, points}` dict — a second player shape, caught
    here within minutes of being written. ⚠️ *The guard's value is that it refuses a new shape at the
    moment it is cheapest to change.*
    """
    from src.api import client as fpl_client

    class _Canned:
        def get_entry_picks(self, entry_id, gameweek):
            return {
                "active_chip": None,
                "automatic_subs": [],
                "entry_history": {"points": 50, "overall_rank": 1, "rank": 1,
                                  "event_transfers": 0, "event_transfers_cost": 0,
                                  "points_on_bench": 0},
                "picks": [{"element": e, "position": n + 1, "multiplier": 1,
                           "is_captain": False, "is_vice_captain": False}
                          for n, e in enumerate(ids)],
            }

    real = fpl_client.FplClient
    fpl_client.FplClient = lambda *a, **k: _Canned()
    try:
        return service.gameweek_result(
            service.GameweekResultRequest(manager_id=1, gameweek=1), store=store)
    finally:
        fpl_client.FplClient = real


def _answers(store):
    ids = _squad(store)
    dearest = max((p for p in store.get_players() if p["id"] not in set(ids)),
                  key=lambda p: p["price"])
    return {
        "analysis": service.analysis(service.SquadRequest(player_ids=ids, horizon=1), store=store),
        # ⭐ Chatter carries a summary per talked-about player. ⚠️ **Stubbed at the Reddit boundary** — a
        # sweep that needed the live subreddit would be a sweep that goes red when somebody else's site
        # is slow.
        "chatter": service.chatter(service.ChatterRequest(player_ids=ids, limit=5),
                                   store=store, client=_FakeReddit(store)),
        "chips": service.chips(service.ChipsRequest(player_ids=ids, bank=2.0), store=store),
        "players": service.players(service.PlayersRequest(horizon=1, limit=5), store=store),
        # ⭐ In the sweep proper: a crowd board carries a **player summary** per row, which is exactly the
        # shape a raw 45-column database row leaks through (ADR-227's original defect).
        "trending": service.trending(service.TrendingRequest(by="in", limit=5), store=store),
        # ⭐ A league's captain split carries a summary per captained player, and the head-to-head carries
        # a row per differential. ⚠️ Both are **stubbed at the FPL boundary**, because a sweep that needed
        # the internet would be a sweep somebody eventually deletes.
        "league": _league(store, ids),
        "gameweek_result": _gameweek_result(store, ids),
        "head_to_head": _h2h(store, ids),
        "compare": _compare_two(store),
        "player": service.player(
            service.PlayerRequest(player_id=ids[0], horizon=1), store=store),
        # ⭐ In the sweep proper, not in NO_PLAYERS: a fingerprint comes **with its player**, and that
        # summary is exactly the kind of field a raw database row leaks through.
        "player_dna": service.player_dna(
            service.PlayerDnaRequest(player_id=ids[0], horizon=1), store=store),
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
    # ⚠️ Answers about **clubs**, not players — twenty fingerprints, no player row anywhere in it. Its own
    # shape is guarded by `test_team_dna_endpoint.py`. ⭐ *"Nothing to check here" has to be written down,
    # or the next reader cannot tell it from "nobody checked".*
    "team_dna",
    # ⚠️ The **league's fixtures**, not anyone's players — a clubs × gameweeks grid whose cells hold an
    # opponent's short name, never a player row. Its own shape is guarded in `test_service_endpoints.py`
    # (blank cells present, keys stringified, a double shaded by its harder half).
    "ticker",
    # ⚠️ A list of **leagues** — an id, a name, a size and a rank. There is no player in it at all; the
    # league that carries players is `league`, which is swept above.
    "leagues",
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
