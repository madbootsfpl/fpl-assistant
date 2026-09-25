"""A played gameweek, as the swipe-right screen needs it (ADR-298).

⭐⭐ **Almost all of this was already on the server.** The per-player week lives in `player_history`,
kept current by the pipeline; the one thing FPL alone knows is whose team he was in that week. These
tests pin the decisions that shape what comes back, not the arithmetic of FPL's own scoring.
"""

from __future__ import annotations

import pytest

from src.api import client as fpl_client
from src.service import GameweekResultRequest, gameweek_result
from src.storage import Storage


class FakeFpl:
    """FPL's picks payload for one gameweek, in FPL's own shape."""

    def __init__(self, payload=None, raises=False, live=None, live_raises=False):
        self._payload, self._raises = payload, raises
        self._live, self._live_raises = live, live_raises

    def get_entry_picks(self, entry_id, gameweek):
        if self._raises:
            raise fpl_client.FplApiError("not published")
        return self._payload

    def get_event_live(self, gameweek):
        """FPL's own points attribution for the week (ADR-299).

        ⚠️ Defaults to an **empty** payload rather than being absent: every existing test in this file
        goes through `gameweek_result`, which now makes this call, and ⭐ *a fake that is missing a method
        the code under test calls turns one new feature into fourteen red tests about something else.*
        """
        if self._live_raises:
            raise fpl_client.FplApiError("live is down")
        return self._live or {"elements": []}


def picks(elements, *, captain=None, subs=(), chip=None, **history):
    base = {"points": 50, "overall_rank": 1_000_000, "rank": 4,
            "event_transfers": 1, "event_transfers_cost": 0, "points_on_bench": 3}
    return {
        "active_chip": chip,
        "automatic_subs": [{"element_out": o, "element_in": i} for o, i in subs],
        "entry_history": {**base, **history},
        "picks": [
            {"element": e, "position": n + 1, "multiplier": 2 if e == captain else (0 if n >= 11 else 1),
             "is_captain": e == captain, "is_vice_captain": False}
            for n, e in enumerate(elements)
        ],
    }


@pytest.fixture
def squad_ids():
    """Fifteen real ids from the committed fixture, so names and positions resolve."""
    store = Storage()
    try:
        return [p["id"] for p in store.get_players()[:15]]
    finally:
        store.close()


def run(monkeypatch, payload, gameweek=5, raises=False, live=None, live_raises=False):
    monkeypatch.setattr(fpl_client, "FplClient",
                        lambda *a, **k: FakeFpl(payload, raises, live, live_raises))
    return gameweek_result(GameweekResultRequest(manager_id=1, gameweek=gameweek))


def test_a_gameweek_fpl_has_not_published_is_not_an_error(monkeypatch, squad_ids):
    """⭐⭐ **Swiping past the present is a normal gesture**, not a failure.

    ⚠️ *A screen that can be swiped into before the data exists must have something true to draw* — so
    this degrades like `my_team` rather than raising.
    """
    answer = run(monkeypatch, None, gameweek=38, raises=True)

    # ⭐ **Every key is present and empty, none is missing.** `kits` arrived with the pitch and joined the
    # rest — ⚠️ *a degraded answer that drops fields makes the client handle two shapes, and the second
    # one only ever appears on the path nobody tests by hand.*
    assert answer == {"gameweek": 38, "played": False, "squad": [],
                      "kits": {}, "summary": {}}


def test_the_squad_is_the_one_from_that_week(monkeypatch, squad_ids):
    answer = run(monkeypatch, picks(squad_ids))

    assert answer["played"] is True
    assert [e["player"]["id"] for e in answer["squad"]] == squad_ids
    assert all(e["player"]["web_name"] for e in answer["squad"])


def test_the_bench_is_where_it_was_set(monkeypatch, squad_ids):
    # ⭐ Positions 12-15 are the bench **as set**, before any automatic substitution.
    answer = run(monkeypatch, picks(squad_ids))

    assert [e["pick"]["benched"] for e in answer["squad"]] == [False] * 11 + [True] * 4


