"""Team DNA — percentile-across-the-league team profiling (Sprint 172, ADR-119).

The team-level companion to `player_dna` (ADR-118): aggregate the player pool + fixtures to per-team metrics, then
rank each team as a **percentile across the 20 PL teams** on eight facets. **Reuses** Player DNA's `Axis` / `Insight`
dataclasses + the set-piece score. Display-only: creates no new xP and never touches `decision_xp` (ADR-041) or the
FDR model — it *composes* existing signals.

Preseason it ranks on **last-season aggregates** (same basis as Player DNA). Several axes are honest, labelled
**proxies** on data we hold (no Opta/Understat): Defensive Strength = the keeper's xGC; Clean-Sheet Potential = a
defence + fixture-ease blend; Squad Depth = the count of regulars. The real clean-sheet rate + team form light up
at GW1.
"""

from collections import defaultdict
from dataclasses import dataclass

from src.analytics.fdr import team_fdr
from src.analytics.gw_form import team_clean_sheet_rate
from src.analytics.player_dna import Axis, Insight, _f, _get, _set_piece_score
from src.analytics.ranking import percentile_rank

REGULAR_MINUTES = 1500     # a player at/above this counts toward "squad depth" (a regular)

# The axes that set the overall grade (both ends + fixtures + output).
_GRADE_AXES = ("Attacking Threat", "Defensive Strength", "Fixture Strength", "FPL Output")
# Skill axes for the "top strengths" insights — defence / clean-sheet / fixtures / set-pieces each get their own
# dedicated line, so they're excluded here to avoid doubling up.
_SKILL_AXES = ("Attacking Threat", "Chance Creation", "FPL Output", "Squad Depth")


@dataclass(frozen=True)
class TeamDNA:
    """A club's eight-axis fingerprint, ranked across the league, plus an overall grade."""
    team: str               # short name (e.g. "ARS")
    name: str               # display name (falls back to the short name)
    axes: list[Axis]        # in radar order
    grade: str              # A+ · A · B · C · D (from the key axes)
    grade_score: int        # 0–100 that the grade came from


def _rank(value, values, *, invert: bool = False) -> int | None:
    """Percentile of `value` across the league (0–100), ties sharing their average rank — see
    `analytics.ranking.percentile_rank` (ADR-127). `invert=True` for lower-is-better axes (xGA, FDR) so the
    best team still scores highest."""
    return percentile_rank(value, values, invert=invert)


def _team_metrics(players, fixtures, *, next_n: int) -> dict:
    """Per-team raw metrics (a dict per team short-name). Pure; Row/dict safe."""
    teams: dict = defaultdict(list)
    for p in players:
        t = _get(p, "team")
        if t is not None:
            teams[t].append(p)
    fdr = {r["team"]: r["avg_difficulty"] for r in team_fdr(fixtures, next_n=next_n)}

    metrics = {}
    for t, ps in teams.items():
        gks = [p for p in ps if _get(p, "position") == "GK"]
        pool = gks or ps                         # the keeper's xGC ≈ the team's xGA (a clean proxy)
        xga = max((_f(_get(p, "xgc")) for p in pool), default=0.0)
        metrics[t] = {
            "attack": sum(_f(_get(p, "xg")) for p in ps),
            "create": sum(_f(_get(p, "xa")) for p in ps),
            "xga": xga,
            "fixt": fdr.get(t) if fdr.get(t) is not None else 3.0,
            "setp": sum(_set_piece_score(p) for p in ps),
            "output": sum(_f(_get(p, "total_points")) for p in ps),
            "depth": sum(1 for p in ps if _f(_get(p, "minutes")) >= REGULAR_MINUTES),
        }
    return metrics


def _grade(axes) -> tuple[str, int]:
    key = [a.percentile for a in axes if a.label in _GRADE_AXES and a.percentile is not None]
    if not key:
        return ("—", 0)
    avg = round(sum(key) / len(key))
    letter = ("A+" if avg >= 85 else "A" if avg >= 72 else "B" if avg >= 58 else "C" if avg >= 42 else "D")
    return (letter, avg)


