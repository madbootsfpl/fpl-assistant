"""Tests for the Price Change Predictor (Sprint 112, ADR-092).

A directional, ownership-normalised transfer-pressure **lens** — never `decision_xp`. Pure, empty-safe, and
0 on flat preseason data (net transfers = 0 → 'stable').
"""

from src.analytics import (
    decision_xp,
    price_detector,
    price_flag,
    price_prediction,
    price_pressure,
)
from src.analytics.price import (
    PRICE_DOWN,
    PRICE_UP,
    PriceCuts,
    price_move,
    price_series,
)
from src.storage import Storage


def _p(net_in=0, net_out=0, own=10.0):
    return {"transfers_in_event": net_in, "transfers_out_event": net_out, "selected_by": own}


def test_price_pressure_is_net_transfers_per_ownership_point():
    assert price_pressure(_p(net_in=500_000, net_out=100_000, own=10.0)) == 40_000.0   # +400k / 10%
    assert price_pressure(_p(net_in=0, net_out=350_000, own=10.0)) == -35_000.0        # −350k / 10% (signed)
    assert price_pressure(_p(net_in=0, net_out=0, own=50.0)) == 0.0                     # flat → 0 (dormant)


def test_price_pressure_is_none_safe():
    assert price_pressure({}) is None                                  # no fields
    assert price_pressure(_p(net_in=100_000, own=0)) is None           # no ownership → can't normalise
    assert price_pressure({"selected_by": 10.0}) is None               # no transfer fields (net None)


def test_price_prediction_thresholds():
    """⚠️ **The cuts are now an argument, not a module constant** (ADR-215). The old version of this test
    built its inputs *from* the constants it was checking — so it passed while the rule was unreachable on
    every real board. ⭐ *A test that derives its fixture from the thing under test is asking whether the
    code agrees with itself.* These are explicit numbers instead."""
    cuts = PriceCuts(rise=1_000.0, fall=-1_000.0)
    assert price_prediction(_p(net_in=10_001, own=10.0), cuts) == "rise"    # +1000.1 per 1%
    assert price_prediction(_p(net_out=10_001, own=10.0), cuts) == "fall"
    assert price_prediction(_p(net_in=100, own=10.0), cuts) == "stable"     # tiny pressure → stable
    assert price_prediction({}, cuts) == "stable"                           # empty-safe → stable


def test_a_direction_that_cannot_fire_never_fires():
    """⭐ `None` means *"this direction cannot fire"*, never *"use a default"* — the default is what left the
    rule dead for a season. A board where nobody is being bought must name no risers."""
    no_rise = PriceCuts(rise=None, fall=-1_000.0)
    assert price_prediction(_p(net_in=99_999_999, own=10.0), no_rise) == "stable"
    assert price_prediction(_p(net_out=10_001, own=10.0), no_rise) == "fall"
    assert price_prediction(_p(net_out=10_001, own=10.0), PriceCuts(None, None)) == "stable"


def test_a_thinly_owned_player_gets_no_opinion():
    """⚠️⚠️ **The floor that builds the population is applied again before anyone is judged by it.**

    Pressure is net transfers *per 1% owned*, so a 0.1%-owned player divides by almost nothing and a few
    thousand sales read as a collapse. The first version of this fix took the cuts over players owned ≥1%
    and then applied them to all 662 — **43 of 72 "fall" flags landed on players nobody owns**.
    ⭐ *A threshold and the thing it judges must be measured in the same population.*
    """
    cuts = PriceCuts(rise=1_000.0, fall=-1_000.0)
    assert price_prediction(_p(net_out=10_001, own=0.1), cuts) == "stable", "below the floor → no opinion"
    assert price_prediction(_p(net_out=10_001, own=1.0), cuts) == "fall", "at the floor → judged"


def test_price_flag_maps_direction_to_a_distinct_marker():
    # ADR-140: plain text triangles, NOT 🔺/🔻. U+1F53A is literally "red triangle pointed up", so the old
    # pair was red-up and red-down — direction carried twice while colour carried nothing. Plain glyphs
    # inherit the surrounding colour, which is what lets each surface paint them green-up / red-down.
    cuts = PriceCuts(rise=1_000.0, fall=-1_000.0)
    assert price_flag(_p(net_in=10_001, own=10.0), cuts) == PRICE_UP == "▲"
    assert price_flag(_p(net_out=10_001, own=10.0), cuts) == PRICE_DOWN == "▼"
    assert PRICE_UP not in "🔺🔻" and PRICE_DOWN not in "🔺🔻", \
        "an emoji brings its own colour, and both of the obvious ones are red — that is the bug"
    assert price_flag(_p(net_in=0, net_out=0, own=10.0), cuts) == ""    # stable → no flag
    # distinct from the retrospective crowd 💰/💸 (this is forward-looking)
    assert price_flag(_p(net_in=999_999_999, own=10.0), cuts) not in ("💰↑", "💸↓")


