"""Crowd & sentiment signals — a display **lens** over the free FPL fields (Phase 6, ADR-057).

Pure: a player row → a list of short, human-readable **flags**. This is display-only — it is **never
blended into xP** (the grounded prediction stays exactly as it was). Empty-safe: a 0 / None field yields no
flag (no crash). Thresholds are tunable constants, calibrated on real data — ownership now; the momentum /
form ones at GW1 (0 in preseason).
"""

# Tunable thresholds (ADR-057), calibrated on the live FPL data.
TEMPLATE_OWN = 20.0        # ≥ this % owned → a "template" pick (≈ the top ~17 today)
DIFFERENTIAL_OWN = 5.0     # 0 < own ≤ this % → a "differential" (reuse ADR-044)
FORM_MIN = 6.0             # ≥ this recent avg pts/GW → "in form" (calibrate at GW1)
TRENDING_NET = 50_000      # |net transfers this GW| ≥ this → trending in/out (calibrate at GW1)


def _get(player, key):
    """A player-row field (sqlite Row or dict), or None if absent."""
    try:
        return player[key]
    except (KeyError, IndexError):
        return None


def net_transfers(player):
    """Net managers buying this player this GW (in − out), or None if neither field is present."""
    tin, tout = _get(player, "transfers_in_event"), _get(player, "transfers_out_event")
    if tin is None and tout is None:
        return None
    return (tin or 0) - (tout or 0)


# The "trending" leaderboards (Sprint 067) — free crowd metrics, display-only (never xP).
# by → (a readable label, the column header). Ownership is live now; momentum/form are 0 preseason (GW1).
TREND_BYS = {
    "owned": ("most owned", "Own%"),
    "in": ("most transferred in", "Net in"),
    "out": ("most transferred out", "Net out"),
    "form": ("in form", "Form"),
}


def _trend_sort_value(player, by):
    """The value to rank by (higher = more 'trending'); missing → 0 (sorts last). Empty-safe."""
    if by == "owned":
        return _get(player, "selected_by") or 0
    if by == "form":
        return _get(player, "form") or 0
    net = net_transfers(player) or 0
    return net if by == "in" else -net          # 'out' ranks by most-sold (net most negative)


def _trend_display_value(player, by):
    """The number shown for a player on this board (own % · net transfers · form)."""
    if by == "owned":
        return _get(player, "selected_by") or 0
    if by == "form":
        return _get(player, "form") or 0
    return net_transfers(player) or 0           # net transfers (positive = buys, negative = sells)


def trending(players, by="owned", limit=10):
    """Rank players by a free crowd metric (ADR-057) — display-only, **never xP**. `by` is one of
    `TREND_BYS` (owned / in / out / form). Returns the top `limit` rows, each with a `trend` value for
    display. Empty-safe (missing metric → 0)."""
    ranked = sorted(players, key=lambda p: _trend_sort_value(p, by), reverse=True)
    return [{**dict(p), "trend": _trend_display_value(p, by)} for p in ranked[:limit]]


def crowd_flags(player) -> list:
    """Short crowd/sentiment flags for a player row — empty-safe, display-only (ADR-057).

    Ownership (`template` / `differential`), transfer momentum (`🔥 in` / `❄️ out`), price movement
    (`💰↑` / `💸↓`) and recent form (`📈 form`). Absent / zero signals simply produce no flag.
    """
    flags = []

    own = _get(player, "selected_by")
    if own is not None:
        if own >= TEMPLATE_OWN:
            flags.append("🟦 template")
        elif 0 < own <= DIFFERENTIAL_OWN:
            flags.append("💎 differential")

    net = net_transfers(player)
    if net is not None:
        if net >= TRENDING_NET:
            flags.append("🔥 in")
        elif net <= -TRENDING_NET:
            flags.append("❄️ out")

    change = _get(player, "cost_change_event")
    if change:                                  # non-zero £0.1m move
        flags.append("💰↑" if change > 0 else "💸↓")

    form = _get(player, "form")
    if form is not None and form >= FORM_MIN:
        flags.append("📈 form")

    return flags


# FPL status codes → a compact availability flag (ADR-074). Chosen distinct from the rating circles
# (🟢🟡🟠🔴) so a player's availability and their quality rating don't blur. "a" (available) → no flag.
_AVAILABILITY_FLAG = {"i": "🚑", "s": "🚫", "u": "⛔", "n": "⛔", "d": "❓"}

# The shared one-line legend for the Fit column (Pool + the stat boards).
AVAILABILITY_LEGEND = ("Fit: 🚑 injured · 🚫 suspended · ⛔ unavailable · ❓ doubtful "
                       "(blank = available) — see **News** for details.")

# The shared one-line legend for the set-piece "Set" column/line (Players + the Squads tables, ADR-081).
SET_PIECE_LEGEND = ("Set pieces: ⚽ penalties · 🚩 corners · 🎯 free-kicks — shown for the **first-choice** "
                    "taker (blank = not on set pieces).")


def set_piece_flags(player) -> list:
    """First-choice set-piece duty flags for a player (ADR-081) — ⚽ pens · 🚩 corners · 🎯 FK, each
    when that order is 1 (the taker). Display-only; empty-safe (a Row or a dict). A low-owned taker is a
    prime differential; the returns are already in the player's points, so this is a *lens*, not xP."""
    flags = []
    if _get(player, "penalties_order") == 1:
        flags.append("⚽ pens")
    if _get(player, "corners_order") == 1:
        flags.append("🚩 corners")
    if _get(player, "freekicks_order") == 1:
        flags.append("🎯 FK")
    return flags


def availability_flag(player) -> str:
    """A compact availability flag for a player row — 🚑 injured · 🚫 suspended · ⛔ unavailable ·
    ❓ doubtful — or `""` when available. A **doubtful** player carries the chance of playing when known
    (`❓ 75%`, US-236). Display-only; empty-safe (a Row or a dict). See ADR-023 for the status codes; the
    News page holds the full text."""
    status = _get(player, "status")
    if status == "d":
        chance = _get(player, "chance")
        return f"❓ {chance}%" if chance is not None else "❓"
    return _AVAILABILITY_FLAG.get(status, "")
