"""Sprint 015 spike (US-048): quantify soccerdata's unique value — npXG.

Throwaway evaluation code. FPL gives total xG (penalties included); Understat gives
`np_xg` (non-penalty xG), which FPL does not. For penalty-takers the two diverge, and
npXG is the better predictor of open-play threat. This measures how much npXG re-ranks
the top attackers vs FPL's own xG — i.e. whether the unique field changes a decision.
"""

import re
import unicodedata
import warnings

warnings.filterwarnings("ignore")
import requests
import soccerdata as sd


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", " ", s.lower())).strip()


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def main():
    boot = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/").json()
    teams = {t["id"]: t["name"] for t in boot["teams"]}
    fpl = [{
        "web": norm(p["web_name"]),
        "full": norm(p["first_name"] + " " + p["second_name"]),
        "team": teams.get(p["team"], ""),
        "fpl_xg": f(p["expected_goals"]),
    } for p in boot["elements"] if f(p["expected_goals"]) > 0]

    # Season alignment matters: FPL's expected_goals reflects the *last completed* season
    # (2025/26 here). Pulling the wrong Understat season silently joins mismatched data
    # (e.g. Thiago 20.6 vs 0.1). Understat "2025" == 2025/26.
    us = (sd.Understat(leagues="ENG-Premier League", seasons="2025")
          .read_player_season_stats().reset_index())
    us_by_token = {}
    us_by_full = {}
    for _, r in us.iterrows():
        rec = {"full": norm(r["player"]), "team": norm(r["team"]),
               "xg": f(r["xg"]), "npxg": f(r["np_xg"])}
        us_by_full.setdefault(rec["full"], []).append(rec)
        for tok in rec["full"].split():
            us_by_token.setdefault(tok, []).append(rec)

    def match(p):
        cands = us_by_full.get(p["full"]) or us_by_token.get(p["web"]) or []
        if len(cands) == 1:
            return cands[0]
        hits = [c for c in cands if norm(p["team"]).split()[0] in c["team"]
                or c["team"].split()[0] in norm(p["team"])]
        return hits[0] if len(hits) == 1 else None

    rows = []
    for p in fpl:
        u = match(p)
        if u:
            rows.append({"web": p["web"], "fpl_xg": p["fpl_xg"],
                         "us_xg": u["xg"], "npxg": u["npxg"],
                         "pen_gap": u["xg"] - u["npxg"]})

    print(f"matched attackers with xG on both sides: {len(rows)}\n")

    by_fpl = sorted(rows, key=lambda r: -r["fpl_xg"])[:15]
    print("Top 15 by FPL xG (which includes penalties):")
    print(f"  {'player':16} {'FPL xG':>7} {'US xG':>7} {'npXG':>7} {'pen gap':>8}")
    for r in by_fpl:
        print(f"  {r['web'][:16]:16} {r['fpl_xg']:7.1f} {r['us_xg']:7.1f} "
              f"{r['npxg']:7.1f} {r['pen_gap']:8.1f}")

    # Does npXG re-rank the top attackers vs FPL xG?
    top_fpl = [r["web"] for r in sorted(rows, key=lambda r: -r["fpl_xg"])[:10]]
    top_npxg = [r["web"] for r in sorted(rows, key=lambda r: -r["npxg"])[:10]]
    entered = [w for w in top_npxg if w not in top_fpl]
    dropped = [w for w in top_fpl if w not in top_npxg]
    print(f"\nTop-10 by FPL xG vs by npXG:")
    print(f"  enters top-10 on npXG: {entered}")
    print(f"  drops out on npXG:     {dropped}")
    big = sorted(rows, key=lambda r: -r["pen_gap"])[:5]
    print(f"  biggest penalty inflation (xG that isn't open-play): "
          f"{[(r['web'], round(r['pen_gap'],1)) for r in big]}")


if __name__ == "__main__":
    main()
