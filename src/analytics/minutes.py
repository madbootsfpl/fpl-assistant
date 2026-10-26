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

# ⭐ **The single definition of "cannot play at all"** (ADR-206). It lived in three places that disagreed:
# here without `"n"`, in `optimizer.UNAVAILABLE_STATUS` with it, and — crudest and most damaging — in
# `xp._status_is_active`, which counted **only** `"a"` and so zeroed every doubtful player outright.
# `optimizer` re-exports this, so its sixteen call sites are untouched.
#
# ⚠️ `"n"` (not in the squad) is now included here, which it was not before: without it `chance_factor`
# returned **1.0** for an unregistered player, because his `chance` is None and None means "no news, assume
# available". No `"n"` rows exist today, so this closes a hole rather than changing a number.
UNAVAILABLE = frozenset({"i", "s", "u", "n"})   # injured / suspended / unavailable / not in squad

_MINUTES_SEASONS = 3                         # recent seasons to gauge a typical minutes share
_FULL_SEASON_MINUTES = 38 * 90               # a full Premier League season of minutes
_FULL_GAME_MINUTES = 90                      # one match, for the in-season share (ADR-173)
_WINDOW_GAMEWEEKS = 5                        # the rolling window the in-season guard judges (ADR-372)
_FORGIVEN_MISSES = 1                         # misses forgiven, but only once that window is full

#: ⭐⭐ **The share of the board the in-season term must keep answering for** (ADR-373). Not a tuning knob
#: and not arbitrary: **0.205 is what ADR-173's rule had decayed to at the moment it was replaced** — so if
#: the rolling window ever does *worse* than the all-or-nothing rule it replaced, the window is not working.
#: ⚠️ A floor derived from a measured fact, pre-registered before it can be breached.
REACH_FLOOR = 0.205


def _field(row, key):
    """Read `key` from a sqlite Row or a dict, returning None if absent (mirrors xp._get)."""
    try:
        return row[key]
    except (KeyError, IndexError):
        return None


def is_unavailable(player) -> bool:
    """True when the player cannot feature at all — a different question from *how likely* he is to (ADR-206).

    ⭐ **The gate answers "can he play?"; `chance_factor` answers "how likely is he to play?"** Keeping those
    two separate is the whole of ADR-206: they had been collapsed into one binary in `xp`, and the binary won —
    so a 75% doubt and a 25% doubt both priced at exactly zero.
    """
    return _field(player, "status") in UNAVAILABLE


def chance_factor(player) -> float:
    """How available a player is next round, in [0, 1] (ADR-038).

    Status is the reliable gate — a suspended player shows `chance_of_playing = None`, so
    injured/suspended/unavailable are zeroed by *status*. Otherwise `chance% / 100`, and a
    `None` chance (FPL's "no news") means assume available.
    """
    if is_unavailable(player):
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
    # ⚠️ **Rows with no minutes are absence of evidence, not evidence of absence** (found 2026-09-01).
    # A player promoted with his club carries stored seasons for years he spent outside the league — Thomas
    # has four, all zero. Averaging those gives share 0.0, i.e. "never plays", for someone who has started
    # every game this season. That is the opposite of what an empty history means two lines above, where the
    # same ignorance returns None and the module's own rule applies: *never penalise the unknown*.
    # `fallback_rate` already draws exactly this line (`if total_min <= 0: return None`); the minutes half
    # had not. It stayed invisible while the shrink prior escaped the weight and quietly restored the points
    # a 0.0 share had taken away — two bugs cancelling, until ADR-172's amendment removed one of them.
    #
    # **The test is the WHOLE history, not the k-season window, and that distinction is the whole rule.**
    # Three empty seasons *after* a full one is real evidence — a player who stopped playing — and must
    # still give 0.0. Never having played at all is the absence of evidence. Minutes alone cannot tell a
    # benching from a season spent outside the league, so the only honest cut is: have we *ever* seen him
    # play? A blanket check on the window would have rescued the decline case too, and a pre-existing test
    # said so.
    if sum((_field(h, "minutes") or 0) for h in history) <= 0:
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


def completed_gameweeks(gw_history_by_code) -> set:
    """The rounds that have actually **finished**, league-wide — a scoreline is the only proof.

    Never row presence and never `minutes == 0`: FPL writes a player's per-gameweek row when the fixture is
    *scheduled*, so a 0 there can mean "has not kicked off yet" (ADR-125/129). Reading that as "did not play"
    would libel every player at every club whose gameweek is in flight — the trap ADR-125 recorded and
    `yet_to_play` (ADR-138) already solved. This is the same test, hoisted so more than one caller can use it.
    """
    return {_field(r, "round")
            for rows in (gw_history_by_code or {}).values() for r in rows
            if _field(r, "round") is not None
            and _field(r, "team_h_score") is not None and _field(r, "team_a_score") is not None}


