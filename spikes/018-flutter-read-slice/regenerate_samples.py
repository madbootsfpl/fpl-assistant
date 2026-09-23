"""Write one real response per endpoint, for a Dart author to write models against.

⭐ **Why samples exist at all.** The mobile audit §5 planned to *generate* the client's models from the
OpenAPI schema — *"one contract, no hand-written duplicates."* That does not work today: every route is
typed `-> dict`, so the schema advertises each response as an untyped object and a generator would emit
`Map<String, dynamic>`. Until responses are typed — an open decision, see
`docs/03_Architecture/Flutter_Start_Checklist.md` — a model author needs the real
payload, and guessing it from `answers.py` is how a client and a server start to disagree.

⚠️ **These are a convenience, and `tests/test_api_contract.py` is the guard.** That test regenerates the
*shape* — keys and types, never values — and fails if it moved. Samples nobody checks are worse than no
samples, because they look authoritative.

Run: `venv/bin/python spikes/018-flutter-read-slice/regenerate_samples.py`
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from src import service  # noqa: E402
from src.storage import Storage  # noqa: E402

HERE = pathlib.Path(__file__).parent / "api-samples"


def legal_squad(store, size=15):
    """The FPL position split, at most three per club — a squad the engine will accept."""
    need = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}
    picked, per_club = [], {}
    for p in store.get_players():
        if need.get(p["position"], 0) and per_club.get(p["team"], 0) < 3 and len(picked) < size:
            picked.append(p["id"])
            need[p["position"]] -= 1
            per_club[p["team"]] = per_club.get(p["team"], 0) + 1
    return picked


def responses(store) -> dict:
    """One answer per endpoint, from the same squad, so a reader can follow a player across them."""
    ids = legal_squad(store)
    target = max((p for p in store.get_players() if p["id"] not in set(ids)),
                 key=lambda p: p["price"])["id"]
    return {
        "analysis": service.analysis(
            service.SquadRequest(player_ids=ids, horizon=5), store=store),
        "transfers": service.transfers(
            service.TransfersRequest(player_ids=ids, horizon=1, bank=2.0, count=1), store=store),
        "captain": service.captain(
            service.CaptainRequest(player_ids=ids, limit=3), store=store),
        "gameweek-plan": service.gameweek(
            service.GameweekRequest(player_ids=ids, horizon=1, bank=2.0, free=1), store=store),
        "route": service.route(
            service.RouteRequest(player_ids=ids, target_id=target, bank=2.0), store=store),
        # ⚠️ **With `bench_weight`, because that is what the Lab asks for** (ADR-268). A sample built
        # without it designates no bench at all, so ⭐ *the shape a client has to render would be absent
        # from the only example it has.*
        "build": service.build(
            service.BuildRequest(budget=100.0, horizon=5, bench_weight=0.1), store=store),
        # ⚠️ **The FPL fetch is stubbed, and it has to be.** `my_team` calls FPL over the network for a
        # manager's picks; a sample regenerated from the internet is not reproducible, and the contract test
        # that compares against it would pass or fail on someone else's uptime. ⭐ The *composition* is what
        # the sample documents — the fetch has its own coverage.
        "my-team": _my_team(store, ids),
        # ⭐ The whole ranked board, because that is literally what the endpoint returns and the app
        # downloads it in one go (ADR-236). A trimmed sample would hide the only thing worth knowing
        # about this response — its size.
        "players": service.players(service.PlayersRequest(horizon=5), store=store),
        # ⭐ The expanding card's own response. Added when a widget test needed to expand a row and had
        # nothing real to expand it with — ⚠️ *a hand-built card fixture would have tested the fixture.*
        "player": service.player(service.PlayerRequest(player_id=ids[0], horizon=5), store=store),
        # ⭐ The crowd's boards (ADR-266). ⚠️ `by="in"` because the *most bought* board is the one the
        # tab opens on, and a sample of the board nobody sees first documents the wrong default.
        "trending": service.trending(service.TrendingRequest(by="in", limit=15), store=store),
        # ⭐ The fixture ticker — twenty clubs, six gameweeks (ADR-265). ⚠️ Worth a sample even though it
        # takes no squad: the shape a client has to survive is the **blank cell**, and a hand-built
        # fixture would be one somebody wrote rather than one the server produces.
        "ticker": service.ticker(service.TickerRequest(next_n=6), store=store),
        # ⭐ Boot Battle's own response, so a widget test can render the real thing (ADR-258).
        "compare": _compare_pair(store, ids),
        # ⚠️⚠️ **Stubbed, and it has to be** — these three call FPL over the network, and a sample
        # regenerated from the internet is not reproducible: the contract test comparing against it would
        # pass or fail on somebody else's uptime, and on whichever gameweek happened to be live. ⭐ The
        # *composition* is what the sample documents; the fetch has its own coverage.
        "leagues": _leagues(),
        "league": _league(store, ids),
        "h2h": _h2h(store, ids),
    }


class _CannedFpl:
    """An FPL client that answers from fixtures. ⭐ Shaped like the real payloads, **not** like our own
    answers — ⚠️ *a stub shaped like the output cannot catch a mistake in the code that produces it.*"""

    def __init__(self, entries, picks):
        self._entries, self._picks = entries, picks

    def get_entry(self, entry_id):
        return {
            "player_first_name": "Sample", "player_last_name": "Manager",
            "leagues": {"classic": [
                {"id": 4021, "name": "A League of Our Own", "rank_count": 12,
                 "entry_rank": 3, "league_type": "x"},
                {"id": 314, "name": "Overall", "rank_count": 10833601,
                 "entry_rank": 482347, "league_type": "s"},
            ]},
        }

    def get_league_standings(self, league_id, page=1):
        return {
            "league": {"name": "A League of Our Own"},
            "standings": {"has_next": False, "results": [
                {"entry": e, "player_name": f"Manager {i + 1}", "entry_name": f"Team {i + 1}",
                 "rank": i + 1, "last_rank": i + 2 if i else 0,
                 "event_total": 60 - i, "total": 400 - 10 * i}
                for i, e in enumerate(self._entries)
            ]},
        }

    def get_entry_picks(self, entry_id, gameweek):
        return self._picks[entry_id]


def _canned_picks(ids, captain, vice):
    """One manager's picks payload, in FPL's own shape."""
    return {"picks": [
        {"element": pid, "position": i + 1,
         "multiplier": 2 if pid == captain else (0 if i >= 11 else 1),
         "is_captain": pid == captain, "is_vice_captain": pid == vice}
        for i, pid in enumerate(ids)
    ], "active_chip": None}


def _with_canned(client, fn):
    """Run `fn` with the FPL client replaced — ⚠️ restored in a `finally`, because a leaked stub would
    silently make every later sample fictional."""
    from src.api import client as api_client
    real = api_client.FplClient
    api_client.FplClient = lambda *a, **k: client
    try:
        return fn()
    finally:
        api_client.FplClient = real


def _leagues():
    return _with_canned(
        _CannedFpl([], {}),
        lambda: service.leagues(service.LeaguesRequest(manager_id=1)))


def _league(store, ids):
    entries = [101, 102, 103]
    picks = {
        101: _canned_picks(ids, ids[0], ids[1]),
        102: _canned_picks(ids, ids[0], ids[2]),
        103: _canned_picks(ids, ids[3], ids[1]),
    }
    return _with_canned(
        _CannedFpl(entries, picks),
        lambda: service.league(
            service.LeagueRequest(league_id=4021, manager_id=101, gameweek=5,
                                  with_captains=True, limit=20),
            store=store))


def _h2h(store, ids):
    """⚠️ The two squads **differ**, or the sample would document the one case the screen never shows —
    ⭐ *a fixture where both sides are identical makes every differential row disappear.*"""
    others = [p["id"] for p in store.get_players() if p["id"] not in set(ids)][:15]
    mine = _canned_picks(ids, ids[0], ids[1])
    theirs = _canned_picks(ids[:8] + others[:7], others[0], ids[1])
    return _with_canned(
        _CannedFpl([1, 2], {1: mine, 2: theirs}),
        lambda: service.head_to_head(
            service.HeadToHeadRequest(manager_id=1, rival_id=2, horizon=1), store=store))


def _compare_pair(store, ids):
    """Two same-position players from the sample squad — ⚠️ `compare` refuses a cross-position pairing."""
    by_id = {p["id"]: p for p in store.get_players()}
    same = [i for i in ids if by_id[i]["position"] == by_id[ids[0]]["position"]]
    return service.compare(
        service.CompareRequest(a_id=same[0], b_id=same[1], horizon=5), store=store)


def _my_team(store, ids):
    """`my_team` over a fixed squad, so the sample is the same every time it is written."""
    from src.service import answers

    squad = {"name": "Sample XI", "player_ids": ids, "bench_ids": ids[-4:],
             "captain_id": ids[0], "vice_captain_id": ids[1]}
    real = answers.fetch_manager_team
    answers.fetch_manager_team = lambda entry_id, players: (squad, "")
    try:
        return service.my_team(service.MyTeamRequest(manager_id=1, horizon=1), store=store)
    finally:
        answers.fetch_manager_team = real


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    store = Storage()
    try:
        for name, answer in responses(store).items():
            path = HERE / f"{name}.json"
            # ⚠️ Dumped through JSON exactly as the HTTP layer would, so what a Dart author reads is what
            # the wire carries — integer gameweek keys included, which become strings here and only here.
            path.write_text(json.dumps(json.loads(json.dumps(answer)), indent=2, sort_keys=True) + "\n")
            print(f"  {path.name:20} {path.stat().st_size / 1024:6.1f} KB")
    finally:
        store.close()


if __name__ == "__main__":
    main()
