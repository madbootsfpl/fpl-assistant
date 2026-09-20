"""Price Change Predictor — a directional, ownership-normalised transfer-pressure lens (ADR-092).

FPL prices move when a player's **net transfers** (in − out) cross a hidden threshold that scales with
**ownership**. We can't compute the exact price or timing (the threshold + the "since last change" counter
aren't published, nor in `bootstrap-static`), so this is a **directional flag**: net transfers per 1%
ownership → a *rise / fall / stable* prediction. Dividing by ownership makes it comparable across players (a
template needs far more net transfers to move than a differential) and the constant total-manager count
**cancels out**. 0 on flat preseason data → **live at GW1**. A **lens** — it never touches `decision_xp`.
"""

from collections import namedtuple

# ⚠️ The floor is imported, not restated. It defines the population the cut points are taken over, and a
# second copy of it here would be two definitions of "who counts" over one quantity — the drift ADR-123/127
# are about. (crowd imports `price_pressure` back, lazily, so this direction is the safe one.)
from src.analytics.crowd import EXODUS_OWNERSHIP_FLOOR as PRESSURE_OWNERSHIP_FLOOR
from src.analytics.crowd import _get, net_transfers
from src.analytics.gw_form import stat_series

# ⭐⭐ **The old constants were PLACEHOLDERS that were never replaced, and the comment beside them said so.**
# `PRICE_RISE_PRESSURE = PRICE_FALL_PRESSURE = 20_000` were, in the words of the line they replaced, *"chosen
# so nothing fires on flat preseason data … calibrated on real net transfers at GW1"*. The first half
# happened. The second did not, and nothing failed — because a rule that never fires looks exactly like a
# rule with nothing to report.
#
# Measured at GW5 (ADR-215), over the 189 players owned by ≥1%:
#
# | | |
# |---|---|
# | the threshold | **±20,000** |
# | highest buying pressure on the board | **+5,760** |
# | lowest selling pressure | **−2,660** |
#
# The bar sat 3.5× above anything that occurs, so `price_prediction` returned `stable` for all 662 players
# while **269 of them had actually moved price that season**.
#
# ⚠️ **And a fixed bar was the wrong SHAPE, not just the wrong value** — the same fault ADR-210 found in
# `EXODUS_PRESSURE`, in the same quantity. `price_pressure` divides `transfers_in_event − transfers_out_event`
# by ownership, and those counters **reset at every deadline and fill across the week**. A constant therefore
# encodes the hour of the week it was picked: the numbers above were read **516 hours** before the GW6
# deadline, and the same board the night before would be an order of magnitude larger.
#
# So, exactly as ADR-210 did for exodus: the **definition** stays and the number goes.
#
# ⭐ **Rises and falls are not symmetric, and one constant for both assumed they were.** Counted from
# `player_history`, which records each player's price per round:
#
# | | rose | fell |
# |---|---|---|
# | GW1→2 | 1.0% | 1.8% |
# | GW2→3 | 2.1% | **16.9%** |
# | GW3→4 | 2.8% | **15.3%** |
#
# About seven times more players fall than rise, because a bad week empties a bandwagon faster than a good
# one fills it. The percentiles below are those observed rates, not a taste.
PRICE_RISE_PERCENTILE = 98.0     # the top ~2% of buying pressure
PRICE_FALL_PERCENTILE = 15.0     # the worst ~15% of selling pressure

# Below this there is no distribution to take a percentile of — the same reasoning, and the same number, as
# `MIN_EXODUS_POPULATION`.
MIN_PRICE_POPULATION = 20

# The live cut points. Either may be `None`, which means *"this direction cannot fire right now"* — never
# "use a default", because the default is what produced a dead rule for a whole season.
PriceCuts = namedtuple("PriceCuts", "rise fall")

