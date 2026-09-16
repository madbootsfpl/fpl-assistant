"""Team defence for DEF/GK — measured as **xGC per 90**, not clean-sheet rate (ADR-188, third attempt).

ADR-188 asked the right question and used the wrong instrument. It tested a club's **clean-sheet rate**: over
four gameweeks that is a five-valued statistic derived from a coin flip, so its variance swamps its signal. It
returned a null twice (whole board, then DEF/GK only per ADR-190) and the weight stayed at 0.

The owner kept disagreeing, on a specific and checkable basis:

    ARS  0.65 xGC/90  — rank  1 of 20        the model rates Konsa (ARS) and Thomas (COV)
    COV  1.94 xGC/90  — rank 19 of 20        within 0.1 xP of each other

**xGC per 90 is continuous and the spread is 3×.** That is a different quantity, not a re-run of a failed
measurement — which is the only thing that justifies a third attempt.

Scored on the population the term applies to **and** the whole board, per ADR-190's Option 3.

    venv/bin/python spikes/195-team-defence-xgc/measure.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analytics import backtest                    # noqa: E402
from src.storage import Storage                       # noqa: E402

MIN_MINUTES = 180


def team_xgc90(players):
    """`{team: xGC per 90}` from the defenders' own rows — minutes-normalised, so a team whose defenders play
    more does not look worse for it. (An unnormalised first cut made exactly that mistake.)"""
    agg = {}
    for p in players:
        if p["position"] in ("DEF", "GK") and (p["minutes"] or 0) >= MIN_MINUTES:
            a = agg.setdefault(p["team"], [0.0, 0.0])
            a[0] += (p["xgc"] or 0.0)
            a[1] += (p["minutes"] or 0)
    return {t: v[0] / (v[1] / 90) for t, v in agg.items() if v[1]}


def main():
    store = Storage()
    try:
        players = store.get_players()
        gwh = store.get_gw_history_by_code()
        codes = store.get_player_codes()
    finally:
        store.close()

    rates = team_xgc90(players)
    league = sum(rates.values()) / len(rates)
    pos = {codes[p["id"]]: p["position"] for p in players if p["id"] in codes}
    team = {codes[p["id"]]: p["team"] for p in players if p["id"] in codes}
    back = {c for c, x in pos.items() if x in ("DEF", "GK")}

    print(f"league mean {league:.2f} xGC/90 · {len(rates)} clubs · "
          f"{len(backtest.rounds_with_actuals(gwh))} gameweeks\n")
    ordered = sorted(rates.items(), key=lambda kv: kv[1])
    print("  best :", ", ".join(f"{t} {v:.2f}" for t, v in ordered[:3]))
    print("  worst:", ", ".join(f"{t} {v:.2f}" for t, v in ordered[-3:]))

    # Does a defender's actual return correlate with his club's xGC/90 at all? The cheapest possible check,
    # and the one that decides whether a sweep is even worth running.
    pairs = []
    for code, rows in gwh.items():
        if code not in back or team.get(code) not in rates:
            continue
        for r in rows:
            if r["total_points"] is not None and (r["minutes"] or 0) >= 60:
                pairs.append((-rates[team[code]], r["total_points"]))   # negated: better defence = higher
    rho = backtest.spearman([a for a, _ in pairs], [b for _, b in pairs])
    n = len(pairs)
    se = backtest.spearman_se(n)
    print(f"\n  DEF/GK player-gameweeks with 60+ mins: {n}")
    print(f"  Spearman(club defensive quality, that player's actual points) = {rho:+.3f}  (1 SE ≈ {se:.3f})")
    print("\n  ⚠️ This is a CORRELATION, not a backtest of the term. It answers one question only:")
    print("     is there anything here that clean-sheet rate was too noisy to see?")


if __name__ == "__main__":
    main()
