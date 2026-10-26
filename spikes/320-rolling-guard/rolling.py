"""ADR-320 option A: does loosening the all-or-nothing in-season guard to a ROLLING WINDOW help?

ADR-173's guard is *"played every completed gameweek, with minutes in each, or fall back to last season"*.
The objection ADR-320 raised is not that the rule is wrong but that **it gets stricter every week it
survives**: by GW20 one rest in August permanently disqualifies a player who has started nineteen since.
⭐ *A rule whose failure rate only ever rises is one that will eventually disqualify everybody.*

Option A keeps the refusal and drops the ratchet: judge him on the **last `window` completed gameweeks**,
and answer only if he appeared with minutes in at least `need` of them.

⚠️ **The denominator is the real design choice here, not the threshold.** ADR-173 divides by the games he
*appeared in*, which is unambiguous only because its guard forces "appeared in" == "all of them". Once
`need < window` the two diverge sharply — Onyeka at 4x90 in the last 5 is **0.80** of available minutes and
**1.00** of minutes he played. Both are swept; the `available` denominator is the one that matches the
docstring's claim, and it is also what bounds the damage: ⭐ *the window does not protect a rested starter by
refusing to answer, it protects him by capping one bad week's influence at 1/window.*

Run 1 of 2. This scores **minutes** (what the change touches directly) and counts the ratchet.
`rolling_on_points.py` scores the **ranking** against §B0's bar.
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
    in_season_share,
    minutes_weight_from_history,
)
from src.storage import Storage  # noqa: E402

FULL_GAME = 90
START = 60


def rolling_share(player, gw_history_by_code, completed, window, tolerance, denom="available"):
    """ADR-173's share, judged on the last `window` completed gameweeks, forgiving `tolerance` misses.

    Returns None — "we cannot say, keep his historical share" — when he missed more than `tolerance` of the
    recent window. At `window >= len(completed)` and `tolerance = 0` with `denom="appeared"` this **is**
    `in_season_share`, which is the identity check `main()` asserts rather than trusts.

    ⚠️⚠️ **The threshold is a tolerance, not an absolute count, and the first draft of this spike had it as
    an absolute.** "Started >= 4 of the last 5" cannot be met at GW3, so that draft **switched the in-season
    term off for the opening weeks** — it was *stricter* than the rule it was loosening, and the per-round ρ
    showed it plainly (worse than live at GW2-6, identical at GW8-9). ⭐ *A candidate that is worse than the
    status quo in a region the status quo already handles is not a loosening; it is two changes wearing one
    name.* `max(1, ...)` keeps it a true superset: identical to ADR-173 until the window fills, looser after.
    """
    recent = sorted(completed)[-window:]
    need = max(1, len(recent) - tolerance)
    rows = {r["round"]: r for r in ((gw_history_by_code or {}).get(player["code"]) or [])}
    played = [rows[g] for g in recent if g in rows and (rows[g]["minutes"] or 0) > 0]
    if len(played) < need:
        return None
    over = len(recent) if denom == "available" else len(played)
    return min(1.0, sum(r["minutes"] or 0 for r in played) / (over * FULL_GAME))


def rolling_factory(window, tolerance, denom, history_by_code, gw_history_by_code=None):
    """`minutes_weight_from_history` with the guard swapped — everything else identical."""
    completed = completed_gameweeks(gw_history_by_code) if gw_history_by_code else set()

    def weight(player):
        share = (rolling_share(player, gw_history_by_code, completed, window, tolerance, denom)
                 if completed else None)
        if share is not None:
            return chance_factor(player) * share
        return availability_weight(player, history_by_code.get(player["code"], []))
    return weight


def score_minutes(players, gw_hist, hist, weight_for, keep=None):
    """Board-wide minutes MAE / bias / start-call, walk-forward (lifted from spikes/204)."""
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


def the_ratchet(players, gw_hist, window, tolerance):
    """Per round: how many players the live guard refuses, and how many the window would answer for.

    ⚠️ This is the claim ADR-320 made *without* measuring it. If the refusal rate does not actually climb,
    option A is answering a worry the data does not have.
    """
    out = []
    for rnd in sorted(completed_gameweeks(gw_hist)):
        before = {c: [r for r in rows if r["round"] < rnd] for c, rows in gw_hist.items()}
        completed = completed_gameweeks(before)
        if not completed:
            continue
        # Only players whose club has actually played — a player with no rows at all is not a refusal,
        # he is a player we know nothing about, and no guard would help him.
        seen = [p for p in players if (before.get(p["code"]) or [])]
        live = [p for p in seen if in_season_share(p, before, completed) is None]
        rescued = [p for p in live
                   if rolling_share(p, before, completed, window, tolerance) is not None]
        out.append((rnd, len(completed), len(seen), len(live), len(rescued)))
    return out


def main():
    db = Storage()
    players = db.get_players()
    gw_hist = db.get_gw_history_by_code()
    hist = db.get_history_by_code()
    owned = {p["code"] for p in players if (p["selected_by"] or 0) >= 1.0}
    completed = completed_gameweeks(gw_hist)

    # The identity check, first and loudly: a sweep whose baseline is not reproduced by its own
    # parameterisation is measuring two different things and comparing them.
    wide = len(completed) + 1
    mismatch = [p["code"] for p in players
                if in_season_share(p, gw_hist, completed)
                != rolling_share(p, gw_hist, completed, wide, 0, "appeared")]
    print(f"identity check at window={wide}, tolerance=0, denom=appeared: "
          f"{'OK — reproduces in_season_share exactly' if not mismatch else f'{len(mismatch)} MISMATCHES'}\n")

    print("THE RATCHET — is the refusal rate actually climbing? (window=5, tolerance=1)\n")
    print(f"  {'GW':>3} {'completed':>10} {'with rows':>10} {'refused':>8} {'refused %':>10} {'window answers':>15}")
    table = the_ratchet(players, gw_hist, 5, 1)
    for rnd, ncomp, seen, live, rescued in table:
        print(f"  {rnd:>3} {ncomp:>10} {seen:>10} {live:>8} {live / seen:>9.1%} {rescued:>15}")

    # ⭐ The projection is the point, not the level. 78% refused at GW8 is survivable; a rate that rises
    # every week is a term switching itself off, and the in-season term is the one ADR-204 measured at
    # 2.9 SE. ⚠️ A projection, clearly: 8 rounds of survival extrapolated at the observed weekly hazard.
    surv = [1 - live / seen for _, _, seen, live, _ in table]
    hazards = [surv[i] / surv[i - 1] for i in range(1, len(surv)) if surv[i - 1]]
    h = statistics.mean(hazards)
    print(f"\n  qualifying at GW{table[-1][0]}: {surv[-1]:.1%}.  Mean weekly survival among survivors: {h:.3f}")
    for gw in (15, 25, 38):
        print(f"    projected at GW{gw}: {surv[-1] * h ** (gw - table[-1][0]):.2%} of players still answered "
              f"by the in-season term")

    print("\n\nMINUTES ACCURACY — scored on the board and on owned (ADR-204: two forecasters can each win one)\n")
    print(f"  {'guard':<30} {'board MAE':>10} {'bias':>8} {'start':>7} | {'owned MAE':>10} {'start':>7}")

    def row(label, factory):
        b = score_minutes(players, gw_hist, hist, factory)
        o = score_minutes(players, gw_hist, hist, factory, keep=lambda p: p["code"] in owned)
        print(f"  {label:<30} {b['mae']:>10.1f} {b['bias']:>+8.1f} {b['start_acc']:>6.1%} | "
              f"{o['mae']:>10.1f} {o['start_acc']:>6.1%}")
        return b, o

    base = row("ADR-173 (the app)", lambda h, before: minutes_weight_from_history(h, before))
    best = None
    for denom in ("available", "appeared"):
        print(f"  {'-- denominator: ' + denom:<30}")
        for window in (3, 4, 5, 6, 8):
            for tol in (0, 1, 2, window - 1):
                if tol >= window:
                    continue
                f = (lambda w, t, dn: lambda h, before: rolling_factory(w, t, dn, h, before))(
                    window, tol, denom)
                b, o = row(f"  last {window}, forgive {tol}", f)
                if best is None or b["mae"] < best[-1]["mae"]:
                    best = (window, tol, denom, b)
    w, tol, dn, b = best
    print(f"\n  baseline board MAE {base[0]['mae']:.1f} -> best guard (last {w}, forgive {tol}, {dn}) "
          f"at {b['mae']:.1f} ({(b['mae'] - base[0]['mae']) / base[0]['mae']:+.1%})")
    db.close()


if __name__ == "__main__":
    main()
