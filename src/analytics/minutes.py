"""Expected minutes (xMins) v0 — weight a player's xP by how likely they are to play.

Lightweight and FPL-native (ADR-038): no ML, no new dependency. The weight is
`chance_factor × minutes_share`, each in [0, 1]:

  chance_factor — FPL's `chance_of_playing% / 100`; `None` → 1.0 ("no news, assume
                  available"); status i/s/u (injured/suspended/unavailable) → 0.0
                  (suspended players carry no 0 chance, so *status* is the reliable gate).
  minutes_share — a recency-weighted mean of `minutes / (38 × 90)` over the recent seasons
                  we hold; minutes-only (`starts` is unreliable pre-2022/23, ADR-038); no
                  900-minute gate (here small minutes *should* lower the weight); no history
                  → 1.0 (never penalise the unknown).

Applied at the decision edge (captain/transfer/analyse/`ask`), it demotes rotation risks
below nailed-on starters. The raw `xp` view stays a pure "assumes they play" number. The
full probabilistic model (congestion, rotation profiles, in-season minutes) is Phase 5.
"""

_UNAVAILABLE = frozenset({"i", "s", "u"})   # injured / suspended / unavailable → won't feature
_MINUTES_SEASONS = 3                         # recent seasons to gauge a typical minutes share
_FULL_SEASON_MINUTES = 38 * 90               # a full Premier League season of minutes


def _field(row, key):
    """Read `key` from a sqlite Row or a dict, returning None if absent (mirrors xp._get)."""
    try:
        return row[key]
    except (KeyError, IndexError):
        return None


def chance_factor(player) -> float:
    """How available a player is next round, in [0, 1] (ADR-038).

    Status is the reliable gate — a suspended player shows `chance_of_playing = None`, so
    injured/suspended/unavailable are zeroed by *status*. Otherwise `chance% / 100`, and a
    `None` chance (FPL's "no news") means assume available.
    """
    if _field(player, "status") in _UNAVAILABLE:
        return 0.0
    chance = _field(player, "chance")
    if chance is None:
        return 1.0
    return max(0.0, min(1.0, chance / 100.0))


def minutes_share(history, k_seasons: int = _MINUTES_SEASONS):
    """A player's recency-weighted share of a full season's minutes, in [0, 1] (ADR-038).

    Minutes-only (`starts` is unreliable across seasons); newer seasons weigh more; each
    season's share is capped at 1.0. Returns None when we hold no history, so the caller
    treats the player as nailed-on rather than penalising missing data.
    """
    seasons = history[-k_seasons:]
    if not seasons:
        return None
    num = den = 0.0
    for rank, h in enumerate(seasons, start=1):   # oldest → 1 … newest → n (recency)
        share = min(1.0, (_field(h, "minutes") or 0) / _FULL_SEASON_MINUTES)
        num += rank * share
        den += rank
    return num / den if den else None


def availability_weight(player, history) -> float:
    """The xMins v0 weight in [0, 1]: `chance_factor × minutes_share` (ADR-038).

    No history → the minutes share defaults to 1.0 (nailed-on), so the weight is just the
    chance factor. Used at the decision edge to scale xP by expected playing time.
    """
    share = minutes_share(history)
    return chance_factor(player) * (1.0 if share is None else share)


def minutes_weight_from_history(history_by_code):
    """A `player → [0, 1]` closure for `player_xp(minutes_weight=…)`, from stored history.

    Looks each player's past seasons up by `code` (element_code) in `history_by_code`
    (as `Storage.get_history_by_code()` returns) and applies `availability_weight`. The
    decision layer builds this once and passes it default-on; `--no-xmins` passes None.
    """
    def weight(player) -> float:
        return availability_weight(player, history_by_code.get(_field(player, "code"), []))
    return weight


def expected_minutes(weight) -> int:
    """A [0, 1] weight as whole expected minutes next GW (e.g. 0.62 → 56) — for display."""
    return round((weight or 0.0) * 90)


def yet_to_play(player, gw_history_by_code) -> bool:
    """Has this player's team completed a gameweek that he played **no part in**? (ADR-138)

    Three states, and telling them apart is the whole function:

    * **He played** → `False`. There is evidence, and it is good.
    * **His team played and he did not** → `True`. That *is* evidence — of a bench role, a rotation, or a
      manager's opinion — and it is the state the xMins weight is currently blind to, because the in-season
      minutes share is deferred until there are enough gameweeks to trust (ADR-125).
    * **His team has not played yet** → `False`. We know nothing, and saying nothing is correct.

    A gameweek counts as completed only when it has a **scoreline** — never on row presence, and never on
    `minutes == 0` alone. FPL writes a player's per-gameweek row when the fixture is *scheduled*, so a 0 there
    can mean "has not kicked off yet" (ADR-125/129). Reading that as "didn't play" would libel every player at
    every club whose gameweek is still in flight.

    This is a **flag, not a correction**: it does not touch xP. It exists so a surface can say what the number
    is standing on — a strong last-season record and no minutes since — and let the manager judge.
    """
    code = _field(player, "code")
    rows = [r for r in ((gw_history_by_code or {}).get(code) or [])
            if _field(r, "team_h_score") is not None and _field(r, "team_a_score") is not None]
    if not rows:
        return False                                     # his team has not played — no basis for an opinion
    return sum(_field(r, "minutes") or 0 for r in rows) == 0
