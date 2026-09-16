"""0b — the walk-forward baseline for the minutes model (ML roadmap Phase 0b).

**Read-only. Imports the real model; changes nothing.**

Why this exists before any learning happens: ⭐ *a model with no baseline is not an improvement, it is a
replacement.* Anything learned later has to beat a number, and the number has to be measured the same way the
learned model will be — walk-forward, predicting round N from rounds < N only (ADR-101's method, applied to
minutes instead of points).

It also serves ADR-192 directly. That ADR found 124 players modelled as **nailed 90-minute starters on no
evidence**, because `minutes_share` returns None for a player with no history and None is read as 1.0. The
question it could not answer was *how wrong is that, in minutes* — which is what a signed error measures.

⚠️ **The model is compared against naive forecasters, not against zero.** An MAE on its own is unreadable:
"the model is out by 23 minutes" is neither good nor bad until you know that predicting 90 for everyone is out
by 31 and predicting last week's minutes is out by 19. ⭐ *A baseline is a comparison or it is a number.*
"""

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analytics.minutes import (  # noqa: E402
    completed_gameweeks,
    expected_minutes,
    minutes_weight_from_history,
)
from src.storage import Storage  # noqa: E402

FULL_GAME = 90
START = 60           # FPL's own line: 60 minutes is the difference between 1 and 2 appearance points


# --- the forecasters ----------------------------------------------------------------
# Each takes (player, gw_rows_before_N, history_by_code) and returns predicted minutes for round N.

def f_model(player, before, history_by_code):
    """The live xMins v0 weight × 90 — exactly what the app uses (ADR-038/173)."""
    weight = minutes_weight_from_history(history_by_code, before)
    return expected_minutes(weight(player))


def f_always_90(player, before, history_by_code):
    """Everyone starts and finishes. The trivial forecaster — and the one the model collapses to
    whenever it has no history, which is the whole of ADR-192's complaint."""
    return FULL_GAME


def f_persistence(player, before, history_by_code):
    """Last completed round's minutes. **The forecaster to beat** — in most sequence problems the
    naive "same as last time" is stubbornly hard to improve on, and a model that cannot is not
    adding information, it is adding machinery."""
    rows = (before or {}).get(player["code"]) or []
    if not rows:
        return FULL_GAME                      # nothing in-season yet → the optimistic default, same as the model
    last = max(rows, key=lambda r: r["round"])
    return last["minutes"] or 0


def f_season_mean(player, before, history_by_code):
    """Mean minutes over every round so far — persistence with the noise averaged out."""
    rows = (before or {}).get(player["code"]) or []
    if not rows:
        return FULL_GAME
    return statistics.mean((r["minutes"] or 0) for r in rows)


FORECASTERS = {
    "xMins v0 (the app)": f_model,
    "always 90":          f_always_90,
    "last GW":            f_persistence,
    "mean so far":        f_season_mean,
}


# --- the walk-forward loop ----------------------------------------------------------

def walk_forward(players, gw_history_by_code, history_by_code, forecaster, keep=None):
    """`(predicted, actual, round, code)` for every player-round we can honestly score.

    ⚠️ **A round only counts once it has a scoreline** (`completed_gameweeks`). FPL writes a player's row when
    the fixture is *scheduled*, so `minutes == 0` in an in-flight gameweek means "has not kicked off", not
    "did not play" — scoring those would libel every player at every club mid-gameweek (ADR-125/129).
    """
    completed = sorted(completed_gameweeks(gw_history_by_code))
    out = []
    for n in completed:
        before = {code: [r for r in rows if r["round"] < n] for code, rows in gw_history_by_code.items()}
        for p in players:
            if keep and not keep(p, before, n):
                continue
            row = next((r for r in (gw_history_by_code.get(p["code"]) or []) if r["round"] == n), None)
            if row is None:
                continue                      # his club had no fixture, or he was not on the squad list
            out.append((forecaster(p, before, history_by_code), row["minutes"] or 0, n, p["code"]))
    return out


def score(triples):
    """MAE, signed bias, and how often the start/bench call is right — three different questions."""
    if not triples:
        return None
    errs = [pred - actual for pred, actual, _, _ in triples]
    right = sum((pred >= START) == (actual >= START) for pred, actual, _, _ in triples)
    return {
        "n": len(triples),
        "mae": statistics.mean(abs(e) for e in errs),
        "bias": statistics.mean(errs),                 # + means the model is OPTIMISTIC
        "start_acc": right / len(triples),
    }


