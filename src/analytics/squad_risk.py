"""Squad triage and a squad-level grade (ADR-130) — what to worry about, and how the 15 look together.

Two questions the app could not answer. **My Squad ▸ Health** said how good a squad was; it did not say what
needed attention *this week*, which is the question a manager opens the app with.

Pure, Row/dict safe, and built entirely from engines that already exist — xMins (ADR-038), Player DNA
(ADR-118), Team DNA (ADR-119) and the shared percentile (ADR-127). No new analytics, no `decision_xp` change.

The one number that is genuinely new is the chance a player fails to reach **60 minutes** — the FPL
appearance-points threshold. It is measured, never modelled: from his own per-gameweek record once there is
enough of one, otherwise from how often he *started* last season. Where there is no basis at all it returns
**None**, and the caller shows "—". A player new to the league is not a certainty to be substituted; we simply
do not know, and saying so is the whole point.
"""

from src.analytics.fdr import team_fdr
from src.analytics.minutes import chance_factor
from src.analytics.ranking import percentile_rank

APPEARANCE_MINUTES = 60     # FPL's second appearance point — the threshold worth measuring against
MIN_GAMEWEEKS = 4           # below this, one bad week would dominate an empirical rate (the ADR-101 bar)
# How the two risks combine into one attention score. Not equal: a player who doesn't play scores nothing,
# while a hard run only shortens the odds — so minutes dominates and fixtures modulates.
_MINUTES_WEIGHT, _FIXTURE_WEIGHT = 0.7, 0.3
_SEASON_GAMES = 38


def _get(row, key):
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return None