# The glyphs, defined once and used by every surface (ADR-140). They are **plain text triangles**, not the
# 🔺/🔻 emoji they replace — and that is the whole change: U+1F53A is literally "red triangle pointed up", so
# the old pair was red-up and red-down. Direction was carried twice (shape and position) while colour, the
# fastest channel a reader has, carried nothing at all.
#
# Plain glyphs inherit the surrounding colour, so each surface can paint them: green up / red down in the web
# tables (a pandas Styler) and in Streamlit captions (`:green[…]` markdown). The terminal renders them
# uncoloured, which is no worse than two identical reds and keeps ONE pair across the whole app — a rule
# written twice always drifts.
PRICE_UP, PRICE_DOWN = "▲", "▼"

PRICE_LEGEND = (f"Price: :green[{PRICE_UP}] likely to rise · :red[{PRICE_DOWN}] likely to fall (— = stable) — "
                "directional pressure from net transfers this gameweek, a flag not the exact price/timing; "
                "live from GW1.")

# The same legend without Streamlit's colour markdown, for anywhere that renders literally (the CLI, and any
# plain-text context). Kept beside its twin so they cannot drift apart unnoticed.
PRICE_LEGEND_PLAIN = (f"Price: {PRICE_UP} likely to rise · {PRICE_DOWN} likely to fall (— = stable) — "
                      "directional pressure from net transfers this gameweek, a flag not the exact "
                      "price/timing; live from GW1.")


def price_pressure(player):
    """Net transfers per 1% ownership (signed) — a cross-player-comparable buying/selling pressure. `None` when
    net transfers or ownership is absent; **0** on flat preseason data. Display/lens only (never xP)."""
    net = net_transfers(player)
    own = _get(player, "selected_by")
    if net is None or not own:
        return None
    return net / own


def price_population(players) -> list:
    """The pressures the cut points are taken over — everyone owned by at least the floor.

    Separate from `price_thresholds` so a test can assert the *population* directly, and so the one place
    that decides who counts cannot drift from the one place that decides where the cuts fall (ADR-210's
    shape, for the same reason).
    """
    out = []
    for p in players or []:
        if (_get(p, "selected_by") or 0) < PRESSURE_OWNERSHIP_FLOOR:
            continue
        pressure = price_pressure(p)
        if pressure is not None:
            out.append(pressure)
    return out


def price_thresholds(players) -> PriceCuts:
    """The buying and selling pressures that read as a likely move **right now** (ADR-215).

    ⚠️ **`players` must be the whole board, never the list on screen.** A percentile taken over a filtered
    view manufactures a top 2% *inside every filter* — so a squad page would report two of your fifteen as
    rising every single week, and a one-club filter would find a riser at that club forever. `price_detector`
    exists so a caller binds the population once, deliberately, rather than passing whichever list is nearest.

    **Either cut is `None` when that direction cannot fire, and there are two ways that happens:**

    * **Too few players to have a distribution.** A percentile of nine players is not a percentile.
    * **The cut has the wrong sign.** ⭐ A distribution always *has* a top 2%, so on its own the percentile
      would name risers in a week when every single player was being sold. The percentile decides **how
      much**; the sign decides **whether there is anything to be a lot of**, and only the sign can say no.
    """
    from src.analytics.ranking import percentile_value

    pressures = price_population(players)
    if len(pressures) < MIN_PRICE_POPULATION:
        return PriceCuts(None, None)
    rise = percentile_value(pressures, PRICE_RISE_PERCENTILE)
    fall = percentile_value(pressures, PRICE_FALL_PERCENTILE)
    return PriceCuts(rise if rise is not None and rise > 0 else None,
                     fall if fall is not None and fall < 0 else None)


def price_detector(players):
    """Bind the live cuts to the whole board, returning the `player -> 'rise'|'fall'|'stable'` test.

    ⭐ **One recipe, bound once** — the shape ADR-181 argued for. `price_prediction` takes its cuts as a
    **required** argument for the same reason: a call site that forgets raises, rather than quietly falling
    back to a number nobody ever calibrated.
    """
    cuts = price_thresholds(players)
    return lambda player: price_prediction(player, cuts)


