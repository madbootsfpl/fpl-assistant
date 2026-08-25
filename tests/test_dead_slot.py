"""Tests for the dead-slot detector (ADR-136).

A dead slot is a squad place that cannot score — and the *whole* design lives in telling one apart from a
player who is merely out this week. `decision_xp` scores all 94 currently-unavailable players at 0.00 and
cannot separate them, because `chance_of_playing_next_round` is 0 for every one of them by definition. The
only signal is FPL's free-text `news`, so that is what these pin.

The news shapes below are the four that actually exist in the live data (2026-08-25), not invented ones.
"""

from datetime import date

import pytest

from src.analytics.dead_slot import dead_slots, gameweeks_missed, return_date

TODAY = date(2026, 8, 25)


def _p(pid, name, team="HUL", pos="FWD", status="u", news="", price=4.5):
    return {"id": pid, "web_name": name, "team": team, "position": pos, "status": status,
            "news": news, "price": price, "chance": 0}


def _fx(event, home, away, kickoff):
    return {"event": event, "home": home, "away": away, "kickoff_time": kickoff}


# Five gameweeks, one HUL fixture each, a week apart.
FIXTURES = [_fx(2, "HUL", "COV", "2026-08-29T14:00:00Z"),
            _fx(3, "ARS", "HUL", "2026-09-05T14:00:00Z"),
            _fx(4, "HUL", "LIV", "2026-09-12T14:00:00Z"),
            _fx(5, "TOT", "HUL", "2026-09-19T14:00:00Z"),
            _fx(6, "HUL", "MCI", "2026-09-26T14:00:00Z")]


# ---- the parse -----------------------------------------------------------------------

@pytest.mark.parametrize("news,expected", [
    ("Calf injury - Expected back 5 Sep", date(2026, 9, 5)),
    ("Ankle injury - Expected back 14 Sep", date(2026, 9, 14)),
    ("Leg injury - Expected back 28 Nov", date(2026, 11, 28)),
    ("Suspended until 19 Sep", date(2026, 9, 19)),          # FPL's other dated form
])
def test_the_two_dated_news_forms_parse(news, expected):
    """Both live phrasings end in `<D Mon>`; 8 of 8 dated players parsed on the real data."""
    assert return_date(_p(1, "X", news=news), today=TODAY) == expected


@pytest.mark.parametrize("news", [
    "Has joined Konyaspor permanently",                     # a departure — no date exists
    "has returned to Getafe CF",                            # the lower-cased variant, also live
    "Unspecified injury - Unknown return date",             # the largest group: 47 players
    "", "Knock", "Expected back soon", "Expected back 31 Feb",
])
def test_anything_without_a_usable_date_returns_none(news):
    """`None` is the common case and covers a departure, an unknown return, and news we couldn't parse — the
    callers deliberately treat all three the same way: there is no date to wait for."""
    assert return_date(_p(1, "X", news=news), today=TODAY) is None


def test_the_year_is_inferred_because_fpl_never_writes_one():
    """A season runs August → May, so a month *earlier* than today's belongs to next year. December→January is
    the only place this can break, so that is where it is pinned."""
    assert return_date(_p(1, "X", news="Expected back 10 Jan"), today=date(2026, 8, 25)) == date(2027, 1, 10)
    assert return_date(_p(1, "X", news="Expected back 3 Feb"), today=date(2026, 12, 28)) == date(2027, 2, 3)
    assert return_date(_p(1, "X", news="Expected back 20 Jan"), today=date(2027, 1, 5)) == date(2027, 1, 20)


# ---- horizon arithmetic --------------------------------------------------------------

def test_a_dated_return_is_counted_in_gameweeks_not_days():
    """The number the advice actually wants. "Back 5 Sep" is only meaningful next to your fixtures."""
    assert gameweeks_missed(_p(1, "X", news="Expected back 5 Sep"), FIXTURES, today=TODAY) == (1, 5)
    assert gameweeks_missed(_p(1, "X", news="Expected back 28 Nov"), FIXTURES, today=TODAY) == (5, 5)
    assert gameweeks_missed(_p(1, "X", news="Unknown return date"), FIXTURES, today=TODAY) == (5, 5)


