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



# ADR-179 — the market signals as **bare glyphs**, for a pitch that wants them (the Lab). `crowd_flags` keeps
# the worded form for tables. Ownership is deliberately kept as ONE entry per player, because it is a
# four-point **scale** (💎 → ⭐ → 🟦 → 👑) rather than four independent facts — the key writes it as a scale
# for the same reason.
_WORDLESS = {"💰↑": "price rising", "💸↓": "price falling"}


def crowd_glyphs(player) -> list:
    """`[(glyph, meaning)]` for the market signals — ownership tier, momentum, price, form.

    ADR-178 argued *against* these as glyphs, and was right about **My Squad**: a phone, minutes before a
    deadline, where 💰↑ and 💸↓ are near-identical at 10px. It was wrong to generalise that to the Lab, where
    you are choosing players and differential-vs-template is the question (ADR-179). Same evidence, different
    page, different answer.
    """
    out = []
    for flag in crowd_flags(player):
        glyph, _, word = flag.partition(" ")
        # The price flags are the only ones whose worded form carries no word (`💰↑` / `💸↓` stand alone), so
        # without this their hover title would be the glyph explaining itself.
        out.append((glyph, word or _WORDLESS.get(glyph, glyph)))
    return out


CROWD_KEY = (
    "**Ownership:** 💎 differential → ⭐ popular → 🟦 template → 👑 essential  \n"
    "**Momentum:** 🔥 transferred in · ❄️ out · 💰↑ price rising · 💸↓ falling · 📈 in form"
)

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


# The one table of set-piece duties (ADR-081): the stored order field, the glyph, the short label a table
# column uses, and the long word the legend uses. ADR-178 put the **glyph alone** on the pitch and the words
# in a table, so the two renderings must not be able to disagree about which glyph means what — they are
# both built from this.
SET_PIECES = (
    ("penalties_order", "⚽", "pens", "penalties"),
    ("corners_order", "🚩", "corners", "corners"),
    ("freekicks_order", "🎯", "FK", "free-kicks"),
)


def _duties(player):
    """The set-piece rows this player is **first choice** for."""
    return [row for row in SET_PIECES if _get(player, row[0]) == 1]


def set_piece_flags(player) -> list:
    """First-choice set-piece duty flags for a player (ADR-081) — ⚽ pens · 🚩 corners · 🎯 FK, each
    when that order is 1 (the taker). Display-only; empty-safe (a Row or a dict). A low-owned taker is a
    prime differential; the returns are already in the player's points, so this is a *lens*, not xP.

    The **worded** form, for a table column. The pitch uses `set_piece_glyphs` instead (ADR-178)."""
    return [f"{glyph} {short}" for _field, glyph, short, _long in _duties(player)]


def set_piece_glyphs(player) -> list:
    """`[(glyph, meaning)]` — the **bare** form the pitch renders (ADR-178).

    Owner: *"would it be cleaner to use just the emoji under the player and have a key at the bottom of the
    pitch?"* On a 104px kit card the worded form wraps to three lines; three glyphs fit on one. The meaning
    rides along as a `title`, so a desktop hover explains without the key — and the key carries the phone.

    This is only legible **because the set is three**. The market flags were cut from the pitch first
    (ADR-178): 💰↑ and 💸↓ are near-identical at 10px, and 💎 ⭐ 🟦 👑 is a four-point ordinal scale drawn as
    four unrelated pictures. Three role glyphs are memorable; seven market glyphs are a rebus.
    """
    return [(glyph, long) for _field, glyph, _short, long in _duties(player)]


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


# ⭐⭐ **The worst tenth is the definition; the number is not.** ADR-146 calibrated `EXODUS_PRESSURE = -8,000`
# on live GW1 data (p10 across players owned ≥1%) and pinned it. ADR-190 tried to re-measure it, got −3,901,
# and recorded *"it varies"* — correctly, but without the mechanism.
#
# ⚠️ **The mechanism is that `transfers_in_event` / `transfers_out_event` are a counter that resets at every
# deadline and fills up across the week.** So `price_pressure` is not a quantity with a stable scale — it is an
# *accumulation*, and its distribution is a function of **how far into the gameweek you look**:
#
# | read | p10 | what −8,000 flags |
# |---|---|---|
# | GW1 calibration (ADR-146) | −7,996 | ~10% — by construction, that day |
# | 2026-09-13, ~1 day after the GW4 deadline (ADR-190) | −3,901 | **2 of 190** |
# | 2026-09-17, ~5 days in, GW5 deadline imminent (ADR-210) | −**14,992** | **50 of 188** |
#
# A fixed threshold on an accumulating counter does not encode a severity. It encodes **the hour of the week
# the calibration happened to run** — and it then reports a quarter of the board as a stampede on deadline day
# and almost nobody on a Sunday. ⭐ *Two samples 51% apart were not noise; they were two points on a ramp.*
#
# So the constant is gone and the **definition** stays: the worst tenth of selling pressure, read from the
# distribution that exists when the question is asked. A percentile is immune to the ramp by construction,
# because it re-reads the population every time.
EXODUS_PERCENTILE = 10.0

# …and only for players enough people own to have an opinion about (ADR-150). `price_pressure` is net
# transfers **per 1% owned**, which is the right scale for comparing a template player with a niche one — but
# it divides by a small number for a 0.1%-owned player, so a few thousand sales read as a stampede. On a
# per-squad warning that never mattered: you only ever see your own players, and you own them. On a *browse*
# list it does, and it filled the page with names nobody holds.
#
# 1% is not a taste: it **defines the population the percentile is taken over**. Under ADR-146 it had to match
# the population the constant was calibrated on; under ADR-210 it does the same job at both ends at once — it
# is the filter applied before the cut point is computed, and the filter applied before a player is tested
# against it. Those two must be the same set, or the threshold describes a distribution nobody is measured in.
EXODUS_OWNERSHIP_FLOOR = 1.0