def test_an_automatic_sub_is_shown_as_what_happened(monkeypatch, squad_ids):
    """⚠️ The bench says what you *chose*; `came_on` says what the game *did*.

    ⭐ *A screen that shows only the choice makes a week look like a decision nobody revised.*
    """
    out, came = squad_ids[10], squad_ids[11]
    answer = run(monkeypatch, picks(squad_ids, subs=[(out, came)]))
    by_id = {e["player"]["id"]: e for e in answer["squad"]}

    assert by_id[came]["pick"]["came_on"] is True
    assert by_id[out]["pick"]["went_off"] is True
    # ⚠️ And the one who came on is still recorded as having been benched — both facts are true.
    assert by_id[came]["pick"]["benched"] is True


def test_a_double_gameweek_sums_both_matches(monkeypatch, squad_ids):
    """⚠️⚠️ Keyed on the **round**, so a player with two fixtures contributes both.

    ⭐ *Showing one of two matches is worse than showing neither, because it looks complete.*

    ⚠️ **The double is seeded, because the season has not had one yet.** Reading the fixture's own rows
    and asserting they sum made the test agree with any implementation — ⭐ *a test whose expectation is
    computed the same way as the answer cannot tell you the answer is wrong.*
    """
    store = Storage()
    try:
        players = {p["id"]: p for p in store.get_players()}
        code = players[squad_ids[0]]["code"]
    finally:
        store.close()

    def doubled(self):
        row = {"round": 5, "total_points": 6, "minutes": 90, "goals_scored": 1, "assists": 0,
               "bonus": 1, "saves": 0, "clean_sheets": 0, "yellow_cards": 1, "red_cards": 0}
        return {code: [dict(row), dict(row)]}

    monkeypatch.setattr(Storage, "get_gw_history_by_code", doubled)
    first = run(monkeypatch, picks(squad_ids))["squad"][0]["result"]

    assert first["points"] == 12, "both matches must count"
    assert first["minutes"] == 180
    assert first["goals"] == 2
    assert first["yellow_cards"] == 2


def test_the_summary_is_fpls_own_numbers(monkeypatch, squad_ids):
    """⭐ Points, rank and the hit come from `entry_history` — ⚠️ *recomputing a settled fact is offering
    a second opinion on it*, and FPL's total already includes the captain and the bonus."""
    answer = run(monkeypatch, picks(squad_ids, points=77, overall_rank=3_842_466,
                                    event_transfers=2, event_transfers_cost=4, points_on_bench=8))

    assert answer["summary"] == {
        "points": 77, "overall_rank": 3_842_466, "rank": 4,
        "transfers": 2, "hit": 4, "bench_points": 8, "chip": None,
    }


def test_a_chip_is_carried(monkeypatch, squad_ids):
    assert run(monkeypatch, picks(squad_ids, chip="bboost"))["summary"]["chip"] == "bboost"


def test_cards_are_reported(monkeypatch, squad_ids):
    """⭐ The field the owner named. ⚠️ Integers, never null, so the client renders nothing rather than
    a blank badge for a player who was not booked."""
    answer = run(monkeypatch, picks(squad_ids))

    for entry in answer["squad"]:
        assert isinstance(entry["result"]["yellow_cards"], int)
        assert isinstance(entry["result"]["red_cards"], int)


def test_a_player_who_did_not_play_says_so(monkeypatch, squad_ids):
    """⚠️ `played` distinguishes *"zero points"* from *"no match"* — ⭐ a blank gameweek and a bad
    performance are different weeks and must not draw the same."""
    answer = run(monkeypatch, picks(squad_ids))

    assert all(isinstance(e["result"]["played"], bool) for e in answer["squad"])


