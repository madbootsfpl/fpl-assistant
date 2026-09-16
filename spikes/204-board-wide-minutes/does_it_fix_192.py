"""Does the blend solve ADR-192's complaint better than ADR-192's own proposal?

ADR-192 proposed demoting players with **no past seasons**. ADR-202 measured that and declined it: rho
declines at every value, and the one real harm (a no-history player in a top-20 recommendation, who scored 0)
was n = 1.

The blend targets a different thing — **low observed minutes this season**, whatever the player's history.
⭐ *That is a better-aimed instrument for the same complaint*: it catches the fringe player who is not
playing, and spares the new signing who is nailed on. Affengruber had no career and had just played 90;
ADR-192's rule demotes him, the blend does not.

So: what happens to the top 20?
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import statistics  # noqa: E402

from blend import blended_factory  # noqa: E402

from src.analytics import backtest  # noqa: E402
from src.analytics import xp as xp_mod
from src.storage import Storage  # noqa: E402

TOP = 20


def main():
    store = Storage()
    gw_history = store.get_gw_history_by_code()
    players = store.get_players()
    history = store.get_history_by_code()
    code_by_id = store.get_player_codes()
    fixtures: dict[int, list] = {}
    real_factory = xp_mod.minutes_weight_from_history
    cold = {p["code"] for p in players if not history.get(p["code"])}

    def top20(k, before, n):
        upcoming = fixtures.setdefault(n, store.get_fixtures_by_event(n))
        if k is not None:
            xp_mod.minutes_weight_from_history = lambda h, gw=None, _k=k: blended_factory(_k, h, gw)
        try:
            ranked = xp_mod.decision_xp(players, upcoming, history, horizon=1, gw_history_by_code=before)
        finally:
            xp_mod.minutes_weight_from_history = real_factory
        rows = [(code_by_id[r["id"]], r["xp"]) for r in ranked if r["id"] in code_by_id]
        return [c for c, _ in sorted(rows, key=lambda t: -t[1])[:TOP]]

    print(f"  {'weight':<22} {'cold in top20':>14} {'top20 mean pts':>16} {'top20 zero-scorers':>20}")
    for k, label in ((None, "xMins v0 (the app)"), (1, "blend, k=1")):
        n_cold, pts = 0, []
        for rnd in backtest.rounds_with_actuals(gw_history):
            before = {c: [r for r in rows if r["round"] < rnd] for c, rows in gw_history.items()}
            for code in top20(k, before, rnd):
                actual = next((r["total_points"] for r in (gw_history.get(code) or [])
                               if r["round"] == rnd and r["total_points"] is not None), None)
                if actual is None:
                    continue
                pts.append(actual)
                n_cold += code in cold
        zeros = sum(1 for p in pts if p <= 0)
        print(f"  {label:<22} {n_cold:>14} {statistics.mean(pts):>16.2f} "
              f"{f'{zeros} of {len(pts)}':>20}")
    store.close()


if __name__ == "__main__":
    main()
