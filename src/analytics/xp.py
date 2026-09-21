"""Expected Points (xP) — the first *cross-domain* metric.

xP joins two threads: a player's scoring rate (`points_per_game`) and their team's
fixture difficulty. The link is `team_id` — a player belongs to a team, a team has
fixtures, each fixture has a difficulty (reusing the FDR `_view` seam).

Formula (ADR-006): per fixture, xP = points_per_game × (1 + (3 − difficulty) × 0.10),
or 0 if the player isn't available. Over a horizon of the next N gameweeks, we sum the
per-fixture xP (ADR-007) — so a double gameweek (two fixtures in one gameweek) adds up.
"""

from datetime import datetime, timezone

from src import config
from src.analytics.cleansheet import clean_sheet_delta, clean_sheet_prob, league_clean_sheet_rate
from src.analytics.defcon_xp import defcon_magnifier, defcon_points_per_match
from src.analytics.fdr import _view
from src.analytics.form import blend_form, form_rate
from src.analytics.gw_form import team_xgc90
from src.analytics.minutes import chance_factor, is_unavailable, minutes_weight_from_history

_K = 0.10   # fixture weighting: ±20% at the extremes (ADR-006)
_BASELINE_SEASONS = 3    # multi-season look-back for the xP baseline (ADR-028)
# A season needs ~10 full games before its points-per-90 is trustworthy — otherwise a
# tiny cameo (e.g. 2 pts in 20 mins → pp90 9.0+) invents an absurd rate. Same minutes
# gate the over/under and DefCon views use (ADR-017/018); the Sprint 016 Meslier lesson.
_MIN_SEASON_MINUTES = 900
# A replacement-level pp90 (ADR-040): the fallback for a player with no qualifying baseline shrinks
# toward this. Pinned below the p10 (~2.9) of 900-minute regulars — sub-threshold players are weaker.
_FALLBACK_PRIOR = 2.0


def _get(row, key):
    """Read `key` from a sqlite Row or a dict, returning None if it's absent.

    Lets player_xp accept both real rows (which have `code`) and lightweight test
    dicts (which may not) without a KeyError.
    """
    try:
        return row[key]
    except (KeyError, IndexError):
        return None


def baseline_rate(
    history, k_seasons: int = _BASELINE_SEASONS, min_minutes: int = _MIN_SEASON_MINUTES
):
    """A multi-season points-per-90 baseline for one player (ADR-028).

    Recency- and minutes-weighted over the last `k_seasons` seasons that clear
    `min_minutes` (a small sample invents an absurd rate — see the gate above), using
    only the fields ADR-027 confirmed reliable across seasons (points + minutes).
    Returns None when no season qualifies (young/fringe player), so the caller can
    fall back to the current single-season rate.
    """
    seasons = [h for h in history if (h["minutes"] or 0) >= min_minutes][-k_seasons:]
    if not seasons:
        return None
    num = den = 0.0
    for rank, h in enumerate(seasons, start=1):   # oldest → 1 … newest → n (recency)
        pp90 = h["total_points"] * 90.0 / h["minutes"]
        weight = rank * h["minutes"]              # newer + higher-minutes seasons weigh more
        num += weight * pp90
        den += weight
    return num / den


def fallback_rate(history, prior: float = _FALLBACK_PRIOR):
    """A damped scoring rate for a player with no qualifying baseline (ADR-040).

    When no season clears the ≥900-min gate, projecting raw `points_per_game` lets a one-game
    cameo (Benitez: 90 min, 7 pts → ppg 7.0) rank like a star. Instead, shrink the player's
    **career** pp90 toward a replacement-level `prior` by how much evidence we have:

        rate = career_pp90 × c + prior × (1 − c),   c = min(1, best_season_minutes / 900)

    Confidence comes from the player's **biggest single season**, not the career sum — scattered
    cameos must not *compound* to false confidence (the Enes Ünal case: 317+330+214 min at ~10 pp90
    would otherwise trust a flukey rate). So Benitez (best 90 min, c ≈ 0.1) and Enes Ünal (best 330,
    c ≈ 0.37) both shrink toward the prior, while one real ≥900-min season (c → 1) keeps ~its own
    rate. Returns None with no history — the caller then falls back to the current `points_per_game`.
    """
    total_min = sum((h["minutes"] or 0) for h in history)
    if total_min <= 0:
        return None
    total_pts = sum((h["total_points"] or 0) for h in history)
    career_pp90 = total_pts * 90.0 / total_min
    best_season_min = max((h["minutes"] or 0) for h in history)
    c = min(1.0, best_season_min / _MIN_SEASON_MINUTES)
    return career_pp90 * c + prior * (1.0 - c)