def report(title, players, gw_hist, hist, keep=None):
    print(f"\n=== {title} ===")
    rows = []
    for name, fn in FORECASTERS.items():
        s = score(walk_forward(players, gw_hist, hist, fn, keep))
        if s:
            rows.append((name, s))
    if not rows:
        print("  (no scorable rows)")
        return
    print(f"  n = {rows[0][1]['n']} player-gameweeks")
    print(f"  {'forecaster':<20} {'MAE':>7} {'bias':>8} {'start call':>11}")
    for name, s in rows:
        print(f"  {name:<20} {s['mae']:>7.1f} {s['bias']:>+8.1f} {s['start_acc']:>10.1%}")


def main():
    db = Storage()
    players = db.get_players()
    gw_hist = db.get_gw_history_by_code()
    hist = db.get_history_by_code()

    completed = sorted(completed_gameweeks(gw_hist))
    print(f"players: {len(players)}   completed rounds: {completed}")

    report("A. every player on the squad list", players, gw_hist, hist)

    # ADR-200's lesson, applied: say what population, and why. A whole-board number is dominated by players
    # nobody would ever pick, and the app's job is to rank the ones a manager is choosing between.
    owned = [p for p in players if (p["selected_by"] or 0) >= 1.0]
    report(f"B. owned by >=1% of managers  (n={len(owned)} players)", owned, gw_hist, hist)

    # ADR-192's 124: no past seasons at all, so `minutes_share` is None and the weight collapses to the
    # chance factor — i.e. 1.0 for anyone without an injury flag. This is the population that ADR's
    # constant has to be set on.
    cold = [p for p in players if not hist.get(p["code"])]
    report(f"C. ADR-192's cold start: no past seasons  (n={len(cold)} players)", cold, gw_hist, hist)

    db.close()


if __name__ == "__main__":
    main()


# --- sensitivity: what the headline number is standing on ----------------------------

def sensitivity():
    """Two checks the headline table cannot make about itself.

    ⚠️ **1. The one real leak in this measurement.** `chance_factor` reads the player's **current**
    `status` / `chance` straight off the players table — today's injury news, applied retrospectively to
    round 1. That is not walk-forward and cannot be made so: FPL serves availability as a *now* field and we
    store no history of it. So the model here is scored with information it did not have at the time. The
    variant below strips the chance factor entirely; the gap between them is the size of the contamination.

    **2. Is the result one round or four?** A win driven by a single gameweek is a coin flip with a table
    drawn round it (ADR-183). Per-round columns say which.
    """
    db = Storage()
    players = db.get_players()
    gw_hist = db.get_gw_history_by_code()
    hist = db.get_history_by_code()
    owned = [p for p in players if (p["selected_by"] or 0) >= 1.0]

    flagged = [p for p in players if (p["status"] or "a") != "a"]
    print(f"\n=== leakage: players carrying a non-available status TODAY: {len(flagged)} of {len(players)} ===")

    def f_model_no_chance(player, before, history_by_code):
        """xMins v0 with the chance factor forced to 1.0 — the share term alone, fully walk-forward."""
        from src.analytics.minutes import availability_weight, in_season_share
        completed = completed_gameweeks(before) if before else set()
        share = in_season_share(player, before, completed) if completed else None
        if share is None:
            w = availability_weight(player, history_by_code.get(player["code"], []))
            chance = f_model(player, before, history_by_code) / FULL_GAME
            share = w / chance if chance else w          # undo the chance factor
        return expected_minutes(min(1.0, share))

    print("\n=== A' — owned >=1%, model with NO availability news (no leak) ===")
    s = score(walk_forward(owned, gw_hist, hist, f_model_no_chance))
    print(f"  xMins v0, share only   MAE {s['mae']:.1f}  bias {s['bias']:+.1f}  start call {s['start_acc']:.1%}")

    print("\n=== per round (owned >=1%) — MAE, and is the winner the same every week? ===")
    print(f"  {'forecaster':<20} " + " ".join(f"{'GW'+str(n):>8}" for n in sorted(completed_gameweeks(gw_hist))))
    for name, fn in FORECASTERS.items():
        triples = walk_forward(owned, gw_hist, hist, fn)
        cells = []
        for n in sorted(completed_gameweeks(gw_hist)):
            s = score([t for t in triples if t[2] == n])
            cells.append(f"{s['mae']:>8.1f}" if s else f"{'-':>8}")
        print(f"  {name:<20} " + " ".join(cells))
    db.close()


