"""ADR-375's gate: does a PERSONAL clean-sheet baseline rescue the term ADR-370 declined?

`clean_sheet_delta` prices a club's clean sheets as `4 × (team_now − league_now)` — a delta, so as not to
double-count the clean sheets already inside a player's historical pts/90. ⭐⭐ But it subtracts the
**league** rate, which removes the *average* player's historical clean sheets, not **his**. Every Arsenal
defender therefore gets the identical credit, when White needs a third of what Konsa needs.

Three baselines, swept over `CLEAN_SHEET_WEIGHT` and scored **on DEF/GK** (ADR-190: score the population
the term applies to):

  control  — today's `4 × (team_now − league_now)`. Reproduces ADR-370, so the comparison has a floor.
  A        — era-relative personal: `4 × ((team_now − league_now) − his_edge)`, where `his_edge` is how
             much better his old defence was than ITS OWN era. ~0 for a player whose club was average, so
             the correction self-nulls for everyone who did not move.
  B        — A with the population mean of `his_edge` removed, so the level shift is zero by construction.

⚠️ **B exists because ρ is rank-based.** Spearman cannot see a constant added to every DEF/GK, only the
differential part — and A carries a +0.135 pts/match level shift I could not explain (ADR-375). If B ≈ A the
shift was never doing anything; if B > A it was bias; if both decline, the baseline was not ADR-370's
problem and this line closes with it. ⭐ *A gate that cannot come back "the premise was wrong" is not a gate.*

Reuses `spikes/192-defender-only-calibration/measure.py` for the sweep and the DEF/GK scoring, because that
is the harness ADR-370 was argued on.
"""

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "192-defender-only-calibration"))

from measure import score, triples_for  # noqa: E402

from src import config  # noqa: E402
from src.analytics import backtest  # noqa: E402
from src.analytics import xp as xp_mod  # noqa: E402
from src.analytics.cleansheet import (  # noqa: E402
    CLEAN_SHEET_POINTS,
    CLEAN_SHEET_POSITIONS,
    historical_cs_edge,
    league_cs_by_season,
)
from src.storage import Storage  # noqa: E402

WEIGHTS = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75, 1.0]


def make_delta(kind, history, league_by_season, mean_edge):
    """A drop-in `clean_sheet_delta` for one of the three baselines."""
    def delta(player, team_rate, league_rate):
        if player["position"] not in CLEAN_SHEET_POSITIONS:
            return 0.0
        if team_rate is None or league_rate is None:
            return 0.0                      # ADR-172 — an unknown rate must never read as a bad one
        club = team_rate - league_rate
        if kind == "control":
            return CLEAN_SHEET_POINTS * club
        edge = historical_cs_edge(history.get(player["code"]) or [], league_by_season)
        if edge is None:
            return CLEAN_SHEET_POINTS * club    # no personal baseline → today's behaviour, not a guess
        if kind == "demeaned":
            edge -= mean_edge
        return CLEAN_SHEET_POINTS * (club - edge)
    return delta


def main():
    store = Storage()
    try:
        players = store.get_players()
        history = store.get_history_by_code()
        gw_history = store.get_gw_history_by_code()
        code_by_id = store.get_player_codes()
        fixtures: dict = {}

        pos_by_code = {code_by_id[p["id"]]: p["position"] for p in players if p["id"] in code_by_id}
        defgk = {c for c, pos in pos_by_code.items() if pos in CLEAN_SHEET_POSITIONS}

        league_by_season = league_cs_by_season(history, {p["code"]: p["position"] for p in players})
        edges = [e for p in players if p["position"] in CLEAN_SHEET_POSITIONS
                 if (e := historical_cs_edge(history.get(p["code"]) or [], league_by_season)) is not None]
        mean_edge = statistics.mean(edges)
        print(f"DEF/GK with a personal baseline: {len(edges)}   mean edge {mean_edge:+.4f} per start"
              f"   (= {-CLEAN_SHEET_POINTS * mean_edge:+.3f} pts/match of level shift in A)")
        print("league clean-sheet rate per season: "
              + "  ".join(f"{s}:{v:.3f}" for s, v in sorted(league_by_season.items())) + "\n")

        real = xp_mod.clean_sheet_delta

        def make_predict(weight, kind):
            def predict(before, n):
                upcoming = fixtures.setdefault(n, store.get_fixtures_by_event(n))
                old_w = config.CLEAN_SHEET_WEIGHT
                config.CLEAN_SHEET_WEIGHT = weight
                xp_mod.clean_sheet_delta = make_delta(kind, history, league_by_season, mean_edge)
                try:
                    ranked = xp_mod.decision_xp(players, upcoming, history, horizon=1,
                                                gw_history_by_code=before)
                finally:
                    config.CLEAN_SHEET_WEIGHT = old_w
                    xp_mod.clean_sheet_delta = real
                return {code_by_id[r["id"]]: r["xp"] for r in ranked if r["id"] in code_by_id}
            return predict

        gws = len(backtest.rounds_with_actuals(gw_history))
        base = score(triples_for(gw_history, make_predict(0.0, "control"), keep_codes=defgk), 10)
        print(f"scored on DEF/GK over {gws} gameweeks — the population the term applies to (ADR-190)")
        print(f"weight-0 baseline: ρ {base['rho']:.4f}  MAE {base['mae']:.2f}  hit@10 {base['hit']:.2f}"
              f"  n {base['n']}  1 SE {base['se']:.4f}\n")
        print(f"  {'baseline':<10} {'weight':>7} {'ρ':>8} {'MAE':>6} {'hit@10':>7} {'vs w=0':>18}")
        for kind in ("control", "A personal", "B demeaned"):
            key = {"control": "control", "A personal": "personal", "B demeaned": "demeaned"}[kind]
            for w in WEIGHTS:
                if w == 0.0:
                    continue                      # identical for all three: the term is off
                s = score(triples_for(gw_history, make_predict(w, key), keep_codes=defgk), 10)
                d = s["rho"] - base["rho"]
                print(f"  {kind:<10} {w:>7.2f} {s['rho']:>8.4f} {s['mae']:>6.2f} {s['hit']:>7.2f}"
                      f"   {d:>+8.4f} = {d / base['se']:>+6.2f} SE")
            print()
        print("§B0: +1 SE on ρ across ≥2 ADJACENT weights, with MAE and hit@10 not falling.")
    finally:
        store.close()


if __name__ == "__main__":
    main()
