"""A flag is evidence about the matches it was published for (ADR-206 §2/§3).

§1 stopped a doubtful player being priced at zero. It left the *shape* wrong: the 0.75 discount still applied
to every gameweek in the horizon, so a knock reported today priced a fixture in **November**.

FPL publishes `chance_of_playing` about the **upcoming** match — a *now* field with no "as of" (ADR-203). So
applying it five weeks out states something the source never said.

⭐ **The reach is measured in DAYS, not gameweeks, and that is the whole of §3**: an international break needs
no concept of its own. GW6 kicks off 19 days after GW5, so a flag raised today simply cannot reach it.
"""

import pytest

from src import config
from src.analytics.minutes import chance_factor
from src.analytics.xp import decision_xp, player_xp

NOW = "2026-09-17T12:00:00+00:00"


def _p(pid, status="a", chance=None, ppg=8.0, tid=1, team="ARS"):
    return {"id": pid, "code": pid, "web_name": f"P{pid}", "position": "FWD", "team": team, "team_id": tid,
            "price": 7.0, "status": status, "chance": chance, "total_points": 40, "points_per_game": ppg,
            "minutes": 360, "form": 0.0, "ep_next": 4.0, "selected_by": 5.0, "penalties_order": None,
            "corners_order": None, "freekicks_order": None, "cost_change_event": 0,
            "transfers_in_event": 0, "xgc": 1.0, "clean_sheets": 0}


def _fx(event, kickoff):
    return {"event": event, "team_h": 1, "team_a": 2, "team_h_difficulty": 3, "team_a_difficulty": 3,
            "home": "ARS", "away": "SUN", "kickoff_time": kickoff,
            "home_team_strength": 3, "away_team_strength": 3}


def _run(players, fixtures, **kw):
    kw.setdefault("minutes_weight", chance_factor)
    kw.setdefault("now", NOW)
    return {r["web_name"]: r for r in player_xp(players, fixtures, horizon=len(fixtures), **kw)}


# --- the shape §1 deliberately left wrong ---------------------------------------------

def test_the_discount_applies_near_and_lifts_beyond_the_window():
    """Tomorrow's match carries the doubt. A match five weeks out does not.

    ⚠️ Given an explicit baseline so this exercises the **`hist`** tier, where xP is linear in the weight and
    the ratio can be asserted exactly. A first version left it to default and landed in `cold_start`, whose
    blend is non-linear — so the assertion failed for a reason that is *correct behaviour*, and is pinned as
    such in `test_the_cold_start_tier_is_re_evaluated_not_rescaled`.
    """
    fixtures = [_fx(5, "2026-09-18T19:00:00Z"), _fx(6, "2026-10-10T11:30:00Z")]
    base = {1: 0.06, 2: 0.06}
    out = _run([_p(1, status="d", chance=75), _p(2)], fixtures, baseline_by_code=base)
    # ⚠️ **Asserted on the EXACT values, not the displayed ones, and the reason is worth stating.** ADR-213
    # made `by_gameweek` apportioned so a player's cells sum to their total — which means a cell is no longer
    # a pure function of that gameweek: a spare tenth lands wherever the largest fractional part is. Two
    # players whose exact GW6 values are identical can therefore *display* 0.1 apart.
    #
    # ⭐ That is tolerable in general (measured: 4 of 2,141 equal-value groups on the real board, 0.2%) but it
    # is guaranteed here, because this fixture uses a deliberately tiny baseline — 0.06 a gameweek, where one
    # tenth is larger than the value itself. The claim being tested is about the **model**, so it belongs on
    # the model's numbers; asserting it on a 1dp rendering would be testing the renderer.
    flagged, twin = out["P1"]["by_gameweek_exact"], out["P2"]["by_gameweek_exact"]
    assert flagged[5] < twin[5], f"the near gameweek must carry the discount: {flagged} vs {twin}"
    assert flagged[6] == twin[6], (
        f"beyond the window he must be worth exactly what an unflagged twin is worth: {flagged} vs {twin}")


def test_an_international_break_needs_no_concept_of_its_own():
    """⭐ **§3 falls out of §2 for free.** Nothing in the code knows what an international break *is* — GW6
    is simply 23 days away, and 23 > 8. The same mechanism handles a cup week, a postponement, or a
    rescheduled fixture, none of which anyone has to enumerate."""
    near = [_fx(5, "2026-09-18T19:00:00Z"), _fx(6, "2026-09-25T19:00:00Z")]      # a normal week apart
    far = [_fx(5, "2026-09-18T19:00:00Z"), _fx(6, "2026-10-10T11:30:00Z")]       # the real break
    flagged = [_p(1, status="d", chance=75)]
    assert _run(flagged, near)["P1"]["by_gameweek"][6] < _run(flagged, far)["P1"]["by_gameweek"][6], (
        "the same gameweek number must be worth more when it is further away")


