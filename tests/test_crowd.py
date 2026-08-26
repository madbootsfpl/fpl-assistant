"""Tests for the crowd/sentiment lens (Phase 6, ADR-057).

`crowd_flags` is a pure, empty-safe row→flags function; the crucial invariant is that these signals are a
**display lens only** — they must never change the grounded xP (`decision_xp`).
"""

from src.analytics import (
    availability_flag,
    crowd_flags,
    decision_xp,
    fit_flag,
    net_transfers,
    ownership_tier,
    set_piece_flags,
    trending,
)
from src.analytics.crowd import (
    DIFFERENTIAL_OWN,
    ESSENTIAL_OWN,
    EXODUS_PRESSURE,
    FORM_MIN,
    TEMPLATE_OWN,
    TRENDING_NET,
    crowd_exodus,
    exodus_note,
)
from src.storage import Storage


def _p(**kw):
    return kw          # a player "row" is just a mapping; crowd_flags is empty-safe


def test_set_piece_flags_for_a_first_choice_taker():
    # ADR-081: order == 1 → the flag; any other order (or absent) → nothing. Display-only, empty-safe.
    assert set_piece_flags(_p(penalties_order=1)) == ["⚽ pens"]
    assert set_piece_flags(_p(corners_order=1)) == ["🚩 corners"]
    assert set_piece_flags(_p(freekicks_order=1)) == ["🎯 FK"]
    assert set_piece_flags(_p(penalties_order=1, corners_order=1, freekicks_order=1)) == [
        "⚽ pens", "🚩 corners", "🎯 FK",
    ]


def test_set_piece_flags_ignores_non_first_choice_and_is_empty_safe():
    assert set_piece_flags(_p(penalties_order=2, corners_order=6, freekicks_order=3)) == []
    assert set_piece_flags(_p()) == []                                   # nothing present → no flags
    assert set_piece_flags(_p(penalties_order=None)) == []               # None → no crash, no flag


def test_availability_flag_per_status():
    # ADR-074: a compact flag per FPL status code; available / unknown → no flag; empty-safe
    assert availability_flag(_p(status="i")) == "🚑"     # injured
    assert availability_flag(_p(status="s")) == "🚫"     # suspended
    assert availability_flag(_p(status="u")) == "⛔"     # unavailable
    assert availability_flag(_p(status="n")) == "⛔"     # not available
    assert availability_flag(_p(status="d")) == "❓"     # doubtful, chance unknown → just the flag
    assert availability_flag(_p(status="a")) == ""       # available → no flag
    assert availability_flag(_p()) == ""                 # missing status → no flag (empty-safe)


def test_fit_flag_shows_check_for_fit_else_the_availability_flag():
    # US-276: the Fit-column helper reads ✅ for a fit player and the availability flag for a concern.
    assert fit_flag(_p(status="a")) == "✅"               # available → positive ✅ (not blank)
    assert fit_flag(_p()) == "✅"                         # missing status → treated as fit (empty-safe)
    assert fit_flag(_p(status="i")) == "🚑"              # injured → the concern flag, unchanged
    assert fit_flag(_p(status="d", chance=75)) == "❓ 75%"  # doubtful still carries the chance
    # the invariant US-276 rests on: availability_flag itself is UNCHANGED (still "" for fit — the
    # truthiness that drives the "who's flagged" logic on My Squad + the gameweek plan).
    assert availability_flag(_p(status="a")) == ""


def test_availability_flag_shows_the_chance_on_a_doubtful_player():
    # US-236: a doubtful player carries the chance of playing (❓ 75%) when known
    assert availability_flag(_p(status="d", chance=75)) == "❓ 75%"
    assert availability_flag(_p(status="d", chance=0)) == "❓ 0%"     # 0% is a real value, still shown
    assert availability_flag(_p(status="i", chance=25)) == "🚑"      # only doubtful appends the chance


def test_availability_flag_is_distinct_from_crowd_and_rating():
    # the availability emojis must not collide with crowd flags (incl. the ⭐/👑 tiers) or the rating circles
    flags = set("🚑🚫⛔❓")
    assert not (flags & set("🟢🟡🟠🔴🟦💎⭐👑🔥❄️📈"))


