"""Team defence is measured with xGC, not clean sheets (ADR-195).

ADR-188 built the clean-sheet term on a club's **clean-sheet rate**, and over four gameweeks that is a
five-valued statistic derived from a coin flip. It read a null. A second look (ADR-190 Option 3) read a null
too, and the owner was told twice that his instinct was not supported by the data. ⭐⭐ *A null is a statement
about the instrument as much as about the world.*

xGC/90 is continuous, minutes-normalised, and spreads 3x across the league on the same four gameweeks.

⚠️ **These guards exist because the suite could not see this change at all.** `CLEAN_SHEET_WEIGHT` is 0, and
`decision_xp` does not even call `_clean_sheet_rates` at weight 0 — so every one of ADR-188's five guards
stayed green through a change to the rate's units, its source and its sign. ⭐ *A dormant term is a term no
test runs; it has to be driven deliberately or it is not covered, it is merely quiet.*
"""

import math

import pytest

from src.analytics.cleansheet import clean_sheet_delta, clean_sheet_prob, league_clean_sheet_rate
from src.analytics.gw_form import TEAM_XGC_MIN_MINUTES, team_xgc90


def _gk(code, team, name="Keeper"):
    return {"code": code, "team": team, "position": "GK", "web_name": name, "id": code}


def _row(rnd, minutes, xgc, **kw):
    """A played round — a scoreline is what makes it played (ADR-125)."""
    base = {"round": rnd, "minutes": minutes, "xgc": xgc, "team_h_score": 1, "team_a_score": 0}
    base.update(kw)
    return base


# --- the instrument ------------------------------------------------------------------

def test_team_xgc_comes_from_the_keeper_and_is_minutes_normalised():
    """A keeper is on for the whole match, so his xGC is the team's — the same reasoning
    `team_clean_sheet_rate` already uses, and for the same reason."""
    players = [_gk(1, "ARS")]
    hist = {1: [_row(1, 90, 0.6), _row(2, 90, 0.7)]}
    assert team_xgc90(hist, players, "ARS") == pytest.approx(0.65), "1.3 xGC over 180 min is 0.65 per 90"


def test_a_benched_keeper_says_nothing_about_the_team():
    """⚠️ **The benched keeper is listed FIRST, deliberately.**

    A first version listed him second, and the mutant that deletes the `minutes <= 0` check **survived** —
    because the *other* guard (one row per round) had already claimed both rounds for the keeper who played,
    so the benched rows were dropped for a reason that had nothing to do with being benched.

    Listed first, he claims the rounds with **0 minutes and 0 xGC**, the real keeper's rows are then skipped
    as duplicates, and the club drops below the minutes floor and reads `None`. ⭐ *A fixture that only
    exercises the lucky ordering will confirm a broken mechanism* — and two guards covering one another is
    exactly the shape that hides it.
    """
    players = [_gk(2, "ARS", "Sub"), _gk(1, "ARS")]        # the benched one iterated FIRST
    hist = {2: [_row(1, 0, 0.0), _row(2, 0, 0.0)],         # never came on
            1: [_row(1, 90, 0.6), _row(2, 90, 0.7)]}
    assert team_xgc90(hist, players, "ARS") == pytest.approx(0.65), (
        "a benched keeper must not claim the round from the one who played it")


def test_a_match_still_in_flight_does_not_count():
    """⚠️ **A live gameweek has minutes but no scoreline** — the trap ADR-125 exists for. A club 45 minutes
    into a match it is losing would otherwise have that half-match priced as a full observation of its
    defence, and the recommendation would move mid-fixture.

    ⭐ *A scoreline is the only proof a match finished*, and `minutes > 0` is not a substitute for it: those
    two guards look redundant and are not, because a match in progress satisfies one and fails the other.
    """
    players = [_gk(1, "ARS")]
    hist = {1: [_row(1, 90, 0.6), _row(2, 90, 0.7),
                {"round": 3, "minutes": 45, "xgc": 1.8,            # in flight: no scoreline yet
                 "team_h_score": None, "team_a_score": None}]}
    assert team_xgc90(hist, players, "ARS") == pytest.approx(0.65), (
        "the unfinished round must contribute neither its xGC nor its minutes")


def test_two_keepers_sharing_a_match_are_counted_once():
    """⚠️ A red card or an injury puts two keepers in one match. Summing both rows would put **180 minutes**
    against a single match's xGC and halve the club's conceded rate — a defence that looks twice as good
    because its keeper got sent off."""
    players = [_gk(1, "ARS"), _gk(2, "ARS", "Sub")]
    hist = {1: [_row(1, 40, 0.9)], 2: [_row(1, 50, 0.9)]}   # same round, one match
    got = team_xgc90(hist, players, "ARS", min_minutes=40)
    assert got is not None
    assert got == pytest.approx(0.9 * 90 / 40), "one row per round — the second keeper's must not extend the denominator"


def test_a_club_below_the_minutes_floor_is_unknown_not_perfect():
    """⚠️ **The ADR-172 failure, not repeated.** Returning 0.0 would read as a flawless defence — the best
    possible value — for a club we know nothing about. Unknown must stay *no opinion*."""
    players = [_gk(1, "ARS")]
    assert team_xgc90({1: [_row(1, 90, 0.6)]}, players, "ARS") is None, "one match is below the floor"
    assert team_xgc90({}, players, "ARS") is None
    assert TEAM_XGC_MIN_MINUTES == 180


