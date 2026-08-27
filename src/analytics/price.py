"""Price Change Predictor — a directional, ownership-normalised transfer-pressure lens (ADR-092).

FPL prices move when a player's **net transfers** (in − out) cross a hidden threshold that scales with
**ownership**. We can't compute the exact price or timing (the threshold + the "since last change" counter
aren't published, nor in `bootstrap-static`), so this is a **directional flag**: net transfers per 1%
ownership → a *rise / fall / stable* prediction. Dividing by ownership makes it comparable across players (a
template needs far more net transfers to move than a differential) and the constant total-manager count
**cancels out**. 0 on flat preseason data → **live at GW1**. A **lens** — it never touches `decision_xp`.
"""

from src.analytics.crowd import _get, net_transfers
from src.analytics.gw_form import stat_series

# Net transfers per 1% ownership beyond which a move reads as "likely". Placeholders chosen so nothing fires on
# flat preseason data (net = 0); calibrated on real net transfers at GW1 (like TRENDING_NET / FORM_WEIGHT).
PRICE_RISE_PRESSURE = 20_000.0
PRICE_FALL_PRESSURE = 20_000.0

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


def price_prediction(player) -> str:
    """`'rise'` | `'fall'` | `'stable'` — the directional price call from the pressure (thresholds GW1-calibrated)."""
    pressure = price_pressure(player)
    if pressure is None:
        return "stable"
    if pressure >= PRICE_RISE_PRESSURE:
        return "rise"
    if pressure <= -PRICE_FALL_PRESSURE:
        return "fall"
    return "stable"


def price_flag(player) -> str:
    """A compact Price-column flag — ▲ rising · ▼ falling · `""` stable. Distinct from the **retrospective**
    crowd 💰↑/💸↓ (`cost_change_event`, a change that already happened); this is **forward-looking**.

    The glyph is deliberately plain text rather than an emoji so the caller can colour it (ADR-140) — green
    up, red down. An emoji brings its own colour and both of the obvious ones are red.
    """
    return {"rise": PRICE_UP, "fall": PRICE_DOWN}.get(price_prediction(player), "")


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