# Below this there is no distribution to take a tenth of. Not tuned — it is the point at which "the worst
# tenth" stops naming more than a couple of players, and a threshold that can only ever describe one member
# is describing that member rather than a population.
MIN_EXODUS_POPULATION = 20


def exodus_population(players) -> list:
    """The pressures the threshold is taken over: everyone owned by at least `EXODUS_OWNERSHIP_FLOOR`%.

    Separate from `exodus_threshold` so a test can assert the *population* directly, and so the one place
    that decides who counts cannot drift from the one place that decides where the cut falls (ADR-150/210).
    """
    from src.analytics.price import price_pressure

    out = []
    for p in players or []:
        if (_get(p, "selected_by") or 0) < EXODUS_OWNERSHIP_FLOOR:
            continue
        pressure = price_pressure(p)
        if pressure is not None:
            out.append(pressure)
    return out


def exodus_threshold(players):
    """The selling pressure that counts as an exodus **right now**, or `None` when nothing does (ADR-210).

    The worst `EXODUS_PERCENTILE`% of the live distribution — the definition ADR-146 wrote down, evaluated
    against today's board instead of against GW1's.

    ⚠️ **`players` must be the whole board, never the list on screen.** The percentile is a claim about the
    league; taken over a filtered view it manufactures a worst tenth *inside every filter*, so choosing one
    club in the Signals filter would report an exodus at that club every week of the season. `exodus_detector`
    exists so a caller binds the population once, deliberately, rather than passing whichever list is nearest.

    **`None` in two cases, and both mean "the flag cannot fire":**

    * **Too few players to have a distribution.** A tenth of nine players is not a tenth of anything.
    * **The cut point is not negative** — preseason, or any week where the worst tenth is still net *buying*.
      ⭐ A percentile always *has* a bottom tenth, so on its own it would report an exodus in a week when
      nobody was being sold at all. The percentile decides **how severe**; the sign decides **whether there
      is anything to be severe about**, and only the second one is able to answer "no".

    ⭐ Returning `None` rather than a permissive number is ADR-192's direction applied deliberately: where the
    instrument cannot answer, it declines to, instead of defaulting to the value that flags everybody.
    """
    from src.analytics.ranking import percentile_value

    pressures = exodus_population(players)
    if len(pressures) < MIN_EXODUS_POPULATION:
        return None
    cut = percentile_value(pressures, EXODUS_PERCENTILE)
    return cut if cut is not None and cut < 0 else None


def exodus_detector(players):
    """Bind the live threshold to the whole board, returning the `player -> dict | None` test (ADR-210).

    ⭐ **One recipe, bound once** — the shape ADR-181 argued for after an optional argument on a shared helper
    let a single call site price a player differently from every other. `crowd_exodus` takes its threshold as
    a **required** argument for the same reason: a call site that forgets it raises, rather than quietly
    falling back to a number measured in August.

    `leavers`, `squad_risk_rows` and `gameweek_plan` all take a `player -> exodus` callable already, so this
    drops straight into the slot `crowd_exodus` itself used to occupy.
    """
    threshold = exodus_threshold(players)

    def detect(player):
        return crowd_exodus(player, threshold)
    return detect


def crowd_exodus(player, threshold) -> dict | None:
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

    `threshold` is the pressure at or below which a sell-off counts, from `exodus_threshold` — **required**,
    and `None` means the flag cannot fire at all (ADR-210). It used to default to the module constant
    `EXODUS_PRESSURE`, and that default was the whole bug: a number measured at one point in one gameweek's
    transfer cycle, applied at every other point of every other week.
    """
    from src.analytics.price import price_pressure

    if _get(player, "status") != "a" or (_get(player, "news") or "").strip():
        return None                      # our own data *does* explain it — the flag would be noise
    pressure = price_pressure(player)
    if threshold is None:
        return None                      # no live distribution to judge against — say nothing (ADR-210)
    if pressure is None or pressure > threshold:
        return None
    net = net_transfers(player)
    if net is None or net >= 0:
        return None
    return {"net": net, "pressure": round(pressure)}


def exodus_note(player, exodus, events=None) -> str | None:
    """One sentence for a heavy sell-off, or `None` — with a **cause** when the headlines carry one.

    Two versions of the same flag, and which one you get is the whole point of ADR-151:

    * **With a resolved event**, it names what the press reported and quotes the headline. *"96,095 sold him
      — Romano reports a move"* is checkable; the reader can weigh the source and disagree.
    * **Without one**, it says only that the crowd is acting on something we cannot see. It still does **not**
      claim the player is injured or leaving, because we do not know that.

    The second is what shipped in ADR-146, and it stays byte-identical when no event resolves — so a snapshot
    built without a language model behaves exactly as it did before.
    """
    if not exodus:
        return None
    sold = f"{abs(exodus['net']):,} managers sold {_get(player, 'web_name')} this gameweek"
    if events:
        from src.analytics.headlines import event_phrase
        return f"{sold} — and {event_phrase(events[0])}"
    return (f"{sold} and nothing in the data explains it — no injury, no suspension, no news. The crowd may "
            "be reacting to something we can't see; worth a look before you keep him.")
