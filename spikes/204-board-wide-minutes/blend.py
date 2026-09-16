"""The Phase 1 gate: a minutes forecaster that is better BOARD-WIDE, and what it buys the ranking.

ADR-202 found that its first premise test was a **false negative** — "last GW's minutes" is 15% better than
the live model on *owned* players but a **dead heat board-wide** (24.6 vs 24.5), and the ranking is
board-wide. ⭐ *A substitute that is not better on the population being scored cannot test whether better
helps.* This is that test, run properly.

It also has a candidate rather than a guess, because ADR-202 located the weak part: the **historical
fallback** (32.1 MAE against the in-season term's 20.0, same players), which `in_season_share` reaches for
whenever a player missed even one completed gameweek — 35-52 of ~190 owned players every round, and all of
them at GW1.

**The candidate is shrinkage.** ADR-173's guard is all-or-nothing by design: *"played every completed
gameweek, with minutes in each, or fall back to last season"*. That refusal exists for a real reason — two
gameweeks cannot tell a rested player from a phased-out one. Shrinkage answers the same worry **continuously**
instead of categorically: trust this season in proportion to how much of it there is.

    share = (n * in_season + k * historical) / (n + k)

`k` is the prior strength in gameweeks — `k = 3` means three rounds of evidence before this season outweighs
last. At n = 0 it *is* the historical share; it never craters a nailed starter on one rest, and it never
ignores four straight benchings either.
"""

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analytics.minutes import (  # noqa: E402
    availability_weight,
    chance_factor,
    completed_gameweeks,
    expected_minutes,
    minutes_weight_from_history,
)
from src.storage import Storage  # noqa: E402

FULL_GAME = 90
START = 60


def in_season_evidence(player, before):
    """`(mean share, n rounds of evidence)` — counting a benching as the 0 it is.

    ⚠️ Denominator is **rounds he has a row for**, not every completed round. A missing row means his club had
    no fixture or he was not on the squad list; scoring that as 0 minutes would punish a blank gameweek as if
    it were a benching (ADR-173's caveat, still unresolved and still not triggered — no blanks yet).
    """
    rows = (before or {}).get(player["code"]) or []
    if not rows:
        return None, 0
    shares = [min(1.0, (r["minutes"] or 0) / FULL_GAME) for r in rows]
    return statistics.mean(shares), len(shares)


def blended_factory(k, history_by_code, gw_history_by_code=None):
    def weight(player):
        in_season, n = in_season_evidence(player, gw_history_by_code)
        hist_weight = availability_weight(player, history_by_code.get(player["code"], []))
        cf = chance_factor(player)
        hist_share = (hist_weight / cf) if cf else hist_weight     # undo the chance factor, re-applied below
        if n == 0:
            return cf * min(1.0, hist_share)
        share = (n * in_season + k * hist_share) / (n + k)
        return cf * min(1.0, share)
    return weight


def score_minutes(players, gw_hist, hist, weight_for, keep=None):
    """Board-wide minutes MAE / bias / start-call, walk-forward."""
    errs, right, n = [], 0, 0
    for rnd in sorted(completed_gameweeks(gw_hist)):
        before = {c: [r for r in rows if r["round"] < rnd] for c, rows in gw_hist.items()}
        w = weight_for(hist, before)
        for p in players:
            if keep and not keep(p):
                continue
            row = next((r for r in (gw_hist.get(p["code"]) or []) if r["round"] == rnd), None)
            if row is None:
                continue
            pred, actual = expected_minutes(w(p)), row["minutes"] or 0
            errs.append(pred - actual)
            right += (pred >= START) == (actual >= START)
            n += 1
    return {"n": n, "mae": statistics.mean(abs(e) for e in errs),
            "bias": statistics.mean(errs), "start_acc": right / n}


def main():
    db = Storage()
    players = db.get_players()
    gw_hist = db.get_gw_history_by_code()
    hist = db.get_history_by_code()
    owned = {p["code"] for p in players if (p["selected_by"] or 0) >= 1.0}

    print("MINUTES ACCURACY — the gate is 'better BOARD-WIDE', which the first attempt was not\n")
    print(f"  {'forecaster':<26} {'board MAE':>10} {'bias':>8} {'start':>7} | {'owned MAE':>10} {'start':>7}")

    def row(label, factory):
        b = score_minutes(players, gw_hist, hist, factory)
        o = score_minutes(players, gw_hist, hist, factory, keep=lambda p: p["code"] in owned)
        print(f"  {label:<26} {b['mae']:>10.1f} {b['bias']:>+8.1f} {b['start_acc']:>6.1%} | "
              f"{o['mae']:>10.1f} {o['start_acc']:>6.1%}")
        return b, o

    base = row("xMins v0 (the app)", lambda h, before: minutes_weight_from_history(h, before))
    best = None
    for k in (1, 2, 3, 5, 8):
        b, o = row(f"blend, k={k}", (lambda kk: lambda h, before: blended_factory(kk, h, before))(k))
        if best is None or b["mae"] < best[1]["mae"]:
            best = (k, b, o)
    print(f"\n  baseline board MAE {base[0]['mae']:.1f} -> best blend k={best[0]} at {best[1]['mae']:.1f} "
          f"({(base[0]['mae'] - best[1]['mae']) / base[0]['mae']:+.1%})")
    db.close()


if __name__ == "__main__":
    main()
