"""The run card's numbers, and who the last five were against (ADR-242).

⭐⭐ **Both were data the client drew a space for and never received.** The pitch's run mode drew three
columns of expected points and `by_gameweek` carried one, because it follows the request's `horizon` — and
the horizon is 1, since the headline beside it is a **this-week** projection. Two of the three columns read
`—` on every card, on every squad, from the day ADR-235 shipped.

⚠️ *A field that is absent renders as a dash, and a dash reads as "no data for this player" rather than as
"this endpoint was never asked for it".*
"""

import pytest

from src import service
from src.service.answers import RUN, _recent_rows
from src.storage import Storage


@pytest.fixture(scope="module")
def store():
    s = Storage()
    yield s
    s.close()


@pytest.fixture(scope="module")
def squad(store):
    """A legal fifteen — the same construction the samples use."""
    need = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}
    picked, per_club = [], {}
    for p in store.get_players():
        if need.get(p["position"], 0) and per_club.get(p["team"], 0) < 3 and len(picked) < 15:
            picked.append(p["id"])
            need[p["position"]] -= 1
            per_club[p["team"]] = per_club.get(p["team"], 0) + 1
    return picked


# ── the run window ───────────────────────────────────────────────────────────────────────────────

def test_the_run_carries_a_number_for_every_fixture_it_draws(store, squad):
    """⭐ The whole bug in one assertion: as many gameweeks of xP as there are fixture columns."""
    answer = service.analysis(service.SquadRequest(player_ids=squad, horizon=1), store=store)
    assert len(answer["xi"][0]["by_gameweek"]) == 1, "the headline is still a one-week projection"

    wide = service.analysis(service.SquadRequest(player_ids=squad, horizon=RUN), store=store)
    assert len(wide["xi"][0]["by_gameweek"]) == RUN


def test_widening_the_run_does_not_widen_the_headline(store, squad):
    """⚠️⚠️ **Why this is a second pass rather than `horizon=3`.**

    Raising the horizon changes `projected_xp` from a week's points to three weeks' — on the owner's own
    squad, 44.9 → 133.9. ⭐ *A three-week total wearing a one-week label is a worse bug than the one being
    fixed*, so the two numbers are computed separately and this test pins them apart.
    """
    one = service.analysis(service.SquadRequest(player_ids=squad, horizon=1), store=store)
    three = service.analysis(service.SquadRequest(player_ids=squad, horizon=RUN), store=store)
    assert three["projected_xp"] > one["projected_xp"] * 1.5, (
        "a three-week projection should be materially larger than a one-week one — if it is not, the "
        "horizon is not doing what this test assumes and the rest of the reasoning is unsafe"
    )


def test_my_team_sends_the_run_its_numbers_even_at_horizon_one(store, squad):
    """⭐⭐⭐ **The actual bug, asserted where it lived.**

    ⚠️ A mutation that made `my_team` reuse the narrow answer — *exactly the shipped behaviour before this
    change* — left every other test in this file green, because they all exercise `analysis` rather than
    the composition that drew the card. ⭐ *A test one layer away from the defect passes through it.*
    """
    from src.service import answers

    picks = {"name": "Test XI", "player_ids": squad, "bench_ids": squad[-4:],
             "captain_id": squad[0], "vice_captain_id": squad[1]}
    real = answers.fetch_manager_team
    answers.fetch_manager_team = lambda entry_id, players: (picks, "")
    try:
        out = service.my_team(service.MyTeamRequest(manager_id=1, horizon=1), store=store)
    finally:
        answers.fetch_manager_team = real

    assert out["run"] == RUN
    assert len(out["run_xp"]) == 15, "every player in the fifteen needs his run"
    for row in out["run_xp"]:
        assert len(row["by_gameweek"]) == RUN, (
            f"player {row['id']} has {len(row['by_gameweek'])} gameweeks for a {RUN}-fixture run — "
            f"the card draws {RUN} columns and the missing ones render as dashes"
        )

    # ⚠️ And the headline is still a single week, which is the whole reason for the second pass.
    assert len(out["analysis"]["gameweeks"]) == 1


def test_a_wide_request_does_not_pay_for_a_second_pass(store, squad):
    """⭐ When the caller already asked for a window at least as wide as the run, the answer is reused."""
    from src.service import answers

    picks = {"name": "Test XI", "player_ids": squad, "bench_ids": squad[-4:],
             "captain_id": squad[0], "vice_captain_id": squad[1]}
    calls = []
    real_analysis, real_fetch = answers.analysis, answers.fetch_manager_team
    answers.fetch_manager_team = lambda entry_id, players: (picks, "")

    def counting(req, *, store=None):
        calls.append(req.horizon)
        return real_analysis(req, store=store)

    answers.analysis = counting
    try:
        service.my_team(service.MyTeamRequest(manager_id=1, horizon=RUN), store=store)
    finally:
        answers.analysis, answers.fetch_manager_team = real_analysis, real_fetch
    assert calls == [RUN], f"expected one analysis pass, got {calls}"


# ── who they played ──────────────────────────────────────────────────────────────────────────────

CLUBS = {1: "ARS", 2: "AVL", 3: "BUR"}


def test_an_appearance_says_who_it_was_against():
    rows = _recent_rows([{"round": 4, "total_points": 2, "minutes": 90,
                          "opponent_team": 1, "was_home": True}], CLUBS)
    assert rows == [{"gameweek": 4, "points": 2, "minutes": 90, "opponent": "ARS", "home": True}]


def test_an_unknown_club_is_null_and_never_a_guess():
    """⚠️ An away trip to "???" is worse than an away trip to nothing — the client renders a dash."""
    rows = _recent_rows([{"round": 4, "total_points": 2, "minutes": 90,
                          "opponent_team": 99, "was_home": False}], CLUBS)
    assert rows[0]["opponent"] is None


def test_home_and_away_are_carried_separately_from_the_club():
    """⭐ Not folded into the name. The client decides how to show it (upper/lower case); the service
    says what happened. ⚠️ A prettified "vs ARS (H)" here would be a layout decision taken in the API."""
    home = _recent_rows([{"round": 1, "opponent_team": 2, "was_home": True}], CLUBS)[0]
    away = _recent_rows([{"round": 1, "opponent_team": 2, "was_home": False}], CLUBS)[0]
    assert home["opponent"] == away["opponent"] == "AVL"
    assert home["home"] is True and away["home"] is False


def test_the_live_endpoint_carries_both(store):
    """⭐ Against the real board, not a constructed row — the join has to actually find the clubs."""
    someone = next(p for p in store.get_players() if p["minutes"] and p["minutes"] > 200)
    answer = service.player(service.PlayerRequest(player_id=someone["id"], horizon=5), store=store)
    assert answer["recent"], f"{someone['web_name']} has minutes but no appearances"
    named = [r for r in answer["recent"] if r["opponent"]]
    assert named, "no appearance named an opponent — the club join found nothing"
    for row in answer["recent"]:
        assert set(row) == {"gameweek", "points", "minutes", "opponent", "home"}
