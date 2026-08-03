"""Sprint 015 spike (US-047): measure FPL <-> Understat name-matching.

Throwaway evaluation code — NOT part of the app. Run in a venv with soccerdata:
    python3 -m venv sd_probe && ./sd_probe/bin/pip install soccerdata
    ./sd_probe/bin/python match_fpl_understat.py

It matches FPL's current roster to Understat's 2024/25 player-season stats and reports
the match rate, splitting the misses into "absent" (roster drift — the player isn't in
Understat at all) vs "name-form" (their surname IS in Understat but we couldn't confirm
the match). That split is what tells us whether matching is a solvable problem.
"""

import re
import unicodedata
import warnings

warnings.filterwarnings("ignore")
import requests
import soccerdata as sd


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z ]", " ", s.lower()).strip()


def collapse(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


# Team aliases: FPL short/long name -> a token that also appears in the Understat team.
TEAM_ALIAS = {
    "spurs": "tottenham", "man city": "manchester city", "man utd": "manchester united",
    "nott'm forest": "nottingham", "wolves": "wolverhampton", "newcastle": "newcastle",
}


def team_key(name: str) -> str:
    n = norm(name)
    return TEAM_ALIAS.get(n, n)


def team_match(fpl_team: str, us_team: str) -> bool:
    a, b = team_key(fpl_team), norm(us_team)
    return a in b or b in a or a.split()[0] == b.split()[0]


def main():
    # --- FPL side: current roster, players who actually played ---
    boot = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/").json()
    teams = {t["id"]: t["name"] for t in boot["teams"]}
    fpl = []
    for p in boot["elements"]:
        if p["minutes"] <= 0:
            continue
        fpl.append({
            "full": collapse(norm(p["first_name"] + " " + p["second_name"])),
            "surname": norm(p["second_name"]).split()[-1] if norm(p["second_name"]) else "",
            "web": norm(p["web_name"]),
            "team": teams.get(p["team"], ""),
        })

    # --- Understat side: 2024/25 player-season stats ---
    us = (sd.Understat(leagues="ENG-Premier League", seasons="2024")
          .read_player_season_stats().reset_index())
    us_players = [{"full": collapse(norm(r["player"])), "team": r["team"]}
                  for _, r in us.iterrows()]
    us_by_full = {}
    us_by_token = {}          # each name token -> understat players (for common-name layer)
    for u in us_players:
        us_by_full.setdefault(u["full"], []).append(u)
        for tok in u["full"].split():
            us_by_token.setdefault(tok, []).append(u)
    us_surnames = {u["full"].split()[-1] for u in us_players if u["full"]}

    def confident(cands, p):
        """One candidate, or several resolved to one by team."""
        if len(cands) == 1:
            return True
        team_hits = [c for c in cands if team_match(p["team"], c["team"])]
        return len(team_hits) == 1

    matched = absent = nameform = 0
    nameform_examples = []
    for p in fpl:
        # Layer 1: exact full-name (formal name matches).
        cands = us_by_full.get(p["full"], [])
        # Layer 2: FPL web_name (the *common* name) as a token in an Understat name.
        if not confident(cands, p) and p["web"]:
            cands = us_by_token.get(p["web"], []) or cands
        if confident(cands, p):
            matched += 1
        elif p["surname"] and p["surname"] in us_surnames or (p["web"] in us_by_token):
            nameform += 1
            if len(nameform_examples) < 8:
                nameform_examples.append(f"{p['full']} / web={p['web']} ({p['team']})")
        else:
            absent += 1

    n = len(fpl)
    print(f"FPL players (played): {n}    Understat 2024/25 players: {len(us_players)}")
    print(f"matched (confident):  {matched:4d}  ({100*matched//n}%)")
    print(f"name-form miss:       {nameform:4d}  ({100*nameform//n}%)  <- present in Understat, no confident match")
    print(f"absent (roster drift):{absent:4d}  ({100*absent//n}%)  <- not in Understat 24/25 at all")
    print()
    print(f"match rate among 'should be matchable' (matched / (matched+nameform)): "
          f"{100*matched//(matched+nameform)}%")
    print("residual name-form misses:", nameform_examples)


if __name__ == "__main__":
    main()