def test_crowd_legend_explains_all_four_ownership_tiers():
    # US-289: the shared legend names the four tiers with their thresholds.
    from src.analytics import CROWD_LEGEND
    for word in ("differential", "popular", "template", "essential"):
        assert word in CROWD_LEGEND
    assert f"≤{DIFFERENTIAL_OWN:.0f}%" in CROWD_LEGEND and f">{ESSENTIAL_OWN:.0f}%" in CROWD_LEGEND


def test_ownership_tier_by_band():
    # US-289: 💎 ≤5 · ⭐ 5–20 · 🟦 20–60 · 👑 >60 (empty-safe); crowd_flags shows exactly one tier.
    assert ownership_tier(_p(selected_by=DIFFERENTIAL_OWN)) == "💎 differential"   # 5.0 → ≤5
    assert ownership_tier(_p(selected_by=0.0)) == "💎 differential"               # 0% included
    assert ownership_tier(_p(selected_by=10.0)) == "⭐ popular"                    # 5–20 (was unbadged before)
    assert ownership_tier(_p(selected_by=TEMPLATE_OWN)) == "🟦 template"           # 20 → template
    assert ownership_tier(_p(selected_by=ESSENTIAL_OWN)) == "🟦 template"          # 60 → still template
    assert ownership_tier(_p(selected_by=74.5)) == "👑 essential"                  # >60 → essential
    assert ownership_tier(_p()) == ""                                             # no ownership → no tier
    assert crowd_flags(_p(selected_by=74.5)) == ["👑 essential"]                   # exactly one tier flag


def test_price_flags_on_cost_change_sign():
    assert crowd_flags(_p(cost_change_event=2)) == ["💰↑"]
    assert crowd_flags(_p(cost_change_event=-1)) == ["💸↓"]
    assert crowd_flags(_p(cost_change_event=0)) == []          # no move → no flag


def test_trending_flags_on_net_transfers():
    assert "🔥 in" in crowd_flags(_p(transfers_in_event=TRENDING_NET, transfers_out_event=0))
    assert "❄️ out" in crowd_flags(_p(transfers_in_event=0, transfers_out_event=TRENDING_NET))
    quiet = crowd_flags(_p(transfers_in_event=10, transfers_out_event=5))     # tiny net → no flag
    assert "🔥" not in " ".join(quiet) and "❄️" not in " ".join(quiet)


def test_in_form_flag():
    assert "📈 form" in crowd_flags(_p(form=FORM_MIN))
    assert crowd_flags(_p(form=2.0)) == []


def test_crowd_flags_is_empty_safe():
    assert crowd_flags(_p()) == []                            # nothing present → no flags, no crash
    assert crowd_flags(_p(selected_by=None, form=None, cost_change_event=None)) == []


def test_net_transfers_handles_absence():
    assert net_transfers(_p(transfers_in_event=100, transfers_out_event=30)) == 70
    assert net_transfers(_p(transfers_in_event=100)) == 100   # one side absent → treated as 0
    assert net_transfers(_p()) is None                        # neither present → None


def test_decision_xp_ignores_the_crowd_fields():
    # THE invariant (ADR-057): the crowd lens must not change the grounded xP prediction.
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

    # Mutate every crowd field to wild values — xP must be identical.
    for p in players:
        p["form"], p["ict_index"], p["value_form"] = 99.0, 999.0, 42.0
        p["transfers_in_event"], p["transfers_out_event"] = 10_000_000, 0
        p["cost_change_event"], p["cost_change_start"] = 9, 9
    after = {r["id"]: r["xp"] for r in decision_xp(players, upcoming, history)}

    assert base == after


# --- trending leaderboards (Sprint 067) ----------------------------------------------------------

def test_trending_ranks_by_each_metric():
    players = [
        {"id": 1, "selected_by": 10, "form": 2.0, "transfers_in_event": 5, "transfers_out_event": 1},
        {"id": 2, "selected_by": 50, "form": 8.0, "transfers_in_event": 1, "transfers_out_event": 9},
        {"id": 3, "selected_by": 30, "form": 5.0, "transfers_in_event": 100, "transfers_out_event": 0},
    ]
    assert [r["id"] for r in trending(players, "owned")] == [2, 3, 1]     # 50 > 30 > 10
    assert [r["id"] for r in trending(players, "form")] == [2, 3, 1]      # 8 > 5 > 2
    assert trending(players, "in")[0]["id"] == 3                          # net +100 buys
    assert trending(players, "out")[0]["id"] == 2                         # net −8 (most sold)
    assert trending(players, "owned", limit=1)[0]["trend"] == 50          # the display value


