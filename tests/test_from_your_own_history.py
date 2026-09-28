"""Three tester questions, one endpoint (ADR-318).

⭐⭐ *"Should the build number be in Settings?"* · *"How does FFH know how many transfers you have?"* ·
*"Could you show rank places dropped or gained with a red/green arrow?"*

⭐ The last two are answered by `get_entry_history`, which this app has called since ADR-234 for chips —
*a call worth making once is worth making once.*
"""

from __future__ import annotations

import pytest

from src.fpl_rules import FT_CAP, free_transfers_from_history, rank_movement


def weeks(*pairs, chips=None):
    """`(event, transfers)` pairs → the shape FPL's `history.current` has."""
    return [{"event": e, "event_transfers": n, "overall_rank": None} for e, n in pairs]


# ── free transfers ───────────────────────────────────────────────────────────

def test_an_untouched_season_reaches_the_cap() -> None:
    """⭐ One a week, rolling over — five gameweeks of no moves and you are at the ceiling."""
    assert free_transfers_from_history(weeks((1, 0), (2, 0), (3, 0), (4, 0), (5, 0))) == FT_CAP


def test_they_do_not_roll_past_the_cap() -> None:
    assert free_transfers_from_history(weeks(*[(n, 0) for n in range(1, 15)])) == FT_CAP


def test_spending_them_spends_them() -> None:
    # ⚠️ GW1 earns nothing (ADR-327) and a move made then costs points, not a bank; GW2 and GW3 each earn
    # one and GW3 spends its own → one banked, plus the week ahead = 2.
    assert free_transfers_from_history(weeks((1, 1), (2, 0), (3, 1))) == 2


def test_a_hit_costs_points_not_future_transfers() -> None:
    """⚠️ Four moves on one free transfer is a −12 hit, **not** a negative bank — ⭐ *transfers beyond
    the free ones cost points, and the next week still brings one.*"""
    assert free_transfers_from_history(weeks((1, 4))) == 1


@pytest.mark.parametrize("chip", ["wildcard", "freehit"])
def test_a_chip_week_leaves_the_bank_alone(chip) -> None:
    """⚠️⚠️ **This is why the chip list matters here and not only for chip advice.** A wildcard makes the
    week's transfers free; ⭐ *it does not spend the ones you saved.*"""
    played = [{"event": 2, "name": chip}]

    banked = free_transfers_from_history(weeks((1, 0), (2, 9)), played)
    spent = free_transfers_from_history(weeks((1, 0), (2, 9)))

    # ⚠️ **Two, not three** (ADR-327). GW2 is the first week that earns a transfer; the chip then spends
    # none of it, so one is banked and the week ahead brings the second. The old value of 3 counted a GW1
    # transfer FPL never issued — ⭐ *this test was written against the implementation, so it agreed with
    # the bug and kept agreeing.*
    assert banked == 2, "the chip week ate the saved transfers"
    assert spent == 1, "…and without the chip, nine moves should have emptied them"


def test_no_history_assumes_the_opening_one() -> None:
    assert free_transfers_from_history([]) == 1


# ── rank movement ────────────────────────────────────────────────────────────

def ranks(*pairs):
    return [{"event": e, "overall_rank": r} for e, r in pairs]


def test_a_smaller_number_is_a_better_position() -> None:
    """⚠️⚠️⚠️ **The inversion, which is the entire reason this lives in the rules module.** A rank of
    167,946 is *better* than 463,077 — ⭐ *a falling number is a rising position*, and doing that
    arithmetic in each client repeats the trap on each surface."""
    assert rank_movement(ranks((3, 463_077), (4, 167_946)), 4) == 295_131


def test_a_larger_number_is_a_drop() -> None:
    assert rank_movement(ranks((4, 167_946), (5, 292_349)), 5) == -124_403


def test_the_first_gameweek_has_nothing_to_compare_with() -> None:
    assert rank_movement(ranks((1, 1_987_556)), 1) is None


def test_a_missing_neighbour_is_unknown_not_zero() -> None:
    """⭐ *"We could not check" is not "no movement"* — and a 0 would have said the second."""
    assert rank_movement(ranks((2, 404_244), (4, 167_946)), 4) is None
    assert rank_movement([], 4) is None


def test_standing_still_is_zero_not_none() -> None:
    """⭐ The counterpart: an unchanged rank is a **known** fact, and the client draws no arrow for it."""
    assert rank_movement(ranks((4, 500), (5, 500)), 5) == 0


# ── the build number ─────────────────────────────────────────────────────────

def test_settings_shows_which_build_this_is() -> None:
    """⚠️⚠️ **It already existed and was readable only when an update was available** — ⭐ *the number that
    settles "is this the version with the fix?" was shown only to people who were already behind.*"""
    import pathlib

    settings = (pathlib.Path(__file__).resolve().parents[1]
                / "mobile/lib/settings_view.dart").read_text()

    assert "kAppBuild" in settings and "kAppVersion" in settings


def test_the_number_matches_fpls_own_for_the_manager_who_reported_it() -> None:
    """🔴 **The bug, as a tester met it** (ADR-327): *"calculated 4 transfers for manager ID 1467290, there
    are only 3 available."*

    ⭐ His real shape, taken from `/entry/1467290/history/` on 2026-09-28: five played gameweeks, moves of
    0·1·1·0·0, Bench Boost in GW2. FPL showed **3**; this function said **4**.

    ⚠️ Bench Boost is in the history deliberately — it is **not** in `FT_FREE_CHIPS`, because it does not
    make transfers free, and a fix that quietly widened that set would pass this test for the wrong reason.
    """
    history = weeks((1, 0), (2, 1), (3, 1), (4, 0), (5, 0))
    assert free_transfers_from_history(history, [{"event": 2, "name": "bboost"}]) == 3


def test_the_first_gameweek_does_not_issue_one() -> None:
    """⭐ The root cause, stated on its own so it cannot regress silently. FPL's first free transfer arrives
    **after** the GW1 deadline, for GW2 — before that the squad is unlimited to edit, which is not a
    transfer anyone can bank."""
    assert free_transfers_from_history(weeks((1, 0))) == 1, "GW1 played, none spent → one for GW2"
    assert free_transfers_from_history(weeks((1, 0), (2, 0))) == 2, "…and two for GW3"
