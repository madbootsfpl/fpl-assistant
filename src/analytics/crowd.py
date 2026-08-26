"""Crowd & sentiment signals — a display **lens** over the free FPL fields (Phase 6, ADR-057).

Pure: a player row → a list of short, human-readable **flags**. This is display-only — it is **never
blended into xP** (the grounded prediction stays exactly as it was). Empty-safe: a 0 / None field yields no
flag (no crash). Thresholds are tunable constants, calibrated on real data — ownership now; the momentum /
form ones at GW1 (0 in preseason).
"""

# Tunable thresholds (ADR-057), calibrated on the live FPL data.
TEMPLATE_OWN = 20.0        # ≥ this % owned → a "template" pick (≈ the top ~17 today)
DIFFERENTIAL_OWN = 5.0     # ≤ this % owned → a "differential" (matches the differential filter, ADR-061)
ESSENTIAL_OWN = 60.0       # > this % owned → "essential" (a must-own; tunable, GW1-calibrated, US-289)
FORM_MIN = 6.0             # ≥ this recent avg pts/GW → "in form" (calibrate at GW1)
# |net transfers this GW| ≥ this → trending in/out. **Calibrated at GW1 (ADR-146):** across the 199 players
# owned by ≥1% of managers, net transfers run p10 −35,221 · median −2,946 · p90 +46,808, so 50k sits just
# outside each tail and fires for well under a tenth of players in either direction. Kept as it was — the
# placeholder turned out to be about right, which is worth recording so nobody re-derives it.
TRENDING_NET = 50_000


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


def ownership_tier(player) -> str:
    """The ownership tier for a player row (US-289, extends ADR-057) — one of **💎 differential** (≤5%),
    **⭐ popular** (5–20%), **🟦 template** (20–60%) or **👑 essential** (>60%), or `""` when ownership is
    absent. A display **lens** (never xP); the boundaries are the tunable `DIFFERENTIAL_OWN` / `TEMPLATE_OWN` /
    `ESSENTIAL_OWN`. The differential cut matches the "best differential" filter (ADR-061)."""
    own = _get(player, "selected_by")
    if own is None:
        return ""
    if own <= DIFFERENTIAL_OWN:      # ≤5% — a low-owned punt, high rank upside
        return "💎 differential"
    if own < TEMPLATE_OWN:           # 5–20% — well-owned but not widespread
        return "⭐ popular"
    if own <= ESSENTIAL_OWN:         # 20–60% — commonly owned, a safer pick
        return "🟦 template"
    return "👑 essential"            # >60% — a must-own; going without is a major rank risk


def ownership_label(player) -> str:
    """The ownership tier **word** (no emoji) — `differential` | `popular` | `template` | `essential` | `""`.
    Lets the explanations (US-290) speak the same ownership language as the badges."""
    tier = ownership_tier(player)
    return tier.split(" ", 1)[1] if tier else ""


def crowd_flags(player) -> list:
    """Short crowd/sentiment flags for a player row — empty-safe, display-only (ADR-057).

    An ownership **tier** (💎 differential / ⭐ popular / 🟦 template / 👑 essential, US-289), transfer momentum
    (`🔥 in` / `❄️ out`), price movement (`💰↑` / `💸↓`) and recent form (`📈 form`). Absent / zero signals
    simply produce no flag.
    """
    flags = []

    tier = ownership_tier(player)
    if tier:
        flags.append(tier)

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
AVAILABILITY_LEGEND = ("Fit: ✅ available · 🚑 injured · 🚫 suspended · ⛔ unavailable · ❓ doubtful "
                       "— see **News** for details.")

# The shared one-line legend for the set-piece "Set" column/line (Players + the Squads tables, ADR-081).
SET_PIECE_LEGEND = ("Set pieces: ⚽ penalties · 🚩 corners · 🎯 free-kicks — shown for the **first-choice** "
                    "taker (blank = not on set pieces).")