def diagnose_fallback():
    """**Why** the model loses: how often does it use this season at all?

    `in_season_share` (ADR-173) returns a share only for a player who appeared in **every** completed
    gameweek with minutes in each; everyone else falls back to last season's share. That refusal was
    deliberate — it stops a single rested week cratering a nailed starter — and this counts what it costs.
    """
    from src.analytics.minutes import in_season_share
    db = Storage()
    players = db.get_players()
    gw_hist = db.get_gw_history_by_code()
    hist = db.get_history_by_code()
    owned = [p for p in players if (p["selected_by"] or 0) >= 1.0]

    print("\n=== how often the model uses THIS season vs last (owned >=1%) ===")
    print(f"  {'round':>6} {'in-season':>11} {'fell back':>11} {'MAE in-season':>15} {'MAE fell back':>15}")
    for n in sorted(completed_gameweeks(gw_hist)):
        before = {c: [r for r in rows if r["round"] < n] for c, rows in gw_hist.items()}
        completed = completed_gameweeks(before)
        used, fell = [], []
        for p in owned:
            row = next((r for r in (gw_hist.get(p["code"]) or []) if r["round"] == n), None)
            if row is None:
                continue
            share = in_season_share(p, before, completed) if completed else None
            pred = f_model(p, before, hist)
            (used if share is not None else fell).append((pred, row["minutes"] or 0, n, p["code"]))
        su, sf = score(used), score(fell)
        print(f"  {n:>6} {len(used):>11} {len(fell):>11} "
              f"{(f'{su['mae']:.1f}' if su else '-'):>15} {(f'{sf['mae']:.1f}' if sf else '-'):>15}")
    db.close()


def ab_same_players():
    """⚠️ **The fallback table above compares two populations, not two methods.**

    "In-season MAE 14.2 vs fell-back 25.8" scores *different players* — the fell-back group is exactly the
    group with erratic minutes, so it is harder to predict whoever predicts it. ⭐ *A comparison between two
    groups is a fact about the groups until you run both methods on one of them.*

    So: take only the players where the in-season share is available, and score what the model DID say
    against what it WOULD have said on last season alone. Same players, same rounds, two methods.
    """
    from src.analytics.minutes import availability_weight, chance_factor, in_season_share
    db = Storage()
    players = db.get_players()
    gw_hist = db.get_gw_history_by_code()
    hist = db.get_history_by_code()
    owned = [p for p in players if (p["selected_by"] or 0) >= 1.0]

    print("\n=== A/B on the SAME players: this season's share vs last season's ===")
    print(f"  {'round':>6} {'n':>5} {'MAE in-season':>15} {'MAE history':>13} {'MAE last GW':>13}")
    tot = {"in": [], "hist": [], "last": []}
    for n in sorted(completed_gameweeks(gw_hist)):
        before = {c: [r for r in rows if r["round"] < n] for c, rows in gw_hist.items()}
        completed = completed_gameweeks(before)
        if not completed:
            continue
        rows_n = []
        for p in owned:
            row = next((r for r in (gw_hist.get(p["code"]) or []) if r["round"] == n), None)
            share = in_season_share(p, before, completed) if row is not None else None
            if share is None:
                continue
            actual = row["minutes"] or 0
            cf = chance_factor(p)
            rows_n.append((
                expected_minutes(cf * share),                                        # what it said
                expected_minutes(availability_weight(p, hist.get(p["code"], []))),   # history only
                f_persistence(p, before, hist),                                      # last GW
                actual))
        if not rows_n:
            continue
        for key, i in (("in", 0), ("hist", 1), ("last", 2)):
            tot[key] += [(r[i], r[3], n, 0) for r in rows_n]
        m = {k: score([(r[i], r[3], n, 0) for r in rows_n])["mae"] for k, i in (("in", 0), ("hist", 1), ("last", 2))}
        print(f"  {n:>6} {len(rows_n):>5} {m['in']:>15.1f} {m['hist']:>13.1f} {m['last']:>13.1f}")
    print(f"  {'ALL':>6} {len(tot['in']):>5} " + " ".join(
        f"{score(tot[k])['mae']:>{w}.1f}" for k, w in (("in", 15), ("hist", 13), ("last", 13))))
    db.close()
