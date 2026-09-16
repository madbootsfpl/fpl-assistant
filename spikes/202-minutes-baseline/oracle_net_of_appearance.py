"""How much of the oracle's headroom is information, and how much is arithmetic?

`oracle_bound.py` put perfect minutes at **+0.206 rho (5.1 SE)** over the live model. ⚠️ **That number is
inflated and cannot be quoted as headroom**, because minutes *are* part of the score: FPL pays 1 appearance
point for 1-59 minutes and 2 for 60+. For every player who returns nothing else — a large share of the board —
knowing his minutes exactly determines his total exactly. ⭐ *An oracle over an input that is also a component
of the output is partly grading its own arithmetic.*

So this re-scores everything against **points net of appearance points**: goals, assists, clean sheets, bonus,
cards — the part of a score that minutes can only ever *inform*. The gap that survives is the real ceiling on
Phase 1.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analytics import backtest  # noqa: E402
from src.analytics import xp as xp_mod
from src.storage import Storage  # noqa: E402

FULL_GAME = 90


def appearance_points(minutes):
    """FPL's own rule: 0 for an unused sub, 1 up to 59 minutes, 2 from 60."""
    m = minutes or 0
    return 0 if m == 0 else (1 if m < 60 else 2)


def main():
    store = Storage()
    gw_history = store.get_gw_history_by_code()
    players = store.get_players()
    history = store.get_history_by_code()
    code_by_id = store.get_player_codes()
    fixtures: dict[int, list] = {}
    real_factory = xp_mod.minutes_weight_from_history

    def ranked_at(kind, before, n):
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
        try:
            out = xp_mod.decision_xp(players, upcoming, history, horizon=1,
                                     minutes_weighted=(kind != "none"), gw_history_by_code=before)
        finally:
            xp_mod.minutes_weight_from_history = real_factory
        return {code_by_id[r["id"]]: r["xp"] for r in out if r["id"] in code_by_id}

    rounds = backtest.rounds_with_actuals(gw_history)
    print(f"  {'weight':<28} {'rho vs TOTAL':>13} {'rho vs NET':>11}   per-round rho (net)")
    got = {}
    for kind, label in (("none", "none  (--no-xmins)"),
                        ("live", "xMins v0  (the app today)"),
                        ("oracle", "ORACLE  (actual minutes)")):
        tot, net = [], []
        for n in rounds:
            before = {c: [r for r in rows if r["round"] < n] for c, rows in gw_history.items()}
            preds = ranked_at(kind, before, n)
            for code, rows in gw_history.items():
                row = next((r for r in rows if r["round"] == n and r["total_points"] is not None), None)
                if row is None or code not in preds:
                    continue
                tot.append((preds[code], row["total_points"], n))
                net.append((preds[code], row["total_points"] - appearance_points(row["minutes"]), n))
        cells = " ".join(
            f"{backtest.spearman([p for p, a, r in net if r == rr], [a for p, a, r in net if r == rr]):>7.3f}"
            for rr in rounds)
        got[kind] = (backtest.mean_gw_spearman(tot), backtest.mean_gw_spearman(net))
        print(f"  {label:<28} {got[kind][0]:>13.3f} {got[kind][1]:>11.3f}   {cells}")

    se = backtest.spearman_se(len([1 for _ in range(len(rounds))]) and
                              backtest.eligible_n(backtest.pairs(gw_history, lambda b, n: ranked_at("live", b, n))))
    print(f"\n  1 SE = {se:.3f}")
    for a, b, what in (("none", "live", "having a weight at all"), ("live", "oracle", "PERFECT minutes from here")):
        dt, dn = got[b][0] - got[a][0], got[b][1] - got[a][1]
        print(f"  {what:<26} total {dt:+.3f} ({dt/se:.1f} SE)   net of appearance {dn:+.3f} ({dn/se:.1f} SE)")
    store.close()


if __name__ == "__main__":
    main()