# The shared legend for the crowd/sentiment "Trends" flags. Ownership is now four tiers (US-289); the numbers
# track the tunable thresholds above.
CROWD_LEGEND = (
    f"Trends — ownership: 💎 **differential** ≤{DIFFERENTIAL_OWN:.0f}% (low-owned, high rank upside) · "
    f"⭐ **popular** {DIFFERENTIAL_OWN:.0f}–{TEMPLATE_OWN:.0f}% (well-owned, not widespread) · 🟦 **template** "
    f"{TEMPLATE_OWN:.0f}–{ESSENTIAL_OWN:.0f}% (commonly owned, a safer pick) · 👑 **essential** "
    f">{ESSENTIAL_OWN:.0f}% (a must-own — going without is a major rank risk). Plus 🔥 transferred in · "
    "❄️ transferred out · 💰↑ price rising · 💸↓ price falling · 📈 in form. (Ownership concentrates — and "
    "momentum/form go live — once the season starts.)"
)


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


def fit_flag(player) -> str:
    """The **Fit-column** display flag — the availability flag when the player is a concern (🚑/🚫/⛔/❓),
    else a positive **✅** (fit). A tester asked for a fit player to read as ✅ rather than a blank cell
    (US-276). Display-only; empty-safe. Note this is deliberately *separate* from `availability_flag`,
    which must keep returning `""` for a fit player — that `""` is the truthiness test the "who's flagged"
    logic relies on (the My Squad caption, the gameweek-plan flags)."""
    return availability_flag(player) or "✅"


# An exodus this severe, measured **per 1% of ownership** so a 50%-owned player isn't flagged just for being
# popular. Calibrated on live GW1 data (ADR-146): across players owned by ≥1%, `price_pressure` runs
# p10 −7,996 · median −969 · p90 +11,104. This is p10 — the worst tenth.
EXODUS_PRESSURE = -8_000


def crowd_exodus(player) -> dict | None:
    """The crowd is dumping this player **and our own data cannot say why** — or `None` (ADR-146).

    This is the app's only route to news it cannot read. FPL's feed carries injuries and suspensions, and
    those already drive `status` and `news`. It carries **nothing** about a transfer to Saudi Arabia, a
    training-ground row, or a manager's press conference — but a hundred thousand managers reading the same
    headline show up in `transfers_out_event` within hours.

    So the signal is not the exodus, it is the **discrepancy**: a heavy sell-off that our own fields leave
    unexplained. Measured on live GW1 data, the eight largest exoduses split five to three — five explained by
    a `status`/`news` we already surface, three (Gyökeres, Konsa, Watkins) with nothing at all behind them.
    Those three are exactly the ones a manager would want to be told about, and the only ones the app was
    silent on.

    Returns ``{net, pressure}`` when it fires. Deliberately says nothing about *what* the news is — it reports
    that the crowd knows something and we do not, which is true, checkable, and the most the data supports.

    Scale is `price_pressure` (net transfers per 1% owned, ADR-092), so a template player is not flagged
    merely for having big absolute numbers.
    """
    from src.analytics.price import price_pressure

    if _get(player, "status") != "a" or (_get(player, "news") or "").strip():
        return None                      # our own data *does* explain it — the flag would be noise
    pressure = price_pressure(player)
    if pressure is None or pressure > EXODUS_PRESSURE:
        return None
    net = net_transfers(player)
    if net is None or net >= 0:
        return None
    return {"net": net, "pressure": round(pressure)}


def exodus_note(player, exodus) -> str | None:
    """One sentence for an unexplained sell-off, or `None`.

    Careful about what it claims. It does **not** say the player is injured or leaving — we do not know that.
    It says the crowd is acting on something we cannot see, which is the honest reading and leaves the
    manager to go and look.
    """
    if not exodus:
        return None
    return (f"{abs(exodus['net']):,} managers sold {_get(player, 'web_name')} this gameweek and nothing in "
            "the data explains it — no injury, no suspension, no news. The crowd may be reacting to "
            "something we can't see; worth a look before you keep him.")