def test_trending_is_empty_safe():
    assert trending([], "owned") == []
    assert trending([{"id": 1}], "owned")[0]["trend"] == 0                # missing metric → 0, no crash


# ---- an exodus our own data can't explain (ADR-146) -----------------------------------

def _pl(**kw):
    base = {"web_name": "X", "status": "a", "news": "", "selected_by": 10.0,
            "transfers_in_event": 0, "transfers_out_event": 0}
    return {**base, **kw}


def test_a_heavy_unexplained_sell_off_is_flagged():
    """The reported gap. Watkins: **103,678 out vs 7,583 in — net −96,095** — while `status` was `a`, `news`
    empty and `chance` None. FPL's feed carries injuries and suspensions; it carries nothing about a transfer
    to Saudi Arabia. But a hundred thousand managers reading the same headline show up in the transfer
    numbers within hours, and the app had that data and used it nowhere.
    """
    watkins = _pl(web_name="Watkins", selected_by=9.5, transfers_in_event=7_583, transfers_out_event=103_678)
    ex = crowd_exodus(watkins)
    assert ex is not None and ex["net"] == -96_095
    note = exodus_note(watkins, ex)
    assert "96,095" in note and "Watkins" in note and "nothing in the data explains it" in note


def test_an_exodus_our_data_DOES_explain_is_not_flagged():
    """The signal is the **discrepancy**, not the exodus. Pedro Porro had the largest sell-off of all
    (−227,771) and it is fully explained by a fitness flag we already surface — flagging him too would bury
    the three players nobody could account for."""
    porro = _pl(web_name="Pedro Porro", status="d", news="Lack of match fitness - 75% chance of playing",
                selected_by=14.3, transfers_out_event=230_000, transfers_in_event=2_229)
    assert crowd_exodus(porro) is None
    assert crowd_exodus(_pl(status="i", transfers_out_event=200_000)) is None


def test_it_is_measured_per_one_percent_owned_so_template_players_are_not_flagged_for_being_popular():
    """A 50%-owned player churns big absolute numbers every week. `price_pressure` normalises by ownership,
    which is why the threshold is a pressure and not a raw count."""
    template = _pl(selected_by=50.0, transfers_out_event=90_000, transfers_in_event=0)   # −1,800 per 1%
    niche = _pl(selected_by=2.0, transfers_out_event=40_000, transfers_in_event=0)       # −20,000 per 1%
    assert crowd_exodus(template) is None
    assert crowd_exodus(niche) is not None


def test_players_being_bought_are_not_an_exodus():
    assert crowd_exodus(_pl(transfers_in_event=200_000, transfers_out_event=0)) is None
    assert crowd_exodus(_pl(transfers_in_event=0, transfers_out_event=0)) is None


def test_the_note_does_not_claim_to_know_WHAT_the_news_is():
    """Careful about what it asserts. We do not know he is injured or leaving — we know the crowd is acting on
    something we cannot see. Saying more than that would be inventing a reason to sound confident."""
    note = exodus_note(_pl(web_name="Watkins", transfers_out_event=100_000),
                       {"net": -100_000, "pressure": -10_000})
    # It *rules things out* — "no injury, no suspension, no news" — which is the honest part: it says what was
    # checked. What it must never do is assert a cause it cannot know.
    assert "no injury, no suspension, no news" in note
    for invented in ("transfer to", "Saudi", "is leaving", "is injured", "is suspended", "will move"):
        assert invented.lower() not in note.lower(), f"the note must not invent a cause: {invented}"
    assert "can't see" in note or "cannot see" in note


def test_the_threshold_is_the_measured_tenth_percentile():
    """Calibrated on live GW1 data: across the 199 players owned by ≥1%, `price_pressure` runs
    p10 −7,996 · median −969 · p90 +11,104. `EXODUS_PRESSURE` is that p10 — the worst tenth — so this speaks
    about as often as it should rather than whenever someone is unpopular."""
    assert EXODUS_PRESSURE == -8_000