def test_a_round_with_no_xgc_is_skipped_rather_than_counted_as_zero():
    players = [_gk(1, "ARS")]
    hist = {1: [_row(1, 90, 0.6), _row(2, 90, None), _row(3, 90, 0.6)]}
    assert team_xgc90(hist, players, "ARS") == pytest.approx(0.6), "the None round contributes neither xGC nor minutes"


# --- the units, which is where this could have gone wrong quietly ---------------------

def test_xgc_becomes_a_probability_so_the_points_multiplier_still_means_points():
    """⚠️ **ADR-195 as written had a units bug.** It says *"swap clean-sheet rate for xGC/90 delta — a change
    to one function's argument"*, but `clean_sheet_delta` multiplies by `CLEAN_SHEET_POINTS`, and that only
    yields **points** when the delta is a **probability**. A raw goals-per-90 difference would produce
    "4 x goals" — a number in no unit at all, with a plausible sign and magnitude to hide behind.

    ⭐ *A swapped input has to arrive in the units the consumer already assumes* — and here the assumption
    lived in a `x 4` three lines away from the change.
    """
    assert clean_sheet_prob(0.0) == 1.0, "concede nothing expected → certain clean sheet"
    assert clean_sheet_prob(0.65) == math.exp(-0.65)
    assert 0.5 < clean_sheet_prob(0.65) < 0.6, "Arsenal-ish: a bit better than a coin flip"
    assert 0.1 < clean_sheet_prob(1.94) < 0.2, "Coventry-ish: roughly one in seven"


def test_the_sign_survives_the_swap_without_anyone_remembering_to_flip_it():
    """⭐ **The Poisson step fixes the direction for free, and that is a design property not a coincidence.**
    For clean-sheet *rate*, higher is better. For xGC, **lower** is better. A raw swap would have inverted
    the term — pricing Coventry's defenders above Arsenal's — while every existing guard stayed green,
    because they all test `team - league` and say nothing about which direction "good" points in.
    """
    good, bad = clean_sheet_prob(0.65), clean_sheet_prob(1.94)      # ARS vs COV
    assert good > bad, "the better defence must map to the higher clean-sheet probability"
    league = league_clean_sheet_rate({"ARS": good, "COV": bad})
    assert clean_sheet_delta({"position": "DEF"}, good, league) > 0, "a good defence must be a BONUS"
    assert clean_sheet_delta({"position": "DEF"}, bad, league) < 0, "a poor defence must be a PENALTY"


def test_an_unknown_club_stays_unknown_all_the_way_through():
    """None in, None out, and `clean_sheet_delta` already turns None into no adjustment. The chain only
    holds if every link preserves it — one `or 0` anywhere makes an unknown club the best in the league."""
    assert clean_sheet_prob(None) is None
    assert clean_sheet_delta({"position": "DEF"}, clean_sheet_prob(None), 0.3) == 0.0


# --- end to end, with the weight driven live -----------------------------------------

def test_with_the_weight_live_a_solid_defence_outranks_a_leaky_one():
    """The whole chain: per-GW rows → xGC/90 → probability → delta → xP. Driven at a **non-zero weight**,
    because at 0 `decision_xp` never calls the rate builder at all."""
    from src.analytics.xp import _clean_sheet_rates, player_xp

    def outfield(pid, name, team, tid):
        return {"id": pid, "code": pid, "web_name": name, "position": "DEF", "team": team,
                "team_id": tid, "price": 5.0, "status": "a", "chance": None, "total_points": 20,
                "points_per_game": 4.0, "minutes": 360, "form": 0.0, "ep_next": 0.0,
                "selected_by": 5.0, "penalties_order": None, "corners_order": None,
                "freekicks_order": None, "cost_change_event": 0, "transfers_in_event": 0,
                "xgc": 1.0, "clean_sheets": 0}

    players = [outfield(1, "Solid", "ARS", 1), outfield(2, "Leaky", "COV", 2)]
    gk_players = [_gk(11, "ARS"), _gk(12, "COV")]
    hist = {11: [_row(r, 90, 0.65) for r in (1, 2, 3, 4)],
            12: [_row(r, 90, 1.94) for r in (1, 2, 3, 4)]}

    rates = _clean_sheet_rates(gk_players, hist)
    assert rates["ARS"] > rates["COV"], "ARS must carry the higher clean-sheet probability"

    fixtures = [{"event": 1, "team_h": 1, "team_a": 2, "team_h_difficulty": 3,
                 "team_a_difficulty": 3, "home": "ARS", "away": "COV", "kickoff_time": None,
                 "home_team_strength": 3, "away_team_strength": 3}]
    out = {r["web_name"]: r["xp"] for r in player_xp(
        players, fixtures, horizon=1, clean_sheet_weight=1.0, clean_sheet_rates=rates)}
    assert out["Solid"] > out["Leaky"], (
        f"the solid defence must project higher once the term is live: {out}")