def cold_start_rate(points_per_game, ep_next, minutes, weight: float = 1.0,
                    min_minutes: int = _MIN_SEASON_MINUTES, prior: float = _FALLBACK_PRIOR) -> float:
    """A scoring rate for a player with **no history at all**, shrunk toward `ep_next` by evidence (ADR-124).

        rate = (weight × points_per_game) × c + ep_next × (1 − c),   c = min(1, minutes / min_minutes)

    Same shape as `fallback_rate`, for the one tier ADR-040 could not reach: with no past seasons there was no
    career rate to shrink, so this branch used to take `max(ep_next, points_per_game)` (ADR-104). That is a switch
    on the *value*, and after one game `points_per_game` **is** that game's score — so a 14-point opener projected
    at 14 a week and out-ranked every established player in the game. Preseason it could not misbehave
    (`points_per_game` was 0, so `ep_next` always won); real data is what activated it.

    Switching on the *evidence* instead makes the two old tiers the two ends of one curve, and both ends keep
    their old behaviour exactly:

      * `minutes = 0` → `c = 0` → `rate = ep_next`. FPL derives `points_per_game` from games played, so no
        minutes means no points-per-game: the old `ep_next` tier *was* the zero-evidence case, not merely similar
        to it. This is ADR-104, unchanged.
      * `minutes ≥ min_minutes` (~10 full games — the bar `baseline_rate` already trusts) → `c = 1` →
        `rate = weight × points_per_game`. The old `current` tier, unchanged.

    Only the middle is new, and it converges: a genuine 6.0-ppg signing reaches their real rate by ~game 10,
    while a one-game fluke that reverts is damped the whole way.

    `weight` (the xMins minutes weight) scales the `points_per_game` term **only** — `ep_next` is FPL's own
    expected points for the next gameweek and already prices minutes, so discounting it again would double-count
    (ADR-104). The caller therefore passes 1.0 as the outer weight; see `player_xp`.

    ⚠️ **ADR-172 — a shrink needs something to shrink toward.** The blend above assumes its two inputs are
    independent. Upstream they are not: FPL currently publishes `ep_next` **equal to `points_per_game`** for
    513 of 626 players, and blending a number with itself returns it —

        ppg × c + ppg × (1 − c)  =  ppg      at *every* value of c

    — so the evidence weighting cancelled and this function returned raw `points_per_game`, which is exactly the
    failure it was written to prevent. Sangaré, two games in, projected **9.9 xP**; 8 of the top 20 were on this
    tier and the top 3 were all of it, with Haaland 4th.

    So when `ep_next` carries **no information about this player beyond what `ppg` already says**, shrink toward
    the replacement `prior` instead — the same `_FALLBACK_PRIOR` that `fallback_rate` (ADR-040) already shrinks
    thin evidence toward. No new constant: the one tier that could not reach it now does.

    **The `ppg > 0` half of the test is load-bearing, not defensive.** Preseason `ppg` is 0 and `ep_next` is
    often 0 too, so a bare equality check would fire on the zero-evidence case and hand a player who has never
    kicked a ball the replacement prior instead of FPL's 0. That would re-break ADR-104, which this ADR is
    restoring. With the guard, both ends survive untouched:

      * `minutes = 0` → `c = 0` → `rate = ep_next` (ADR-104, unchanged — `ppg` is 0 so the test cannot fire)
      * `minutes ≥ min_minutes` → `c = 1` → `rate = weight × ppg` (unchanged either way)

    And it **self-repairs**: the day FPL publishes a real `ep_next`, the equality stops holding and the shrink
    goes back to using it, with no constant to remember to revert.
    """
    ppg = float(points_per_game or 0)
    ep = float(ep_next or 0)
    c = min(1.0, max(0.0, (minutes or 0) / min_minutes))
    # Equality is a heuristic for "this tells us nothing new", and it is allowed to be: on a coincidence the
    # player is still a low-evidence cold start, so the conservative branch is the right answer anyway.
    if ep == ppg and ppg > 0:
        # ⚠️ **The whole blend carries the weight here, and that is the difference that matters.** ADR-104's
        # rule — do not discount the far term by minutes — is a fact about **`ep_next`**, which is FPL's
        # *expected points for the next gameweek* and has already priced minutes in. `prior` is not that
        # kind of number: it is a **points-per-90 rate**, the same one `fallback_rate` shrinks toward, and a
        # rate becomes points only when multiplied by expected minutes. ADR-172's first cut swapped the
        # target and kept the rule, which left the identical prior minutes-scaled in the `fallback` tier and
        # unscaled here — the same player halving to 48% of his xP on one path and 76% on the other.
        return weight * (ppg * c + prior * (1.0 - c))
    # `ep_next` already prices minutes, so only the `ppg` term is discounted (ADR-104, unchanged).
    return weight * ppg * c + ep * (1.0 - c)


