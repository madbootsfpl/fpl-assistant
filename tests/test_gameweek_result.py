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

    def __init__(self, payload=None, raises=False):
        self._payload, self._raises = payload, raises

    def get_entry_picks(self, entry_id, gameweek):
        if self._raises:
            raise fpl_client.FplApiError("not published")
        return self._payload


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


def run(monkeypatch, payload, gameweek=5, raises=False):
    monkeypatch.setattr(fpl_client, "FplClient", lambda *a, **k: FakeFpl(payload, raises))
    return gameweek_result(GameweekResultRequest(manager_id=1, gameweek=gameweek))


def test_a_gameweek_fpl_has_not_published_is_not_an_error(monkeypatch, squad_ids):
    """⭐⭐ **Swiping past the present is a normal gesture**, not a failure.

    ⚠️ *A screen that can be swiped into before the data exists must have something true to draw* — so
    this degrades like `my_team` rather than raising.
    """
    answer = run(monkeypatch, None, gameweek=38, raises=True)

    assert answer == {"gameweek": 38, "played": False, "squad": [], "summary": {}}


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
