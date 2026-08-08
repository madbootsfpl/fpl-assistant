"""Price Change Predictor — a directional, ownership-normalised transfer-pressure lens (ADR-092).

FPL prices move when a player's **net transfers** (in − out) cross a hidden threshold that scales with
**ownership**. We can't compute the exact price or timing (the threshold + the "since last change" counter
aren't published, nor in `bootstrap-static`), so this is a **directional flag**: net transfers per 1%
ownership → a *rise / fall / stable* prediction. Dividing by ownership makes it comparable across players (a
template needs far more net transfers to move than a differential) and the constant total-manager count
**cancels out**. 0 on flat preseason data → **live at GW1**. A **lens** — it never touches `decision_xp`.
"""

from src.analytics.crowd import _get, net_transfers

# Net transfers per 1% ownership beyond which a move reads as "likely". Placeholders chosen so nothing fires on
# flat preseason data (net = 0); calibrated on real net transfers at GW1 (like TRENDING_NET / FORM_WEIGHT).
PRICE_RISE_PRESSURE = 20_000.0
PRICE_FALL_PRESSURE = 20_000.0

PRICE_LEGEND = ("Price: 🔺 likely to rise · 🔻 likely to fall (— = stable) — directional pressure from net "
                "transfers this gameweek, a flag not the exact price/timing; live from GW1.")


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
    """A compact Price-column flag — 🔺 rising · 🔻 falling · `""` stable. Distinct from the **retrospective**
    crowd 💰↑/💸↓ (`cost_change_event`, a change that already happened); this is **forward-looking**."""
    return {"rise": "🔺", "fall": "🔻"}.get(price_prediction(player), "")