def team_dna_all(players, fixtures, *, next_n: int = 5, team_names=None, gw_history=None,
                 last_rows=None) -> dict:
    """`{team_short: TeamDNA}` for every team in the pool — each ranked across the league on the eight axes, with a
    grade. Compute-once (efficient for the "Your teams" strip). Never raises on zeros / blanks / preseason."""
    metrics = _team_metrics(players, fixtures, next_n=next_n)
    if not metrics:
        return {}
    names = team_names or {}
    cols = {k: [m[k] for m in metrics.values()] for k in
            ("attack", "create", "xga", "fixt", "setp", "output", "depth")}

    out = {}
    # ADR-128: the real clean-sheet rate, once gameweeks have been played. Falls back to the labelled
    # defence+fixtures proxy per team, so a club whose opener hasn't kicked off yet keeps the old estimate
    # rather than reading 0%.
    cs_rates = {t: team_clean_sheet_rate(gw_history, players, t) for t in metrics} if gw_history else {}
    rated = [v for v in cs_rates.values() if v is not None]

    # ADR-128 follow-up: "regulars" means ≥1500 minutes — about 17 matches — so for most of a season this
    # season cannot tell any two clubs apart, and every team reads the same number. Fall back to last season's
    # squad while that is true (the ADR-126 pattern), and hand the ranking back the moment this season can
    # separate anyone. Scaling the threshold to games played was measured and rejected: after one gameweek it
    # sorts 20 clubs into 5 buckets and still reads 0 for a club yet to kick off — a weak signal that *looks*
    # like a real one, which is the failure mode this project keeps choosing against.
    depth_label, depths = "regulars", {t: m["depth"] for t, m in metrics.items()}
    if len(set(depths.values())) <= 1 and last_rows:
        by_team: dict = {}
        for r in last_rows:
            team = _get(r, "team")
            if team in metrics:
                by_team[team] = by_team.get(team, 0) + (1 if _f(_get(r, "minutes")) >= REGULAR_MINUTES else 0)
        if len(set(by_team.values())) > 1:
            depth_label, depths = "last season", by_team
    depth_col = list(depths.values())

    for t, m in metrics.items():
        d_pct = _rank(m["xga"], cols["xga"], invert=True)
        f_pct = _rank(m["fixt"], cols["fixt"], invert=True)
        rate = cs_rates.get(t)
        if rate is not None and len(rated) > 1:
            cs_label, cs_value, cs_pct = "actual", round(rate * 100), _rank(rate, rated)
        else:
            cs_label, cs_value = "def + fix", round(m["xga"], 1)
            cs_pct = round(((d_pct or 0) + (f_pct or 0)) / 2)        # defence AND opponent difficulty
        axes = [
            Axis("Attacking Threat", "team xG", round(m["attack"], 1), _rank(m["attack"], cols["attack"])),
            Axis("Chance Creation", "team xA", round(m["create"], 1), _rank(m["create"], cols["create"])),
            Axis("Defensive Strength", "team xGA", round(m["xga"], 1), d_pct),
            Axis("Clean-Sheet Potl", cs_label, cs_value, cs_pct),
            Axis("Fixture Strength", "next-5 FDR", round(m["fixt"], 2), f_pct),
            Axis("Set-Piece Threat", "SP takers", round(m["setp"], 1), _rank(m["setp"], cols["setp"])),
            Axis("FPL Output", "team pts", round(m["output"]), _rank(m["output"], cols["output"])),
            Axis("Squad Depth", depth_label, depths.get(t, m["depth"]),
                 _rank(depths.get(t, m["depth"]), depth_col)),
        ]
        grade, score = _grade(axes)
        out[t] = TeamDNA(team=t, name=names.get(t, t), axes=axes, grade=grade, grade_score=score)
    return out


def team_dna(team, players, fixtures, *, next_n: int = 5, team_names=None, gw_history=None,
             last_rows=None) -> TeamDNA | None:
    """One team's `TeamDNA` (the single-team convenience over `team_dna_all`). None if the team isn't in the pool."""
    return team_dna_all(players, fixtures, next_n=next_n, team_names=team_names,
                        gw_history=gw_history, last_rows=last_rows).get(team)


def team_insights(dna) -> list[Insight]:
    """Grounded insights for a `TeamDNA`: top attacking/output strengths, a miserly-defence note, the fixture swing,
    a set-piece-loaded note. Reuses the player insight kinds (good ✓ · sp ⚡ · info ℹ · warn ⚠). Capped at 4."""
    if dna is None:
        return []
    by = {a.label: a for a in dna.axes}
    out: list[Insight] = []

    skills = sorted((a for a in dna.axes if a.label in _SKILL_AXES and a.percentile is not None),
                    key=lambda a: a.percentile, reverse=True)
    for a in skills[:2]:
        if a.percentile >= 80:
            out.append(Insight("good", f"Elite {a.label.lower()} — top {max(1, 100 - a.percentile)}% of the league"))

    dfc = by.get("Defensive Strength")
    if dfc and dfc.percentile is not None and dfc.percentile >= 75:
        out.append(Insight("good", f"Miserly defence (xGA {dfc.value:g}) — clean-sheet upside for its defenders"))

    fix = by.get("Fixture Strength")
    if fix and fix.percentile is not None:
        if fix.percentile >= 80:
            out.append(Insight("info", "One of the softest fixture runs (next 5) — a window to target its assets"))
        elif fix.percentile <= 40:
            out.append(Insight("warn", "A tough next-5 run — its assets may dip; watch the fixture swing"))

    sp = by.get("Set-Piece Threat")
    if sp and sp.percentile is not None and sp.percentile >= 85:
        out.append(Insight("sp", "Loaded with set-piece threat (penalty + dead-ball takers)"))

    return out[:4]