def test_price_is_a_lens_and_never_changes_decision_xp():
    # ADR-092 invariant: the predictor must not feed the grounded xP.
    store = Storage()
    try:
        players = [dict(p) for p in store.get_players()]
        upcoming = store.get_upcoming_fixtures()
        history = store.get_history_by_code()
    finally:
        store.close()
    if not players:
        return
    base = {r["id"]: r["xp"] for r in decision_xp(players, upcoming, history)}
    for p in players:                                                  # force strong price pressure both ways
        p["transfers_in_event"], p["transfers_out_event"] = 5_000_000, 0
    # ⭐ The cuts are re-read from the mutated board, which is the point of the detector: the lens fires
    # because the distribution changed, not because a constant happened to be crossed.
    predict = price_detector(players)
    assert any(predict(p) == "rise" for p in players)                   # the lens now fires…
    after = {r["id"]: r["xp"] for r in decision_xp(players, upcoming, history)}
    assert base == after                                              # …but xP is identical


def test_the_arrows_are_plain_text_so_a_surface_can_colour_them():
    """ADR-140 — the whole reason the glyphs changed.

    An emoji brings its own colour, and both of the obvious triangles are red (U+1F53A is *"red triangle
    pointed up"*), so the old pair spent the fastest channel a reader has on nothing. Plain text triangles
    inherit the surrounding colour, which is what lets the web tables paint them green-up / red-down.

    If someone swaps these back to emoji, the colouring silently stops working — the Styler matches on the
    exact glyph — so this asserts the property rather than the characters.
    """
    assert PRICE_UP.isprintable() and PRICE_DOWN.isprintable()
    assert all(ord(c) < 0x1F000 for c in PRICE_UP + PRICE_DOWN), \
        "an emoji-plane glyph carries its own colour and cannot be recoloured by CSS"
    assert PRICE_UP != PRICE_DOWN


def test_both_legends_say_the_same_thing_in_two_dialects():
    """One rule written twice always drifts, so they are pinned to agree. The Streamlit legend carries colour
    markdown; the plain one is for anywhere that renders literally."""
    from src.analytics.price import PRICE_LEGEND, PRICE_LEGEND_PLAIN

    assert f":green[{PRICE_UP}]" in PRICE_LEGEND and f":red[{PRICE_DOWN}]" in PRICE_LEGEND
    assert ":green[" not in PRICE_LEGEND_PLAIN and ":red[" not in PRICE_LEGEND_PLAIN
    strip = PRICE_LEGEND.replace(f":green[{PRICE_UP}]", PRICE_UP).replace(f":red[{PRICE_DOWN}]", PRICE_DOWN)
    assert strip == PRICE_LEGEND_PLAIN, "the two legends have drifted apart"


# ---- The price journey (ADR-160) ------------------------------------------------------------------
# Retrospective, unlike everything above it in this file: `price_flag` predicts where a price is going,
# these say where it has been.

def _hist(pairs):
    """`{code: [rows]}` for `[(round, value_in_tenths), …]`. A scoreline marks the gameweek as played."""
    return {9: [{"round": r, "value": v, "minutes": 90, "total_points": 2,
                 "team_h_score": 1, "team_a_score": 0, "was_home": True} for r, v in pairs]}


def _pl(price, change=0):
    return {"id": 1, "code": 9, "web_name": "P", "price": price, "cost_change_start": change}


def test_the_move_since_the_season_started_is_read_straight_off_fpl():
    assert price_move(_pl(4.6, 1)) == 0.1
    assert price_move(_pl(7.9, -3)) == -0.3
    assert price_move(_pl(15.5, 0)) == 0.0
    assert price_move({"price": 5.0}) is None


def test_todays_price_is_the_last_point_so_the_chart_cannot_contradict_the_page():
    """`value` is only written when a gameweek is played, but prices move nightly. Watkins really does read
    £8.0m at GW1 and £7.9m everywhere else in the app; a chart ending on the stale number would be a chart
    disagreeing with the number printed beside it."""
    assert price_series(_hist([(1, 80)]), 9, _pl(7.9, -1)) == [("GW1", 8.0), ("now", 7.9)]


def test_a_price_that_has_not_moved_yields_one_point_not_a_flat_pair():
    """Appending an identical 'now' would draw a dead-level line implying two observations of the same thing."""
    assert price_series(_hist([(1, 45)]), 9, _pl(4.5, 0)) == [("GW1", 4.5)]


def test_a_double_gameweek_does_not_add_a_price_to_itself():
    """ADR-129's rule, and `value` is the column it was written for — summing two fixtures in one round would
    read as a £4.5m rise."""
    rows = _hist([(1, 45), (1, 45)])
    assert price_series(rows, 9, _pl(4.5, 0)) == [("GW1", 4.5)]