def apportion(unrounded: dict, total: float, places: int = 1) -> dict:
    """Round each value so the parts **sum to `total` exactly** (largest-remainder / Hamilton).

    ⭐⭐ **The obvious version is wrong, and shipped that way for months.** `by_gameweek` rounded each
    gameweek independently while `xp` rounded the *sum* — and a rounded sum is not a sum of rounded values.
    Measured on the real board at horizon 5: **253 of 662 players** disagreed with their own breakdown, by up
    to **0.20 points**. The comment beside the field said *"sums to `xp`"*, which is the claim this restores
    rather than a new promise.

    ⚠️ It matters beyond display. ADR-213 publishes this board for clients that cannot run Python, and a
    client summing a rounded breakdown to get a shorter horizon would inherit the drift — so the web app and
    the mobile app would quote **different xP for the same player**.

    The method: floor everything, then hand the spare tenths to the largest fractional parts (ties broken by
    key, so the result is deterministic). No value moves more than one unit in the last place.
    """
    if not unrounded:
        return {}
    scale = 10 ** places
    target = round(total * scale)
    floors = {k: int(unrounded[k] * scale // 1) for k in unrounded}
    short = target - sum(floors.values())
    # Largest fractional part first; the key breaks ties so two runs never differ.
    order = sorted(unrounded, key=lambda k: (-(unrounded[k] * scale - floors[k]), k))
    for k in order[:max(short, 0)]:
        floors[k] += 1
    for k in order[len(order) + min(short, 0):]:      # short < 0 → take tenths back from the smallest
        floors[k] -= 1
    return {k: floors[k] / scale for k in unrounded}


def _multiplier(difficulty) -> float:
    """Turn a 1-5 difficulty into a scoring multiplier (neutral at 3, or if unknown)."""
    if difficulty is None:
        return 1.0
    return 1 + (3 - difficulty) * _K


def _horizon_gameweeks(upcoming, gameweeks: int) -> list[int]:
    """The next `gameweeks` gameweek numbers present in `upcoming`, in order."""
    events = sorted({f["event"] for f in upcoming if f["event"] is not None})
    return events[:gameweeks]


def _difficulties_by_team_gw(upcoming, source: str, horizon_events) -> dict:
    """Map team_id → {gameweek → [fixture difficulties]} within the horizon.

    Grouping by gameweek (not a flat list) is what lets xP split per GW (ADR-032): a
    double gameweek gives two entries in one GW, a blank gameweek gives none — the same
    DGW/BGW handling as ADR-007, now visible per week.
    """
    horizon = set(horizon_events)
    by_team_gw: dict = {}
    for f in upcoming:
        if f["event"] not in horizon:
            continue
        for team_id, team_short in ((f["team_h"], f["home"]), (f["team_a"], f["away"])):
            difficulty, _, _ = _view(f, team_short, source)
            by_team_gw.setdefault(team_id, {}).setdefault(f["event"], []).append(difficulty)
    return by_team_gw


def _first_kickoff_by_gw(upcoming) -> dict:
    """`{gameweek → earliest kickoff}` as an aware datetime, skipping fixtures with no time yet."""
    out: dict = {}
    for f in upcoming or []:
        ev, raw = _get(f, "event"), _get(f, "kickoff_time")
        if ev is None or not raw:
            continue
        try:
            when = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except ValueError:
            continue
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        if ev not in out or when < out[ev]:
            out[ev] = when
    return out


def _flag_reach(gw_kickoff, now, days):
    """`reach(gw) → bool`: is this gameweek close enough for an availability flag to be evidence about it?

    ⭐ **Measured in days, which is the whole of ADR-206 §3.** An international break needs no concept of its
    own — GW6 kicks off 19 days after GW5, so it simply falls outside the window.

    ⚠️ **Unknown kickoff → True (still in reach).** A fixture with no time yet is most often the *next* one,
    and reading "we don't know when" as "far away" would quietly un-flag a player before a match that might be
    tomorrow. ⭐ *When a guard's input is missing, fail toward the cautious reading, not the convenient one.*
    """
    now = now or datetime.now(timezone.utc)
    if isinstance(now, str):
        now = datetime.fromisoformat(now.replace("Z", "+00:00"))
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    def reach(gw) -> bool:
        when = gw_kickoff.get(gw)
        return True if when is None else (when - now).days <= days
    return reach


def _rate_tier(p, ppg, code, weight, baseline_by_code, history_by_code, form_by_code, form_weight):
    """`(rate, weight, applied_weight, rate_source)` for one player at one minutes-weight regime.

    Extracted from `player_xp`'s loop so it can be evaluated **twice** — once with the availability discount
    and once without (ADR-206 §2). Doing it this way rather than scaling the finished number is not fussiness:
    the `cold_start` tier carries the weight *inside* its rate, non-linearly, so dividing the output by the
    chance factor would be wrong for exactly the players who have least evidence.

    Rate tiers (ADR-028/040/124): a trusted ≥900-min baseline, else a low-evidence shrunk fallback (so a cameo
    can't project like a star), else the cold-start blend.
    """
    applied_weight = weight
    baseline = baseline_by_code.get(code)
    if baseline is not None:
        rate, rate_source = baseline, "hist"
    else:
        fb = fallback_rate(history_by_code.get(code, []))
        if fb is not None:
            rate, rate_source = fb, "fallback"
        else:
            # No history at all: shrink this season's points-per-game toward FPL's `ep_next` by how many
            # minutes back it (ADR-124). The blend carries the minutes weight on its `ppg` term, so the
            # outer weight must not apply it a second time — same guard ADR-104 already used for the
            # zero-evidence end of this curve, which this branch subsumes.
            _mins, _ep = _get(p, "minutes"), _get(p, "ep_next")
            rate = cold_start_rate(ppg, _ep, _mins, weight)
            rate_source = "cold_start"
            # Report the weight that actually landed: the blend discounts its `ppg` term only, so the
            # effective discount is weighted ÷ unweighted (1.0 when there is nothing to discount). Both
            # ends still read as they did before — 1.0 at zero evidence (ADR-104), `weight` at full.
            _unweighted = cold_start_rate(ppg, _ep, _mins, 1.0)
            applied_weight = (rate / _unweighted) if _unweighted else 1.0
            weight = 1.0                 # the weight is inside `rate` now — don't apply it twice
    # In-season form blend (ADR-060) — DORMANT: form_weight 0 (default) or no per-GW form for this player
    # ⇒ rate unchanged, so xP is identical today (the ADR-041 invariant holds).
    fr = form_by_code.get(code)
    if fr is not None and form_weight and rate is not None:
        rate = blend_form(rate, fr[0], fr[1], form_weight)
    return rate, weight, applied_weight, rate_source


def _status_is_active(p) -> bool:
    """Can this player feature at all? (ADR-206, replacing ADR-006's binary)

    ⚠️ **This was `p["status"] == "a"`, and it zeroed every DOUBTFUL player outright.** `chance_factor`
    (ADR-038) already computed the right multiplier — 0.75 for a 75% doubt — and never got the chance to
    apply it, because this ran first and returned False. A 75% doubt and a 25% doubt priced identically, at
    exactly zero: 23 players on the day this was found, including the joint-highest-scoring forward in the
    game at 74.5% ownership, whose 5-gameweek projection read `{0.0, 0.0, 0.0, 0.0, 0.0}`.

    ⭐⭐ **TWO MECHANISMS MODELLED THE SAME THING AND THE CRUDER ONE RAN FIRST**, so the finer one was dead
    code for exactly the population it was written for.

    ⭐ **ADR-006's reasoning had expired, not been wrong.** It justified the binary with *"`chance_of_playing`
    is barely populated, so `status` is the signal"* — true in preseason, when the column was empty. FPL now
    populates it (25/50/75), and nothing re-checked the premise. *A constraint recorded in an ADR is a fact
    about a version, not a law* (ADR-180).

    The split is now clean: **this answers "can he play?", `chance_factor` answers "how likely is he to?"**
    With `--no-xmins` a doubtful player scores his full rate, which is correct and deliberate — that view is
    documented as *"assumes they play"*, and for a player who genuinely cannot, the assumption is not
    counterfactual but meaningless, so `i`/`s`/`u`/`n` stay zeroed in both.
    """
    return not is_unavailable(p)


def player_xp(
    players, upcoming, source: str = "fpl", horizon: int = 1, baseline_by_code=None,
    is_available=None, minutes_weight=None, history_by_code=None, now=None,
    flag_horizon_days: int = config.FLAG_HORIZON_DAYS,
    form_by_code=None, form_weight: float = 0.0,
    defcon_weight: float = 0.0, clean_sheet_weight: float = 0.0, clean_sheet_rates=None,
) -> list[dict]:
    """Compute each player's expected points over the next `horizon` gameweeks.

    `players` are rows from Storage.get_players() (team_id, points_per_game, status,
    ep_next, web_name, position, team, code). `upcoming` is from get_upcoming_fixtures().

    The scoring **rate** is the multi-season historical baseline (ADR-028) when available
    — keyed by the player's `code` in `baseline_by_code` — else the current
    `points_per_game`. xP is the sum of per-fixture rate × fixture-multiplier over the
    horizon; 0 if the player is unavailable or has no rate at all. Sorted by xP, highest first.

    `is_available(player)` decides who scores (others → 0); it defaults to "status is 'a'".
    The captain view (ADR-029) passes a looser predicate so *doubtful* players still get an
    xP (to be suggested with a flag) rather than being zeroed.

    `minutes_weight(player)` (xMins v0, ADR-038) optionally scales xP by expected playing
    time — a continuous [0, 1] weight applied to the total and every per-GW cell. When
    absent (the raw `xp` view), xP is unchanged; the decision layer passes it default-on.
    """
    horizon_events = _horizon_gameweeks(upcoming, horizon)
    # ADR-206 §3 — earliest kickoff per gameweek, so a flag's reach is measured in days.
    gw_kickoff = _first_kickoff_by_gw(upcoming)
    reach = _flag_reach(gw_kickoff, now, flag_horizon_days)
    diff_by_team_gw = _difficulties_by_team_gw(upcoming, source, horizon_events)
    baseline_by_code = baseline_by_code or {}
    history_by_code = history_by_code or {}
    form_by_code = form_by_code or {}
    is_available = is_available or _status_is_active
    # ADR-188 — the league mean clean-sheet rate, computed once. Clubs with no played gameweeks are excluded
    # rather than counted as 0%, so the baseline is over what is known.
    league_cs = league_clean_sheet_rate(clean_sheet_rates)

    results = []
    for p in players:
        ppg = p["points_per_game"]
        code = _get(p, "code")
        # xMins v0 (ADR-038): scale by expected playing time; 1.0 (unchanged) without the hook. Computed up here
        # because the cold-start blend needs it for one of its two terms (ADR-124).
        weight = minutes_weight(p) if minutes_weight is not None else 1.0
        rate, weight, applied_weight, rate_source = _rate_tier(
            p, ppg, code, weight, baseline_by_code, history_by_code, form_by_code, form_weight)

        # ADR-206 §2/§3 — a doubt is evidence about the matches it was published for, not about November.
        # `far` is the same projection with the availability discount removed, used for gameweeks the flag
        # cannot reach. Identical to `near` for everyone unflagged, so this is a no-op for 636 of 659 players.
        far = None
        if minutes_weight is not None and 0.0 < chance_factor(p) < 1.0:
            far = _rate_tier(p, ppg, code, minutes_weight(p) / chance_factor(p),
                             baseline_by_code, history_by_code, form_by_code, form_weight)
        # 🚫 A set-piece rate bonus sat here (ADR-096) and was removed as unmeasurable (ADR-190). It could
        # only ever apply off the `hist` tier — 9 players, fixed for the season — which is both why it was
        # correct and why no whole-board metric could ever score it. Duty is still *shown* (crowd.SET_PIECES).
        available = is_available(p)
        gw_map = diff_by_team_gw.get(p["team_id"], {})
        # Fixtures flattened in gameweek order (for `games` and the next-fixture difficulty).
        flat = [d for gw in horizon_events for d in gw_map.get(gw, [])]

        if rate is None or not available:
            by_gameweek = {gw: 0.0 for gw in horizon_events}
            by_gameweek_exact = dict(by_gameweek)
            xp = 0.0
            defcon_xp = 0.0
            cs_xp = 0.0
        else:
            # Per-GW xP unrounded, so the total is exactly today's number (ADR-032);
            # per-GW cells are rounded only for display. The minutes weight scales both.
            # ADR-206 §2/§3 — pick the regime per gameweek: discounted where the flag is evidence,
            # undiscounted beyond its reach. `far is None` for everyone unflagged → `regime` is constant →
            # byte-identical to before (the invariance every guarded change here is held to).
            def regime(gw, _rate=rate, _weight=weight, _far=far):
                if _far is not None and not reach(gw):
                    return _far[0], _far[1]
                return _rate, _weight

            unrounded = {
                gw: regime(gw)[1] * regime(gw)[0] * sum(_multiplier(d) for d in gw_map.get(gw, []))
                for gw in horizon_events
            }
            # DefCon fixture magnifier (ADR-097) — a DELTA that re-weights the DefCon points already in the
            # baseline: 2·P(clear) · Σ(magnifier(d) − 1) per GW, minutes-weighted. 0 at weight 0 → xp
            # unchanged (invariance), no double-count. Folded into by_gameweek so it still sums to xp (ADR-032).
            defcon_pm = defcon_points_per_match(p)
            defcon_by_gw = {
                gw: regime(gw)[1] * defcon_weight * defcon_pm
                    * sum(defcon_magnifier(d) - 1.0 for d in gw_map.get(gw, []))
                for gw in horizon_events
            }
            # Clean-sheet term (ADR-188) — a DELTA, like DefCon above and for the same reason: the player's
            # own pts/90 already contains the clean sheets he kept at his old rate, so only the difference
            # between **this** club's rate and the league's is new information. DORMANT at weight 0 → every
            # cell 0 → xp unchanged (the ADR-041 invariant every dormant weight is held to).
            cs_pm = clean_sheet_delta(p, (clean_sheet_rates or {}).get(p["team"]), league_cs)
            cs_by_gw = {
                gw: regime(gw)[1] * clean_sheet_weight * cs_pm * len(gw_map.get(gw, []))
                for gw in horizon_events
            }
            unrounded = {gw: unrounded[gw] + defcon_by_gw[gw] + cs_by_gw[gw] for gw in horizon_events}
            xp = round(sum(unrounded.values()), 1)
            # ADR-213: apportioned, not rounded independently — the parts must sum to `xp`.
            by_gameweek = apportion(unrounded, xp)
            by_gameweek_exact = dict(unrounded)
            defcon_xp = round(sum(defcon_by_gw.values()), 1)
            cs_xp = round(sum(cs_by_gw.values()), 1)

        results.append({
            "id": p["id"],
            "web_name": p["web_name"],
            "team": p["team"],
            "position": p["position"],
            "xp": xp,
            "games": len(flat),                       # fixtures in the horizon (DGW → >horizon)
            "ep_next": p["ep_next"],
            "difficulty": flat[0] if flat else None,  # next fixture (for N=1 display)
            "rate": round(rate, 2) if rate is not None else None,
            "rate_source": rate_source,
            "by_gameweek": by_gameweek,               # ADR-032/213: {gw → xP}, sums to `xp` exactly
            # ⭐ **Unrounded, and emitted for EVERY caller rather than behind a flag** (ADR-213). This is what
            # the pipeline publishes, because a client deriving a shorter horizon must sum exact values —
            # summing the rounded ones drifts, and the web app and the mobile app would then disagree about
            # the same player. ⚠️ ADR-181's lesson is why it is not an optional argument: an opt-in on a
            # shared helper is a silent opt-out at every call site that forgets it.
            "by_gameweek_exact": by_gameweek_exact,
            # ⭐ Fixtures per gameweek. `games` is their sum over the horizon, but a **double gameweek is one
            # key with two fixtures** — so a client holding only `by_gameweek` cannot recover the count.
            # Published so the board is a faithful stand-in for this function rather than nearly one.
            "games_by_gameweek": {gw: len(gw_map.get(gw, [])) for gw in horizon_events},
            "gameweeks": list(horizon_events),
            "minutes_weight": round(applied_weight, 2),   # xMins v0 weight applied (1.0 without the hook)
            "defcon_xp": defcon_xp,                   # ADR-097: the DefCon magnifier's net delta (0 dormant)
            "clean_sheet_xp": cs_xp,                  # ADR-188: the club clean-sheet delta (0 dormant)
        })

    results.sort(key=lambda r: r["xp"], reverse=True)
    return results


def decision_xp(players, upcoming, history_by_code, *, source: str = "fpl", horizon: int = 5,
                minutes_weighted: bool = True, gw_history_by_code=None, now=None) -> list[dict]:
    """The single "decision xP" recipe shared by squad / analyse / transfer / ask (ADR-041).

    Assembles the *full* xP the tool acts on: the multi-season historical baseline + the
    low-evidence fallback (ADR-040), the xMins weight (ADR-038, unless `--no-xmins`), and — when
    live — an in-season **form** blend (ADR-060). One place, so the optimiser and the
    recommendations can't disagree on a player's xP.

    `gw_history_by_code` (from `Storage.get_gw_history_by_code()`) is the per-GW history for the
    form term. **Form is dormant until GW1:** preseason it's empty and `config.FORM_WEIGHT` is 0,
    so the rate — and every xP — is unchanged (an invariance test pins this). The GW1 flip is a
    backfill + raising `FORM_WEIGHT`; nothing else here changes.
    """
    baseline_by_code = {code: baseline_rate(rows) for code, rows in history_by_code.items()}
    # ADR-173 — the weight prefers minutes he has actually played this season, where that is
    # unambiguous; `gw_history_by_code` is the same per-GW data the form term below reads.
    weight = (minutes_weight_from_history(history_by_code, gw_history_by_code)
              if minutes_weighted else None)
    # form_by_code: code → (form_pp90, confidence); only players with a computable rate. Empty
    # preseason (no per-GW history) → no blend. Keyed by the same `code` the baseline uses.
    form_by_code = {
        code: fr
        for code, rows in (gw_history_by_code or {}).items()
        if (fr := form_rate(rows, k_gameweeks=config.FORM_GAMEWEEKS))[0] is not None
    }
    return player_xp(
        players, upcoming, source=source, horizon=horizon, now=now,
        baseline_by_code=baseline_by_code, minutes_weight=weight, history_by_code=history_by_code,
        form_by_code=form_by_code, form_weight=config.FORM_WEIGHT,
        defcon_weight=config.DEFCON_MAGNIFIER_WEIGHT,
        # ADR-188 — the club clean-sheet delta for DEF/GK. Rates are computed only when the weight is live,
        # so a dormant term costs nothing: `team_clean_sheet_rate` is a scan per club and there is no reason
        # to pay for it to multiply by zero.
        clean_sheet_weight=config.CLEAN_SHEET_WEIGHT,
        clean_sheet_rates=(_clean_sheet_rates(players, gw_history_by_code)
                           if config.CLEAN_SHEET_WEIGHT else None),
    )


def _clean_sheet_rates(players, gw_history_by_code) -> dict:
    """`{team → clean-sheet probability}` from the per-GW history, or `{}` with nothing played yet.

    ⭐ **ADR-195 changed only this function.** `clean_sheet_delta`, `league_clean_sheet_rate` and the call
    site above are untouched, along with ADR-188's five mutation-tested guards — which is the whole point:
    the term's *shape* was never what was wrong, its *input* was.

    ADR-188 measured a club's **clean-sheet rate**, and over four gameweeks that is a five-valued statistic
    derived from a coin flip. It read a null. So did a second look at it (ADR-190 Option 3), and I told the
    owner twice that his instinct was not supported. ⭐⭐ *A null is a statement about the instrument as much
    as about the world* — xGC/90 is continuous and minutes-normalised, spreads 3x across the league on the
    same four gameweeks, and correlates with defenders' actual points at **4.2 SE** where the rate showed
    nothing.

    The Poisson step (`clean_sheet_prob`) is what keeps the output a probability, so the `x CLEAN_SHEET_POINTS`
    downstream still means points. **The weight is still 0**; this changes what would be swept at GW6, not
    what ships today.
    """
    if not gw_history_by_code:
        return {}
    return {t: clean_sheet_prob(team_xgc90(gw_history_by_code, players, t))
            for t in {p["team"] for p in players}}
