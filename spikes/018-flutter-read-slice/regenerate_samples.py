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
        "build": service.build(
            service.BuildRequest(budget=100.0, horizon=5), store=store),
    }


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