def test_a_player_with_no_gameweek_rows_still_reports_his_price():
    assert price_series({}, 9, _pl(6.1, 0)) == [("now", 6.1)]
    assert price_series(None, 9, {"web_name": "P"}) == []


# ---- the live threshold (ADR-215) -------------------------------------------------------

def _board(n=60, own=5.0, net=0):
    return [dict(_p(net_in=net, own=own), id=i, web_name=f"P{i}") for i in range(n)]


def test_the_cuts_are_read_from_the_live_board_not_from_a_constant():
    """⭐⭐ **The whole point.** `price_pressure` divides accumulating counters that reset at every deadline,
    so a fixed bar encodes the hour it was picked. Double every player's transfers and the cut must move with
    them — a constant would not."""
    from src.analytics.price import price_thresholds

    quiet = [dict(_p(net_in=1_000 * (i % 10), own=5.0)) for i in range(60)]
    busy = [dict(_p(net_in=10_000 * (i % 10), own=5.0)) for i in range(60)]
    assert price_thresholds(busy).rise > price_thresholds(quiet).rise * 5


def test_a_direction_declines_rather_than_inventing_one():
    """⭐ A distribution always HAS a top 2%, so the percentile alone would name risers in a week when every
    player on the board was being sold. The sign is what can answer "no"."""
    from src.analytics.price import price_thresholds

    all_selling = [dict(_p(net_out=1_000 * (i % 9 + 1), own=5.0)) for i in range(60)]
    cuts = price_thresholds(all_selling)
    assert cuts.rise is None, "nobody is being bought — there is no rise cut to take"
    assert cuts.fall is not None and cuts.fall < 0


def test_too_small_a_population_has_no_distribution():
    """A percentile of nine players is not a percentile. ⭐ Declining beats defaulting — the default is what
    produced a rule that never fired."""
    from src.analytics.price import MIN_PRICE_POPULATION, price_thresholds

    tiny = [dict(_p(net_in=50_000 * i, own=5.0)) for i in range(MIN_PRICE_POPULATION - 1)]
    assert price_thresholds(tiny) == (None, None)


def test_the_population_is_the_owned_board_not_everyone():
    """The floor defines who the cut is taken over, and it must be the same set it is applied to."""
    from src.analytics.price import PRESSURE_OWNERSHIP_FLOOR, price_population

    mixed = ([dict(_p(net_in=1_000, own=PRESSURE_OWNERSHIP_FLOOR)) for _ in range(30)]
             + [dict(_p(net_in=1_000, own=0.1)) for _ in range(30)])
    assert len(price_population(mixed)) == 30


def test_the_detector_binds_the_whole_board_once():
    """⚠️ **The failure this shape prevents.** A squad page holds fifteen players; a percentile over those
    flags your worst two every week forever, whatever the league is doing. Bound to the board, a quiet squad
    inside a busy league correctly reports nothing."""
    from src.analytics.price import price_detector

    board = ([dict(_p(net_in=500_000, own=5.0), web_name=f"hot{i}") for i in range(10)]
             + [dict(_p(net_in=0, own=5.0), web_name=f"cold{i}") for i in range(50)])
    predict = price_detector(board)
    my_squad = [p for p in board if p["web_name"].startswith("cold")][:15]
    assert not any(predict(p) == "rise" for p in my_squad), (
        "a quiet squad in a busy league must report nothing")
    assert sum(predict(p) == "rise" for p in board) > 0, "…while the board itself still has risers"


def test_on_the_real_board_the_rule_actually_fires():
    """⚠️⚠️ **The test that would have caught the original bug, and the one that did not exist.**

    `price_prediction` returned `stable` for all 662 players for a whole season. Every unit test passed,
    because each built its input *from* the constants it was checking. ⭐ *A rule that never fires looks
    exactly like a rule with nothing to report* — so this one asks the real board.
    """
    from src.analytics.price import PRESSURE_OWNERSHIP_FLOOR, price_detector

    store = Storage()
    try:
        players = store.get_players()
    finally:
        store.close()
    if not players:
        return
    predict = price_detector(players)
    eligible = [p for p in players if (p["selected_by"] or 0) >= PRESSURE_OWNERSHIP_FLOOR]
    assert len(eligible) >= 20, "the snapshot must have a population to take a percentile over"

    verdicts = [predict(p) for p in eligible]
    rises, falls = verdicts.count("rise"), verdicts.count("fall")
    assert rises, "no player on the whole board is predicted to rise — the rule is unreachable again"
    assert falls, "no player on the whole board is predicted to fall"
    # ⭐ Measured from `player_history`: about 2% of prices rise and ~15% fall per gameweek. Loose bounds —
    # this is a smoke alarm for "the rule is dead" or "the rule flags everyone", not a calibration check.
    assert 0.001 < rises / len(eligible) < 0.15, f"{rises}/{len(eligible)} rising is not a top-2% rule"
    assert 0.02 < falls / len(eligible) < 0.40, f"{falls}/{len(eligible)} falling is out of band"
