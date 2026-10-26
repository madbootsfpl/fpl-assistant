"""Why does fixing a real ratchet buy +0.18 SE? Who does the looser guard actually move, and to where?

`rolling.py` confirmed ADR-320's premise (refusals climb 49% -> 78%, GW2 -> GW8). `rolling_on_points.py`
found the fix is worth +0.18 SE against a +1 SE bar. ⭐ *Both of those can be true, and the gap between
them is the thing worth understanding* — so this names the players and reads where in the board they sit.

Run 3 of 3.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rolling import rolling_share  # noqa: E402

from src.analytics import xp as xp_mod  # noqa: E402
from src.analytics.minutes import (  # noqa: E402
    completed_gameweeks,
    expected_minutes,
    in_season_share,
    minutes_weight_from_history,
)
from src.storage import Storage  # noqa: E402

WINDOW, TOLERANCE = 5, 1


def main():
    db = Storage()
    players = db.get_players()
    gw_hist = db.get_gw_history_by_code()
    hist = db.get_history_by_code()
    by_code = {p["code"]: p for p in players}
    completed = completed_gameweeks(gw_hist)
    live_w = minutes_weight_from_history(hist, gw_hist)

    rescued = []
    for p in players:
        if not (gw_hist.get(p["code"]) or []):
            continue
        if in_season_share(p, gw_hist, completed) is not None:
            continue
        share = rolling_share(p, gw_hist, completed, WINDOW, TOLERANCE)
        if share is None:
            continue
        rescued.append((p, expected_minutes(live_w(p)), expected_minutes(share * 1.0)))

    print(f"RESCUED at GW{max(completed)} by 'last {WINDOW}, forgive {TOLERANCE}': {len(rescued)} players "
          f"of {len([p for p in players if gw_hist.get(p['code'])])} with rows\n")

    # Where do they sit? The ranking is the thing being scored, and a change confined to the bottom of
    # the board cannot move hit@20 however many players it touches (ADR-204's top-of-board finding).
    upcoming = db.get_fixtures_by_event(max(completed) + 1)
    ranked = xp_mod.decision_xp(players, upcoming, hist, horizon=1, gw_history_by_code=gw_hist)
    rank_of = {r["id"]: i + 1 for i, r in enumerate(ranked)}
    xp_of = {r["id"]: r["xp"] for r in ranked}

    rows = sorted(rescued, key=lambda t: rank_of.get(t[0]["id"], 10**6))
    print(f"  {'player':<22} {'rank':>6} {'xP':>6} {'xMins now':>10} {'xMins after':>12}  {'last 5 mins':>14}")
    for p, now, after in rows[:15]:
        recent = {r["round"]: (r["minutes"] or 0) for r in (gw_hist.get(p["code"]) or [])}
        tail = ",".join(str(recent.get(g, 0)) for g in sorted(completed)[-WINDOW:])
        print(f"  {p['web_name'][:22]:<22} {rank_of.get(p['id'], 0):>6} {xp_of.get(p['id'], 0):>6.2f} "
              f"{now:>10} {after:>12}  {tail:>14}")

    in_top = [p for p, _, _ in rescued if rank_of.get(p["id"], 10**6) <= 20]
    in_100 = [p for p, _, _ in rescued if rank_of.get(p["id"], 10**6) <= 100]
    print(f"\n  of the {len(rescued)} rescued: {len(in_top)} are in the top 20, {len(in_100)} in the top 100")
    print("  ⭐ that ratio is the whole answer — a correction confined to the bottom of the board is a")
    print("     correction the ranking metric cannot see, and the top 20 is the only part a pick reads.")

    # The two players ADR-320 named, checked rather than carried over.
    print()
    for name in ("Onyeka", "Konsa"):
        p = next((q for q in players if name.lower() in (q["web_name"] or "").lower()), None)
        if p is None:
            print(f"  {name}: not in the player table")
            continue
        share = rolling_share(p, gw_hist, completed, WINDOW, TOLERANCE)
        recent = {r["round"]: (r["minutes"] or 0) for r in (gw_hist.get(p["code"]) or [])}
        tail = ",".join(str(recent.get(g, 0)) for g in sorted(completed)[-WINDOW:])
        print(f"  ADR-320 named {name}: xMins {expected_minutes(live_w(p))} -> "
              f"{'refused too' if share is None else expected_minutes(share)}   last {WINDOW}: {tail}   "
              f"rank {rank_of.get(p['id'], 0)}")
    db.close()


if __name__ == "__main__":
    main()
