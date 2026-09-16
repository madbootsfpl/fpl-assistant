"""The ceiling on Phase 1: what does PERFECT minutes knowledge buy the points ranking?

⚠️ **This deliberately leaks, and that is the point.** It weights every player by the minutes he *actually*
played in the round being predicted. No model can ever do better than that. So the ρ it reaches is a **hard
upper bound on everything the ML roadmap's Phase 1 could deliver** — not an estimate of it.

Why it was needed: the first premise test swapped in "last GW's minutes", which is 15% more accurate than the
live model **on owned players** but a dead heat board-wide (MAE 24.6 vs 24.5) — and the ranking is board-wide.
⭐ *A substitute that is not actually better on the population being ranked cannot test whether better helps.*
An oracle has no such problem: it is better everywhere, by construction.

Read it as: **the whole of Phase 1 is worth at most (oracle − live).** If that gap is under §B0's +1 SE bar,
a learned minutes model cannot clear the bar however good it is, and the roadmap should say so.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analytics import backtest  # noqa: E402
from src.analytics import xp as xp_mod
from src.storage import Storage  # noqa: E402

FULL_GAME = 90


def main():
    store = Storage()
    gw_history = store.get_gw_history_by_code()
    players = store.get_players()
    history = store.get_history_by_code()
    code_by_id = store.get_player_codes()
    fixtures: dict[int, list] = {}
    real_factory = xp_mod.minutes_weight_from_history

    def predict(kind, target_round):
        def inner(before, n):
            upcoming = fixtures.setdefault(n, store.get_fixtures_by_event(n))
            if kind == "oracle":
                actual = {code: next((r["minutes"] or 0 for r in rows if r["round"] == n), None)
                          for code, rows in gw_history.items()}

                def factory(history_by_code, gw_history_by_code=None):
                    def weight(player):
                        m = actual.get(player["code"])
                        return 1.0 if m is None else min(1.0, m / FULL_GAME)
                    return weight
                xp_mod.minutes_weight_from_history = factory
            elif kind == "none":
                xp_mod.minutes_weight_from_history = real_factory
            try:
                ranked = xp_mod.decision_xp(
                    players, upcoming, history, horizon=1,
                    minutes_weighted=(kind != "none"), gw_history_by_code=before)
            finally:
                xp_mod.minutes_weight_from_history = real_factory
            return {code_by_id[r["id"]]: r["xp"] for r in ranked if r["id"] in code_by_id}
        return inner

    rounds = backtest.rounds_with_actuals(gw_history)
    print(f"  {'weight':<28} {'rho (mean GW)':>14} {'MAE':>7} {'hit@20':>8}   per-round rho")
    got = {}
    for kind, label in (("none", "none  (--no-xmins, = always 90)"),
                        ("live", "xMins v0  (the app today)"),
                        ("oracle", "ORACLE  (actual minutes)")):
        triples = backtest.pairs(gw_history, predict(kind, None))
        by_gw = {}
        for pred, actual, rnd in triples:
            by_gw.setdefault(rnd, []).append((pred, actual))
        cells = " ".join(
            f"{backtest.spearman([p for p, _ in by_gw[r]], [a for _, a in by_gw[r]]):>7.3f}" for r in rounds)
        rho = backtest.mean_gw_spearman(triples)
        got[kind] = rho
        print(f"  {label:<28} {rho:>14.3f} {backtest.mae(triples):>7.2f} "
              f"{backtest.hit_rate(triples, 20):>8.2f}   {cells}")

    se = backtest.spearman_se(backtest.eligible_n(backtest.pairs(gw_history, predict("live", None))))
    print(f"\n  1 SE = {se:.3f}   (§B0's bar is a gain of +1 SE)")
    print(f"  having a weight at all   : {got['live'] - got['none']:+.3f}  = {(got['live']-got['none'])/se:.1f} SE")
    print(f"  PERFECT minutes from here: {got['oracle'] - got['live']:+.3f}  = {(got['oracle']-got['live'])/se:.1f} SE"
          "   <-- the hard ceiling on Phase 1")
    store.close()


if __name__ == "__main__":
    main()