def price_prediction(player, cuts: PriceCuts) -> str:
    """`'rise'` | `'fall'` | `'stable'` — the directional call, against the cuts the caller bound.

    ⚠️ `cuts` is required and there is no default. The previous signature took none, read two module
    constants, and returned `stable` for every player on the board for a whole season without anything going
    red (ADR-215).
    """
    # ⚠️⚠️ **The same floor that built the population, applied again before anyone is tested against it.**
    # ADR-210 wrote this rule down and the first version of this function broke it: the cuts were taken over
    # players owned ≥1% and then applied to all 662, so **43 of 72 "fall" flags landed on players nobody
    # owns**. Pressure is net transfers *per 1% owned*, so for a 0.1%-owned player it divides by almost
    # nothing and a few thousand sales read as a collapse. ⭐ *A threshold and the thing it judges must be
    # measured in the same population, or it describes a distribution its subject was never in.*
    #
    # ⭐ Below the floor the answer is **"cannot say"**, not "will not move" — thinly-owned prices move all
    # the time. It surfaces as `stable` because that is what the existing callers render as blank, which is
    # the honest display for *no opinion*.
    if (_get(player, "selected_by") or 0) < PRESSURE_OWNERSHIP_FLOOR:
        return "stable"
    pressure = price_pressure(player)
    if pressure is None:
        return "stable"
    if cuts.rise is not None and pressure >= cuts.rise:
        return "rise"
    if cuts.fall is not None and pressure <= cuts.fall:
        return "fall"
    return "stable"


def price_flag(player, cuts: PriceCuts) -> str:
    """A compact Price-column flag — ▲ rising · ▼ falling · `""` stable. Distinct from the **retrospective**
    crowd 💰↑/💸↓ (`cost_change_event`, a change that already happened); this is **forward-looking**.

    The glyph is deliberately plain text rather than an emoji so the caller can colour it (ADR-140) — green
    up, red down. An emoji brings its own colour and both of the obvious ones are red.
    """
    return {"rise": PRICE_UP, "fall": PRICE_DOWN}.get(price_prediction(player, cuts), "")


# A price move is £0.1m, so anything under half of one is float noise, not a change.
_PRICE_EPS = 0.05


def price_move(player):
    """What a player's price has done **since the season started**, in £m — `+0.1`, `-0.3`, `0.0`, or None.

    Retrospective, unlike `price_flag`, which predicts. FPL gives this directly as `cost_change_start` (in
    tenths) rather than making us difference anything, so it is exact and available from day one — which is
    the whole reason this is worth showing while the per-gameweek series is still one point long (ADR-160).
    """
    change = _get(player, "cost_change_start")
    return None if change is None else change / 10.0


def price_series(gw_history, code, player, *, last: int = 12) -> list[tuple]:
    """A player's price per gameweek, oldest first, **with today's price as the final point** (ADR-160).

    Two sources, on purpose. The per-gameweek `value` column gives the price *at* each gameweek, aggregated
    with `agg="last"` because a double gameweek must not add a player's price to itself (ADR-129 wrote that
    rule for exactly this column). But `value` is only written when a gameweek is played, while prices move
    every night — so the newest per-GW point can be days stale. **Watkins reads £8.0m at GW1 and £7.9m
    everywhere else in the app**, and a chart that disagrees with the number beside it is worse than no chart.
    Appending the live price fixes that and is also what makes a series exist at all this early.

    Returns `[(label, £m), …]`; `[]` when there is nothing to draw.
    """
    points = [(f"GW{rnd}", value / 10.0)
              for rnd, value in stat_series(gw_history, code, "value", last=last, agg="last")]
    now = _get(player, "price")
    if now is not None and (not points or abs(points[-1][1] - float(now)) >= _PRICE_EPS):
        points.append(("now", round(float(now), 1)))
    return points
