"""Tests for the per-gameweek xP breakdown (ADR-032).

The breakdown must decompose the horizon total exactly, and handle a double gameweek
(two fixtures in one GW → summed) and a blank gameweek (no fixture → 0).
"""

from src.analytics import player_xp


def _player(pid=1, ppg=4.0, team_id=1, status="a", minutes=900):
    # `minutes` at the 900-min evidence bar → a no-history player's rate is their ppg (ADR-124's full-evidence end).
    return {"id": pid, "code": None, "web_name": f"P{pid}", "team": "AAA",
            "position": "MID", "team_id": team_id, "points_per_game": ppg,
            "status": status, "ep_next": 1.0, "minutes": minutes}


def _fx(event, home_id, away_id=99, home="AAA", away="OPP", diff=3):
    # diff 3 → multiplier 1.0, so each fixture contributes exactly the rate (4.0)
    return {"event": event, "team_h": home_id, "team_a": away_id, "home": home,
            "away": away, "team_h_difficulty": diff, "team_a_difficulty": diff}


def test_by_gameweek_sums_to_the_total():
    upcoming = [_fx(1, 1), _fx(2, 1), _fx(3, 1)]        # team 1 plays each GW
    r = player_xp([_player(ppg=4.0)], upcoming, horizon=3)[0]
    assert r["gameweeks"] == [1, 2, 3]
    assert r["by_gameweek"] == {1: 4.0, 2: 4.0, 3: 4.0}
    assert round(sum(r["by_gameweek"].values()), 1) == r["xp"] == 12.0


def test_double_gameweek_sums_its_fixtures():
    upcoming = [_fx(1, 1), _fx(2, 1), _fx(2, 1)]        # two fixtures in GW2
    r = player_xp([_player(ppg=4.0)], upcoming, horizon=2)[0]
    assert r["by_gameweek"][1] == 4.0
    assert r["by_gameweek"][2] == 8.0                  # 2 × 4.0
    assert r["xp"] == 12.0 and r["games"] == 3


def test_blank_gameweek_is_zero():
    # GW2 exists (team 2 plays) but team 1 has no fixture that week → 0 for team 1
    upcoming = [_fx(1, 1), _fx(2, 2), _fx(3, 1)]
    r = player_xp([_player(team_id=1, ppg=4.0)], upcoming, horizon=3)[0]
    assert r["gameweeks"] == [1, 2, 3]
    assert r["by_gameweek"] == {1: 4.0, 2: 0.0, 3: 4.0}
    assert r["xp"] == 8.0


def test_unavailable_player_is_zero_every_gameweek():
    upcoming = [_fx(1, 1), _fx(2, 1)]
    r = player_xp([_player(ppg=4.0, status="i")], upcoming, horizon=2)[0]
    assert r["xp"] == 0.0
    assert r["by_gameweek"] == {1: 0.0, 2: 0.0}        # keys still present, all zero


# ---- the breakdown has to sum to its own total (ADR-213) -------------------------------

def test_apportion_parts_sum_to_the_whole():
    """⭐⭐ **The obvious implementation is wrong and shipped that way for months.**

    `by_gameweek` rounded each gameweek independently while `xp` rounded the *sum* — and a rounded sum is not
    a sum of rounded values. On the real board at horizon 5, **253 of 662 players** disagreed with their own
    breakdown by up to 0.20 points, while the comment beside the field claimed it *"sums to `xp`"*.
    """
    from src.analytics.xp import apportion

    # The canonical failure: three values that each round up, so the parts exceed the whole.
    vals = {1: 2.06, 2: 2.06, 3: 2.06}
    total = round(sum(vals.values()), 1)                     # 6.2
    out = apportion(vals, total)
    assert round(sum(out.values()), 1) == total
    assert sorted(out.values()) == [2.0, 2.1, 2.1], "the spare tenth goes to one gameweek, not all three"

    # And the opposite direction — values that each round down.
    vals = {1: 2.04, 2: 2.04, 3: 2.04}
    total = round(sum(vals.values()), 1)                     # 6.1
    assert round(sum(apportion(vals, total).values()), 1) == total


def test_apportion_never_moves_a_value_more_than_one_tenth():
    """⚠️ Making the parts sum is easy if you are allowed to lie about them. This is the constraint that
    stops the fix being worse than the bug — every cell stays within rounding distance of its true value."""
    import random

    from src.analytics.xp import apportion

    rng = random.Random(7)
    for _ in range(5000):
        vals = {g: rng.uniform(0, 9) for g in range(rng.randint(1, 8))}
        total = round(sum(vals.values()), 1)
        out = apportion(vals, total)
        assert abs(round(sum(out.values()), 1) - total) < 1e-9
        for g, v in vals.items():
            assert abs(out[g] - v) <= 0.1 + 1e-9, f"gw {g} moved {abs(out[g]-v)} from {v}"


def test_apportion_is_deterministic():
    """Two runs must agree, or the published board churns for no reason and a diff is meaningless."""
    from src.analytics.xp import apportion

    vals = {1: 1.05, 2: 1.05, 3: 1.05, 4: 1.05}
    total = round(sum(vals.values()), 1)
    assert apportion(vals, total) == apportion(vals, total)


def test_apportion_handles_an_empty_horizon():
    """A player with no fixtures in the window — a blank gameweek, or a club already finished."""
    from src.analytics.xp import apportion

    assert apportion({}, 0.0) == {}


def test_every_real_breakdown_sums_to_its_own_total():
    """⚠️ **The guard that matters, and the three above did not provide it.**

    Mutation-testing this file caught it: restoring the old `{gw: round(v, 1)}` line left all three
    `apportion` tests green, because they exercise the helper and never assert that `decision_xp` *calls*
    it. ⭐ *Testing a component is not testing that anything uses it.*

    So this one asks the question a user would: take the real board, add up the column, and see whether it
    equals the number printed beside it.
    """
    from src.analytics.xp import decision_xp
    from src.storage import Storage

    store = Storage()
    players, upcoming = store.get_players(), store.get_upcoming_fixtures()
    history, gw_history = store.get_history_by_code(), store.get_gw_history_by_code()

    for horizon in (1, 3, 5, 8):
        board = decision_xp(players, upcoming, history, horizon=horizon,
                            gw_history_by_code=gw_history)
        assert board, "the snapshot must have players, or this proves nothing"
        wrong = [(r["web_name"], r["xp"], round(sum(r["by_gameweek"].values()), 2))
                 for r in board if abs(sum(r["by_gameweek"].values()) - r["xp"]) > 1e-9]
        assert not wrong, (
            f"horizon {horizon}: {len(wrong)} of {len(board)} breakdowns do not sum to their total "
            f"— e.g. {wrong[:3]}")