def in_season_share(player, gw_history_by_code, completed=None):
    """The share of available minutes he has **actually played** — or None when we cannot say (ADR-173/372).

    Judged on the **last `_WINDOW_GAMEWEEKS` completed gameweeks**, forgiving up to `_FORGIVEN_MISSES` of
    them — "played at least 4 of the last 5". Returns None for anything short of that, and **None means
    unchanged**: the caller keeps his historical share.

    ADR-173's refusal of the ambiguous case is kept and is still the decision. ADR-125's objection is real —
    two gameweeks cannot tell a player rested once from one being phased out — so the forgiveness applies
    **only once the window is full**. Below five completed gameweeks this is bit-for-bit ADR-173's original
    rule: every completed gameweek, with minutes in each. ⭐ *A rule that forgives a miss out of a sample of
    two has not loosened a guard, it has removed one.*

    What changed is **the ratchet, not the refusal** (ADR-371). *"Every completed gameweek"* got stricter
    every week it survived — it refused **49% of players at GW2 and 78% by GW8**, trending to single digits
    by GW25, because one rest in August disqualified a player permanently. ⭐⭐ *A rule whose failure rate
    only ever rises is one that will eventually disqualify everybody*, and a term that answers for 2% of the
    board has switched itself off. A window forgets: Konsa's 0-minute GW1 stops counting against him once it
    rolls out, and he is judged on the five weeks he has just started.

    ⚠️⚠️ **The denominator is `len(recent)`, not `len(played)` — available minutes, not minutes he turned up
    for.** That is what the docstring's first line claims and it is also what makes the forgiveness safe: a
    forgiven miss still costs him `1/window` of the share. ⭐ *The window does not protect a rested starter
    by refusing to answer; it protects him by capping what one bad week can cost him.*

    What is left unambiguous is the case ADR-173 was built for: he has started recently, and last season's
    minutes are simply the wrong number for him. Calafiori carried **0.43** from an injury-hit season while
    playing **0.94** of the minutes available; Kinsky **0.18** while first choice.

    🔴 **A player whose club had a BLANK gameweek is now handled WORSE, not better, and this is the one
    regression the change ships with.** Under ADR-173 a missing row disqualified him outright and he fell
    back to history. Now it is a *forgiven miss* scored as a 0 against the available denominator — so a
    blank costs a nailed starter `1/window` of his share rather than nothing. No blanks have landed yet;
    ADR-173's caveat is unresolved and now has a second claimant. ⚠️ The fix is the same one it always was:
    *"every completed gameweek"* and *"every gameweek his club played"* are different questions, and nothing
    here asks the second one.
    """
    completed = completed_gameweeks(gw_history_by_code) if completed is None else completed
    if not completed:
        return None
    recent = sorted(completed)[-_WINDOW_GAMEWEEKS:]
    # Forgive only once the window is full — below that, `need == len(recent)` is ADR-173 exactly.
    need = len(recent) - _FORGIVEN_MISSES if len(recent) >= _WINDOW_GAMEWEEKS else len(recent)
    rows = {_field(r, "round"): r for r in ((gw_history_by_code or {}).get(_field(player, "code")) or [])}
    played = [rows[g] for g in recent if g in rows and (_field(rows[g], "minutes") or 0) > 0]
    if len(played) < need:
        return None                                   # missed too many, or was not on the sheet for them
    return min(1.0, sum(_field(r, "minutes") or 0 for r in played) / (len(recent) * _FULL_GAME_MINUTES))


def in_season_reach(players, gw_history_by_code, completed=None) -> tuple[int, int, bool]:
    """How much of the board the in-season term still speaks for — `(answered, eligible, below_floor)`.

    ⭐⭐ **ADR-372 fixed a term that was decommissioning itself, and nothing would have reported it if the
    fix stopped working.** ADR-173's guard refused 49% of players at GW2 and 78% by GW8 — a reach falling
    toward single digits — and the only reason anybody noticed was that an owner asked about one defender.
    ⭐ *A fix applied once is not a fix that stays applied*, and the cheapest response to a slow failure is a
    number that makes it loud.

    `eligible` counts players whose club has actually played. A player with no rows at all is not a refusal
    — he is a player we know nothing about, and no guard would help him.

    ⚠️ `below_floor` is **False until the window has filled**. Before then the reach is naturally high and
    falling (one completed gameweek qualifies anyone who played it), so a floor would fire on the ordinary
    shape of an opening month rather than on a fault.

    ⭐ **This is a report, not a table, and the difference is the point.** ADR-203 had to *store* availability
    as it passed because FPL serves it as a now-field that cannot be backfilled. The reach can be recomputed
    from stored history for any round at any time — so recording it would be keeping a second copy of a
    derivable number. *The same lesson does not imply the same mechanism.*
    """
    completed = completed_gameweeks(gw_history_by_code) if completed is None else completed
    eligible = [p for p in (players or [])
                if ((gw_history_by_code or {}).get(_field(p, "code")) or [])]
    answered = [p for p in eligible
                if in_season_share(p, gw_history_by_code, completed) is not None]
    settled = len(completed) >= _WINDOW_GAMEWEEKS
    below = bool(eligible) and settled and (len(answered) / len(eligible)) < REACH_FLOOR
    return len(answered), len(eligible), below


def minutes_weight_from_history(history_by_code, gw_history_by_code=None):
    """A `player → [0, 1]` closure for `player_xp(minutes_weight=…)`, from stored history.

    Looks each player's past seasons up by `code` (element_code) in `history_by_code`
    (as `Storage.get_history_by_code()` returns) and applies `availability_weight`. The
    decision layer builds this once and passes it default-on; `--no-xmins` passes None.
    """
    completed = completed_gameweeks(gw_history_by_code) if gw_history_by_code else set()

    def weight(player) -> float:
        # ADR-173 — what he has played this season beats what he played last, but only where there is no
        # doubt. `in_season_share` returns None for every ambiguous case, and None means "unchanged".
        share = in_season_share(player, gw_history_by_code, completed) if completed else None
        if share is not None:
            return chance_factor(player) * share
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