def test_a_blank_gameweek_is_not_counted_against_him():
    """`total` counts only the gameweeks his team plays in — there was nothing to miss in a blank."""
    blank = [f for f in FIXTURES if f["event"] != 4]
    assert gameweeks_missed(_p(1, "X", news="Unknown return date"), blank, today=TODAY) == (4, 4)


def test_returning_for_the_second_match_of_a_double_is_not_missing_that_week():
    """A gameweek counts as missed only when **every** one of his team's fixtures in it kicks off before he is
    back. Otherwise a DGW return would be scored as an absence."""
    dgw = FIXTURES + [_fx(3, "HUL", "EVE", "2026-09-08T19:00:00Z")]   # GW3 becomes a double
    p = _p(1, "X", news="Expected back 7 Sep")             # back between the two GW3 matches
    assert gameweeks_missed(p, dgw, today=TODAY) == (1, 5)


# ---- the verdict ---------------------------------------------------------------------

def test_a_departed_player_is_a_dead_slot_and_says_why():
    """The reported case. Naming the reason is most of the value: "has joined Inter" is what makes a manager
    act, where "a low-xP forward" does not."""
    gone = _p(1, "Destan", news="Has joined Konyaspor permanently")
    (slot,) = dead_slots([gone], FIXTURES, today=TODAY)
    assert slot["reason"] == "gone" and (slot["missed"], slot["total"]) == (5, 5)


def test_a_short_dated_absence_is_NOT_a_dead_slot():
    """Doku — £7.5m, calf, back 5 Sep, about two gameweeks. This is the case the whole design exists for:
    selling a premium to fill a two-week hole is worse advice than the "hold" being fixed."""
    doku = _p(2, "Doku", team="HUL", status="i", news="Calf injury - Expected back 5 Sep", price=7.5)
    assert dead_slots([doku], FIXTURES, today=TODAY) == []


def test_a_long_dated_absence_IS_a_dead_slot_and_carries_its_date():
    """Minteh — back 28 Nov, functionally identical to a departure over any horizon you're planning on. The
    reason string carries the date so a manager who disagrees can see what we're standing on."""
    minteh = _p(3, "Minteh", status="i", news="Leg injury - Expected back 28 Nov")
    (slot,) = dead_slots([minteh], FIXTURES, today=TODAY)
    assert slot["reason"] == "out until 28 Nov"


def test_an_unknown_return_is_a_dead_slot():
    """47 of the 94 unavailable players — the largest group. There is no date to wait for."""
    (slot,) = dead_slots([_p(4, "Saliba", status="i", news="Back injury - Unknown return date")],
                         FIXTURES, today=TODAY)
    assert slot["reason"] == "no return date"


def test_an_available_player_is_never_a_dead_slot():
    assert dead_slots([_p(5, "Salah", status="a", news="")], FIXTURES, today=TODAY) == []


def test_a_doubtful_player_is_not_a_dead_slot():
    """`d` is a warning, not an absence — he is expected to play and is kept in the XI (ADR-023)."""
    assert dead_slots([_p(6, "Doubtful", status="d", news="Knock - 75% chance of playing")],
                      FIXTURES, today=TODAY) == []


def test_an_unparseable_date_leaves_the_advice_exactly_as_it_was():
    """The failure direction, chosen on purpose. Missing a dead slot leaves the manager where they already
    are; inventing one costs them a transfer. So garbage in the news resolves toward **silence**, not a sell.

    (`u` still reads as gone — that comes from the status field, not the text.)
    """
    weird = _p(7, "X", status="i", news="Expected back when the vibes are right")
    assert dead_slots([weird], FIXTURES, today=TODAY)[0]["reason"] == "no return date"
    # …and a *dated* one we can read is still respected rather than treated as noise
    assert dead_slots([_p(8, "Y", status="i", news="Expected back 5 Sep")], FIXTURES, today=TODAY) == []


def test_no_fixtures_means_no_verdict_rather_than_a_guess():
    """Out of season, or a team with nothing scheduled: we cannot say he misses anything, so we don't."""
    assert dead_slots([_p(9, "X", news="Has joined Konyaspor permanently")], [], today=TODAY) == []