def test_an_unflagged_player_is_byte_identical():
    """⚠️ The invariance. 636 of 659 players are unflagged, and none of them may move by a thousandth."""
    fixtures = [_fx(5, "2026-09-18T19:00:00Z"), _fx(6, "2026-10-10T11:30:00Z")]
    players = [_p(1), _p(2, ppg=3.0)]
    with_now = _run(players, fixtures)
    without = _run(players, fixtures, now=None)
    assert {k: v["xp"] for k, v in with_now.items()} == {k: v["xp"] for k, v in without.items()}
    assert with_now["P1"]["by_gameweek"][5] == with_now["P1"]["by_gameweek"][6], (
        "an unflagged player's two identical fixtures must project identically")


def test_an_unavailable_player_is_not_rescued_by_distance():
    """⚠️ **Scope.** This lifts a *doubt*, never the gate. An injured player stays 0 for the whole horizon —
    too pessimistic in its own way, and deliberately out of scope rather than half-fixed here."""
    fixtures = [_fx(5, "2026-09-18T19:00:00Z"), _fx(6, "2026-10-10T11:30:00Z")]
    out = _run([_p(1, status="i")], fixtures)["P1"]
    assert out["xp"] == 0.0 and set(out["by_gameweek"].values()) == {0.0}


def test_a_fixture_with_no_kickoff_time_stays_in_reach():
    """⭐ *When a guard's input is missing, fail toward the cautious reading, not the convenient one.*
    A fixture with no time yet is most often the next one; treating "unknown" as "far away" would un-flag a
    player before a match that might be tomorrow."""
    out = _run([_p(1, status="d", chance=75)], [_fx(5, None)])["P1"]["by_gameweek"]
    undiscounted = _run([_p(1)], [_fx(5, None)])["P1"]["by_gameweek"]
    assert out[5] < undiscounted[5], "an unknown kickoff must keep the discount, not drop it"


def test_the_window_is_a_declared_constant_with_a_reason():
    """ADR-199: a threshold is measured, or declared unmeasured **with a reason**. This one cannot be measured
    until ADR-203's availability log has history — it began recording 2026-09-17."""
    assert config.FLAG_HORIZON_DAYS == 8
    import inspect
    src = inspect.getsource(config)
    i = src.index("FLAG_HORIZON_DAYS")
    assert "DECLARED, NOT MEASURED" in src[max(0, i - 1200):i], (
        "the constant must carry its provenance beside it")


def test_the_cold_start_tier_is_re_evaluated_not_rescaled():
    """⚠️ **Why the rate tier is computed twice instead of the answer being divided by the chance factor.**

    The `cold_start` blend carries the minutes weight *inside* its rate and non-linearly (ADR-124), so
    `xp / chance` would be wrong for exactly the players with the least evidence to spare. A player with no
    history at all exercises that branch.
    """
    fixtures = [_fx(5, "2026-09-18T19:00:00Z"), _fx(6, "2026-10-10T11:30:00Z")]
    cold = _p(1, status="d", chance=50, ppg=6.0)          # no baseline, no past seasons → cold_start
    out = _run([cold], fixtures, history_by_code={}, baseline_by_code={})["P1"]
    assert out["rate_source"] == "cold_start", out["rate_source"]
    near, far = out["by_gameweek"][5], out["by_gameweek"][6]
    assert far > near, "the far gameweek must still lift"
    assert far != pytest.approx(near / 0.5, rel=0.001), (
        "…and it must NOT be the naive rescale — the blend is non-linear in the weight")


def test_decision_xp_threads_the_clock():
    """⭐ *Testing a component is not testing that anything uses it.* Every surface goes through `decision_xp`;
    if it does not accept `now`, the whole mechanism is unreachable in production."""
    fixtures = [_fx(5, "2026-09-18T19:00:00Z"), _fx(6, "2026-10-10T11:30:00Z")]
    out = {r["web_name"]: r for r in decision_xp(
        [_p(1, status="d", chance=75)], fixtures, {}, horizon=2, now=NOW)}
    assert out["P1"]["by_gameweek"][6] > out["P1"]["by_gameweek"][5]