def test_an_unknown_player_is_skipped_not_fatal(monkeypatch, squad_ids):
    """⭐ A squad containing an id the board has never seen still renders the other fourteen.

    ⚠️ *One unrecognised player must not cost the whole week* — the same rule as ADR-215's partial read.
    """
    answer = run(monkeypatch, picks([999_999] + squad_ids[:14]))

    assert len(answer["squad"]) == 14


def test_every_player_in_that_week_has_a_shirt(monkeypatch, squad_ids):
    """⚠️⚠️ **The kits of the clubs you owned THEN, which is the whole point of sending them.**

    The past week is drawn on the pitch (owner's feedback on ADR-298's first build), and the live
    `my-team` kit map covers only the clubs in the *current* squad. ⭐ *A player you have since sold would
    be shirtless in the week he scored* — which is exactly the week you swiped back to look at.
    """
    answer = run(monkeypatch, picks(squad_ids))

    assert answer["kits"], "a played week carries no kits, so the pitch draws fifteen 👕 emoji"
    for entry in answer["squad"]:
        club = entry["player"]["team"]
        assert club in answer["kits"], f"{entry['player']['web_name']} ({club}) has no shirt"
        assert answer["kits"][club]["outfield"], f"{club}'s outfield shirt is blank"
        assert answer["kits"][club]["gk"], f"{club}'s keeper shirt is blank"


def test_a_played_week_carries_fpls_own_points_breakdown(monkeypatch, squad_ids):
    """⭐⭐⭐ **FPL attributes the points; we never do** (ADR-299).

    The owner asked for the breakdown his competitor shows — *minutes 80' → 2, goals 1 → 4, yellow 1 →
    -1*. 🔴 **The obvious implementation is the wrong one**: a scoring table (goals 6/5/4 by position,
    assists 3, clean sheet 4/1) is twenty lines and is **already wrong**, because FPL added
    `defensive_contribution` this season and it appears in real rows now.

    ⚠️ *A points breakdown that disagrees with the total printed above it is worse than no breakdown*, and
    a hand-rolled table starts disagreeing the moment the game changes without telling us.
    """
    live = {"elements": [
        {"id": squad_ids[0], "explain": [{"fixture": 1, "stats": [
            {"identifier": "minutes", "value": 90, "points": 2},
            {"identifier": "goals_scored", "value": 1, "points": 6},
            {"identifier": "yellow_cards", "value": 1, "points": -1},
            # ⭐ The line a scoring table would have missed.
            {"identifier": "defensive_contribution", "value": 11, "points": 2},
        ]}]},
    ]}
    answer = run(monkeypatch, picks(squad_ids), live=live)

    first = next(e for e in answer["squad"] if e["player"]["id"] == squad_ids[0])
    stats = [line["stat"] for line in first["result"]["breakdown"]]
    assert "defensive_contribution" in stats, (
        "the breakdown is being derived rather than taken from FPL — this season's new stat is missing"
    )
    assert [line["points"] for line in first["result"]["breakdown"]] == [2, 6, -1, 2]

    # ⚠️ Everyone else gets an empty list, never a fabricated one.
    others = [e for e in answer["squad"] if e["player"]["id"] != squad_ids[0]]
    assert all(e["result"]["breakdown"] == [] for e in others)


def test_a_zero_point_line_is_dropped(monkeypatch, squad_ids):
    """⚠️ FPL emits `minutes 0 → 0` for a man who never came on. ⭐ *A breakdown listing what did not
    happen is longer and says less.*"""
    live = {"elements": [{"id": squad_ids[0], "explain": [{"stats": [
        {"identifier": "minutes", "value": 0, "points": 0},
        {"identifier": "bonus", "value": 1, "points": 1},
    ]}]}]}
    answer = run(monkeypatch, picks(squad_ids), live=live)

    first = next(e for e in answer["squad"] if e["player"]["id"] == squad_ids[0])
    assert [line["stat"] for line in first["result"]["breakdown"]] == ["bonus"]