def _f(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _played(row) -> bool:
    """A gameweek that actually happened — judged on the scoreline, never on row presence (ADR-125/129)."""
    return _get(row, "team_h_score") is not None and _get(row, "team_a_score") is not None


def minutes_risk(player, gw_history=None, history=None, *, min_gameweeks: int = MIN_GAMEWEEKS):
    """The chance this player does **not** reach 60 minutes, 0.0-1.0 — or `None` when we cannot say.

    Returns `(risk, basis)` where `basis` is `"record"`, `"last season"` or `None`, so the caller can show
    which evidence it is standing on rather than presenting two different things as one number.

    * **`record`** — his own per-gameweek minutes, once he has `min_gameweeks` played. The honest measure, and
      only possible because per-gameweek minutes are now stored per *fixture* (ADR-129).
    * **`last season`** — `starts / 38`. A start almost always goes the distance (87-92 minutes per start for
      regulars on the live data), so starting is a sound proxy for clearing the threshold.
    * **`None`** — no per-gameweek record and no last season. New to the league. Not a risk of 100%; an
      unknown, and the caller must render it as one.

    Either basis is scaled by `chance_factor` (ADR-038), so an injury flag raises the risk.
    """
    fit = chance_factor(player)
    rows = [r for r in ((gw_history or {}).get(_get(player, "code")) or []) if _played(r)]
    if len(rows) >= min_gameweeks:
        reached = sum(1 for r in rows if (_get(r, "minutes") or 0) >= APPEARANCE_MINUTES)
        return max(0.0, 1.0 - (reached / len(rows)) * fit), "record"

    seasons = (history or {}).get(_get(player, "code")) or []
    if seasons:
        latest = seasons[-1]
        starts = _get(latest, "starts")
        if starts is not None:
            return max(0.0, 1.0 - min(1.0, starts / _SEASON_GAMES) * fit), "last season"
    return None, None


def fixture_risk_by_team(upcoming, *, next_n: int = 5) -> dict:
    """`{team: 0.0-1.0}` — how hard each club's next-`next_n` run is **relative to the league**.

    Relative on purpose. An absolute scale off the raw difficulty returns roughly the same middling number for
    almost every club (the league-typical average is ~3.2), so "Fixtures" would win as a player's headline
    driver while saying nothing. A percentile only flags a run that is genuinely hard *compared with everyone
    else's* — which is the only sense in which a fixture run is a reason to act.
    """
    ranked = team_fdr(upcoming, next_n=next_n)
    diffs = [r["avg_difficulty"] for r in ranked if r["avg_difficulty"] is not None]
    return {r["team"]: (percentile_rank(r["avg_difficulty"], diffs) or 50) / 100.0
            for r in ranked if r["avg_difficulty"] is not None}


def squad_risk_rows(owned, upcoming, *, gw_history=None, history=None, next_n: int = 5) -> list[dict]:
    """One row per owned player, **most in need of attention first** (ADR-130).

    Sorted by how much you might regret holding him, not by how good he is — a triage list, not a ranking. Each
    row carries the two risks, the larger of them as the **driver**, and the basis behind the minutes figure.

    A player whose minutes cannot be assessed is not treated as maximum risk: his attention comes from his
    fixtures alone and `minutes_basis` is None, so the caller can mark him unassessed.
    """
    fixt = fixture_risk_by_team(upcoming, next_n=next_n)
    rows = []
    for p in owned:
        mins, basis = minutes_risk(p, gw_history, history)
        f = fixt.get(_get(p, "team"), 0.5)
        # The two risks are NOT on the same scale, so they are weighted rather than compared directly.
        # `minutes_risk` is a probability — the chance he fails to reach 60. `fixture_risk` is a percentile —
        # how hard his run is *relative to the league*. Taking the larger of the two let an ordinary-but-
        # above-median run (79th percentile) swamp every player-level signal, so eight players scored an
        # identical 0.79 and the list sorted by club instead of by who needed attention.
        #
        # Minutes carries the heavier weight because the failures differ in kind: a player who does not play
        # scores nothing at all, while a hard fixture only shortens the odds on a return.
        m_part = _MINUTES_WEIGHT * mins if mins is not None else 0.0
        f_part = _FIXTURE_WEIGHT * f
        rows.append({
            "id": _get(p, "id"), "web_name": _get(p, "web_name"), "team": _get(p, "team"),
            "position": _get(p, "position"),
            "minutes_risk": mins, "minutes_basis": basis, "fixture_risk": f,
            "driver": "Minutes" if m_part > f_part else "Fixtures",
            "attention": round(m_part + f_part, 3),
        })
    rows.sort(key=lambda r: -r["attention"])
    return rows


def _mean(values):
    vals = [v for v in values if v is not None]
    return round(sum(vals) / len(vals)) if vals else None


def squad_dna(owned, dna_by_id=None, team_dna_by_team=None) -> dict:
    """The owned 15 as one graded picture: four bars, a grade, and grounded edge lines (ADR-130).

    Deliberately an **average of percentiles the engines already produce** rather than a new squad-level
    ranking. There is no pool of other people's squads to rank against, and inventing a distribution would be
    a percentile with nothing behind it. `dna_by_id` is `{player id: PlayerDNA}`, `team_dna_by_team` is
    `{team: TeamDNA}`; both may be partial and any missing player simply doesn't contribute.

    The grade uses `team_dna.grade_letter`, so a squad's B and a club's B mean the same thing.
    """
    from src.analytics.team_dna import grade_letter

    def player_axis(*labels):
        vals = []
        for p in owned:
            dna = (dna_by_id or {}).get(_get(p, "id"))
            for ax in (getattr(dna, "axes", None) or []):
                if ax.label in labels and ax.percentile is not None:
                    vals.append(ax.percentile)
        return _mean(vals)

    def team_axis(label):
        seen, vals = set(), []
        for p in owned:
            team = _get(p, "team")
            if team in seen:
                continue                      # one vote per club, not per player at that club
            seen.add(team)
            dna = (team_dna_by_team or {}).get(team)
            for ax in (getattr(dna, "axes", None) or []):
                if ax.label == label and ax.percentile is not None:
                    vals.append(ax.percentile)
        return _mean(vals)

    bars = {
        "Attack": player_axis("Goal Threat", "Creativity"),
        "Output": player_axis("FPL Output"),
        "Defence": team_axis("Clean-Sheet Potl"),
        "Fixtures": team_axis("Fixture Strength"),
    }
    score = _mean(bars.values())
    return {"bars": bars, "grade": grade_letter(score) if score is not None else "—",
            "score": score or 0, "edges": squad_edges(owned)}


def squad_edges(owned) -> list[str]:
    """Grounded one-liners about the shape of a squad — each traceable to a count, never a vibe."""
    out = []
    pens = [p for p in owned if (_get(p, "penalties_order") or 9) == 1]
    if len(pens) >= 2:
        out.append(f"{len(pens)} first-choice penalty takers — a deliberate edge")
    by_team: dict = {}
    for p in owned:
        by_team[_get(p, "team")] = by_team.get(_get(p, "team"), 0) + 1
    heavy = sorted((n, t) for t, n in by_team.items() if n >= 3)
    if heavy:
        n, t = heavy[-1]
        out.append(f"{n} players from {t} — a strong lean, and a blank gameweek hits all of them")
    prem = [p for p in owned if _f(_get(p, "price")) >= 9.0]
    if len(prem) >= 4:
        out.append(f"{len(prem)} premiums at £9.0m+ — little left for the bench")
    return out[:3]
