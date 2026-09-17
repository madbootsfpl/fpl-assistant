"""A doubt is a probability, not a verdict (ADR-206).

`xp._status_is_active` was `p["status"] == "a"`, so **every doubtful player projected exactly 0.0** —
23 of them on the day this was found, at chance values of 25, 50 and 75, all priced identically. Meanwhile
`chance_factor` (ADR-038) computed the correct 0.75 multiplier and never got to apply it, because the binary
gate ran first and returned False.

⭐⭐ **TWO MECHANISMS MODELLED THE SAME THING AND THE CRUDER ONE RAN FIRST**, making the finer one dead code
for exactly the population it was written for.

⚠️ **The whole suite stayed green through the fix** — 1842 tests, not one of them red, while 23 players moved
from 0.0 to real projections. Nothing had ever asserted what a *doubtful* player is worth. These do.
"""

import pytest

from src.analytics.minutes import UNAVAILABLE, chance_factor, is_unavailable
from src.analytics.xp import _status_is_active, player_xp


def _p(pid, pos="FWD", status="a", chance=None, ppg=6.0, team="ARS", tid=1):
    return {"id": pid, "code": pid, "web_name": f"P{pid}", "position": pos, "team": team, "team_id": tid,
            "price": 7.0, "status": status, "chance": chance, "total_points": 40, "points_per_game": ppg,
            "minutes": 360, "form": 0.0, "ep_next": 0.0, "selected_by": 5.0, "penalties_order": None,
            "corners_order": None, "freekicks_order": None, "cost_change_event": 0,
            "transfers_in_event": 0, "xgc": 1.0, "clean_sheets": 0}


def _fixtures():
    return [{"event": 1, "team_h": 1, "team_a": 2, "team_h_difficulty": 3, "team_a_difficulty": 3,
             "home": "ARS", "away": "SUN", "kickoff_time": None,
             "home_team_strength": 3, "away_team_strength": 3}]


def _xp(players, **kw):
    weight = kw.pop("minutes_weight", lambda p: chance_factor(p))
    return {r["web_name"]: r["xp"] for r in
            player_xp(players, _fixtures(), horizon=1, minutes_weight=weight, **kw)}


# --- the gate answers a different question from the chance factor ---------------------

def test_a_doubtful_player_is_not_treated_as_unavailable():
    """The bug, at its smallest. `status == 'a'` is not the same question as *can he play*."""
    assert _status_is_active(_p(1, status="d", chance=75)) is True
    assert is_unavailable(_p(1, status="d", chance=75)) is False
    for gone in ("i", "s", "u", "n"):
        assert _status_is_active(_p(1, status=gone)) is False, gone


def test_a_seventy_five_percent_doubt_is_worth_three_times_a_twenty_five_percent_one():
    """⚠️ **The heart of it: these two used to price IDENTICALLY, at zero.** A model that cannot tell a
    near-certain starter from a long shot is not being cautious, it is being silent."""
    likely, unlikely = _p(1, status="d", chance=75), _p(2, status="d", chance=25)
    out = _xp([likely, unlikely])
    assert out["P1"] > 0 and out["P2"] > 0, "a doubtful player must carry SOME value"
    assert out["P1"] == pytest.approx(3 * out["P2"], rel=0.02), (
        f"75% must be worth three times 25%, not the same: {out}")


def test_a_doubtful_player_keeps_most_of_his_value_against_a_weaker_fit_one():
    """The owner's case, in miniature: an 8.2-ppg forward at 75% against a 4.2-ppg forward who is fit.

    The old gate made this a landslide for the fit player (0.0 against a real number) and the app recommended
    the transfer at **+4.7 XI xP**. Priced properly it is **+0.6** — inside the noise floor, which is a
    completely different sentence.
    """
    hot_but_doubtful = _p(1, status="d", chance=75, ppg=8.2)
    fit_but_worse = _p(2, status="a", ppg=4.2)
    out = _xp([hot_but_doubtful, fit_but_worse])
    assert out["P1"] > 0, "the old gate zeroed him outright"
    assert abs(out["P1"] - out["P2"]) < out["P2"], (
        f"the two must be close, not a landslide: {out}")


def test_the_horizon_does_not_escape_the_flag_but_the_flag_does_not_zero_it():
    """⚠️ A doubt about tomorrow used to read `{0.0, 0.0, 0.0, 0.0, 0.0}` — the app saying a player with a
    knock would score nothing for **five gameweeks**, two of them after a 19-day international break.

    §1 fixes the zero. It deliberately does **not** fix the flatness: 0.75 still applies to every gameweek in
    the horizon, which is ADR-206 §2's problem and is left open on purpose rather than half-solved here.
    """
    out = player_xp([_p(1, status="d", chance=75)], _fixtures(), horizon=1,
                    minutes_weight=chance_factor)
    assert out[0]["xp"] > 0
    assert all(v >= 0 for v in out[0]["by_gameweek"].values())


def test_an_unregistered_player_is_not_assumed_available():
    """⚠️ Closing a hole the fix would otherwise have opened. `"n"` (not in the squad) was missing from
    `minutes`' set, and his `chance` is None — which `chance_factor` reads as *"no news, assume available"*
    and returns **1.0**. Letting non-'a' statuses through the gate without this would have priced a player
    who is not registered at full value."""
    assert "n" in UNAVAILABLE
    assert chance_factor(_p(1, status="n")) == 0.0
    assert _xp([_p(1, status="n")])["P1"] == 0.0


def test_the_three_definitions_of_unavailable_are_now_one():
    """⭐ It lived in three places that disagreed — here, in `optimizer`, and in `xp`'s binary. A fix in one
    of three definitions is a fix in one third of the app."""
    from src.analytics import optimizer
    assert optimizer.UNAVAILABLE_STATUS is UNAVAILABLE
    assert optimizer.is_unavailable(_p(1, status="d")) is False


def test_the_captain_picker_still_counts_doubtful_players():
    """⚠️ `captain.py` carried `is_available=lambda p: not is_unavailable(p)  # count doubtful, not only 'a'`
    — a **local workaround for this exact bug**, written at one call site and left everywhere else.

    ⭐ *A workaround at one call site is a bug report nobody filed.* The override is now removed because it
    equals the default; this pins the behaviour so removing it cannot silently regress.
    """
    from src.analytics.captain import captain_picks

    players = [_p(1, status="d", chance=75, ppg=9.0), _p(2, status="a", ppg=4.0)]
    picks = captain_picks(players, _fixtures())
    names = [c["web_name"] for c in picks]
    assert "P1" in names, f"a doubtful player must still be a captaincy candidate: {names}"
    assert all(c["xp"] > 0 for c in picks if c["web_name"] == "P1"), (
        "…and must carry a real projection, not a zero that keeps him in the list decoratively")