def test_a_failed_breakdown_does_not_take_the_week_with_it(monkeypatch, squad_ids):
    """⚠️⚠️ **One extra request, and it must never be fatal.** The week's points, squad, kits and cards
    were all working before this field existed — ⭐ *a detail that did not load must not take down the
    screen that was working without it.*"""
    answer = run(monkeypatch, picks(squad_ids), live_raises=True)

    assert answer["played"] is True
    assert len(answer["squad"]) == 15
    assert all(e["result"]["breakdown"] == [] for e in answer["squad"])


def test_a_played_week_names_the_match_and_its_scoreline(monkeypatch, squad_ids):
    """⭐ *"away to MUN 1-0" is the context a bare total lacks.* ⚠️ A **list**, because a double gameweek
    is two matches and showing one of two is worse than showing neither."""
    answer = run(monkeypatch, picks(squad_ids))

    played = [e for e in answer["squad"] if e["result"]["played"]]
    assert played, "the fixture needs a played week to describe"

    store = Storage()
    try:
        history = store.get_gw_history_by_code()
        clubs = {tm["id"]: tm["short_name"] for tm in store.get_teams()}
        players = {p["id"]: p for p in store.get_players()}
    finally:
        store.close()

    checked = 0
    for entry in played:
        matches = entry["result"]["matches"]
        assert matches, f"{entry['player']['web_name']} played but names no match"
        rows = [r for r in history[players[entry["player"]["id"]]["code"]] if r["round"] == 5]
        assert len(matches) == len(rows), "a double gameweek must name both matches"
        for match, row in zip(matches, rows, strict=True):
            # ⚠️ `opponent` is null, never a guess — the rule `_recent_rows` already follows.
            assert match["opponent"] == clubs.get(row["opponent_team"])
            assert match["home"] == bool(row["was_home"])
            # ⭐⭐ **Oriented by who was at home**, which is the half a "does the key exist?" test misses.
            # ⚠️ *A scoreline printed the wrong way round turns a 1-0 win into a 1-0 defeat*, and it is
            # right half the time by accident — a mutation swapping the two survived until this line.
            if match["home"]:
                assert match["scored"] == row["team_h_score"]
                assert match["conceded"] == row["team_a_score"]
            else:
                assert match["scored"] == row["team_a_score"]
                assert match["conceded"] == row["team_h_score"]
            checked += 1

    assert checked >= 5, f"only {checked} scorelines were actually compared"


def test_a_double_gameweek_names_both_matches(monkeypatch, squad_ids):
    """⚠️⚠️ **The fixture has no double gameweek, so nothing exercised the second match.**

    A mutation taking `rows[:1]` survived every other test in this file — correctly, because every player
    in the committed fixture played exactly once in GW5. ⭐ *A branch the test data cannot reach is a
    branch the test suite is not testing*, however many assertions point at it.

    So this one manufactures the case: one player, two rows, one round.
    """
    store = Storage()
    try:
        history = {code: list(rows) for code, rows in store.get_gw_history_by_code().items()}
        players = {p["id"]: p for p in store.get_players()}
    finally:
        store.close()

    code = players[squad_ids[0]]["code"]
    week = [r for r in history[code] if r["round"] == 5]
    assert len(week) == 1, "the fixture changed — this test builds its double from a single"
    # ⭐ A second match in the same round: what a rearranged fixture actually looks like.
    twin = dict(week[0])
    twin["opponent_team"] = 99
    history[code] = history[code] + [twin]

    monkeypatch.setattr(Storage, "get_gw_history_by_code", lambda self: history)
    answer = run(monkeypatch, picks(squad_ids))

    entry = next(e for e in answer["squad"] if e["player"]["id"] == squad_ids[0])
    assert len(entry["result"]["matches"]) == 2, (
        "only one match of a double gameweek is named — showing one of two is worse than showing "
        "neither, because it looks complete"
    )
    # ⚠️ And the unknown club stays null rather than becoming a guess.
    assert entry["result"]["matches"][1]["opponent"] is None
