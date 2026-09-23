"""Mini-leagues over HTTP — the table, the captain split, and the head-to-head (ADR-267).

⚠️⚠️ **Every test here stubs the FPL boundary.** These three endpoints are the only ones that call
somebody else's API, and ⭐ *a test that needs the internet is a test that fails for reasons about the
internet* — which trains a reader to ignore it.
"""

import pathlib
import sys

import pytest

from src import service
from src.storage import Storage

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent
                       / "spikes" / "018-flutter-read-slice"))

from regenerate_samples import _canned_picks, _CannedFpl, _with_canned  # noqa: E402


@pytest.fixture(scope="module")
def store():
    s = Storage()
    yield s
    s.close()


@pytest.fixture(scope="module")
def ids(store):
    return [p["id"] for p in store.get_players()][:15]


def test_a_manager_id_finds_his_leagues_and_private_ones_lead():
    """⭐⭐ **Nobody knows their league id** (ADR-141) — it lives in a URL you have to go and find.

    ⚠️ And FPL mixes the league you joined with friends in among automatic ones (your club, your region,
    Overall), which are always bigger. ⭐ *Sorting by size would bury the only leagues anyone means.*
    """
    answer = _with_canned(
        _CannedFpl([], {}),
        lambda: service.leagues(service.LeaguesRequest(manager_id=1)))

    assert [lg["private"] for lg in answer["leagues"]][0] is True, "a private league must lead"
    assert answer["leagues"][0]["name"] == "A League of Our Own"


def test_the_table_costs_one_request_and_the_captain_split_is_opt_in(store, ids):
    """⚠️⚠️ **The split costs one FPL request per manager**; the table costs one in total.

    ⭐ *A screen that quietly spends fifty requests to draw a second panel will be blamed for being slow*,
    so the expensive half only happens when asked for.
    """
    entries = [101, 102, 103]
    picks = {e: _canned_picks(ids, ids[0], ids[1]) for e in entries}

    class _Counting(_CannedFpl):
        def __init__(self, *a):
            super().__init__(*a)
            self.picks_calls = 0

        def get_entry_picks(self, entry_id, gameweek):
            self.picks_calls += 1
            return super().get_entry_picks(entry_id, gameweek)

    plain = _Counting(entries, picks)
    _with_canned(plain, lambda: service.league(
        service.LeagueRequest(league_id=1, gameweek=5), store=store))
    assert plain.picks_calls == 0, "the table alone must not read a single squad"

    asked = _Counting(entries, picks)
    answer = _with_canned(asked, lambda: service.league(
        service.LeagueRequest(league_id=1, gameweek=5, with_captains=True), store=store))
    assert asked.picks_calls == len(entries)
    assert answer["captains"], "asking for captains must produce some"


def test_the_split_reports_how_many_squads_it_actually_read(store, ids):
    """⚠️⚠️ **A partial read must never present itself as the whole league** (ADR-215's rule).

    ⭐ *A manager whose fetch fails is simply absent* — an exception would throw away two good reads
    because of one bad id — but then the answer has to say what it is standing on.
    """
    from src.api.client import FplApiError

    entries = [101, 102, 103]
    picks = {101: _canned_picks(ids, ids[0], ids[1]), 102: _canned_picks(ids, ids[0], ids[2])}

    class _OneBroken(_CannedFpl):
        def get_entry_picks(self, entry_id, gameweek):
            if entry_id == 103:
                raise FplApiError("that manager is not public")
            return super().get_entry_picks(entry_id, gameweek)

    answer = _with_canned(_OneBroken(entries, picks), lambda: service.league(
        service.LeagueRequest(league_id=1, gameweek=5, with_captains=True), store=store))

    assert answer["captains_from"] == 2, "it must count what it read, not what it asked for"
    assert answer["rows"], "one unreadable squad must not lose the table"
    assert answer["captains"][0]["share"] == 100.0, "the share is of what was read"


def test_the_captain_share_is_of_the_squads_read_not_the_league(store, ids):
    """⭐ *"9 of 12" is a different fact from "9"* — the reader is deciding whether to differ from a crowd,
    and a bare count cannot tell him how big the crowd is."""
    entries = [101, 102, 103, 104]
    picks = {
        101: _canned_picks(ids, ids[0], ids[1]),
        102: _canned_picks(ids, ids[0], ids[1]),
        103: _canned_picks(ids, ids[0], ids[1]),
        104: _canned_picks(ids, ids[5], ids[1]),
    }
    answer = _with_canned(_CannedFpl(entries, picks), lambda: service.league(
        service.LeagueRequest(league_id=1, gameweek=5, with_captains=True), store=store))

    top = answer["captains"][0]
    assert top["count"] == 3
    assert top["share"] == 75.0


def test_a_head_to_head_sets_the_shared_players_aside(store, ids):
    """⭐⭐ **The shared players are reported and then set aside.**

    ⚠️ They are usually the large majority of both totals and the part you can do nothing about —
    *printing the shared total is what makes the small gap believable rather than looking like a rounding
    error on two big numbers.*
    """
    others = [p["id"] for p in store.get_players() if p["id"] not in set(ids)][:15]
    mine = _canned_picks(ids, ids[0], ids[1])
    theirs = _canned_picks(ids[:8] + others[:7], others[0], ids[1])

    answer = _with_canned(_CannedFpl([1, 2], {1: mine, 2: theirs}), lambda: service.head_to_head(
        service.HeadToHeadRequest(manager_id=1, rival_id=2, horizon=1), store=store))

    assert answer["shared_count"] > 0
    assert answer["shared_xp"] > 0
    assert answer["my_edge"] and answer["their_edge"], "different squads must produce differentials"
    # ⭐ The sentence is built from the same numbers, so headline and rows cannot disagree.
    assert answer["note"]


def test_identical_squads_produce_no_differentials(store, ids):
    """⚠️ The case a fixture with two different squads never reaches — ⭐ *and the one where the screen
    has to say something true rather than show an empty list.*"""
    same = _canned_picks(ids, ids[0], ids[1])
    answer = _with_canned(_CannedFpl([1, 2], {1: same, 2: dict(same)}), lambda: service.head_to_head(
        service.HeadToHeadRequest(manager_id=1, rival_id=2, horizon=1), store=store))

    assert answer["my_edge"] == []
    assert answer["their_edge"] == []
    assert answer["gap"] == 0
    assert answer["same_captain"] is True
    assert "cannot separate you" in answer["note"]


def test_a_differential_carries_the_one_player_shape_so_a_doubt_can_be_flagged(store, ids):
    """⚠️⚠️ **Found by the shape sweep, and a real defect.** The engine's edge row carries no `status`, so
    ⭐ *a differential who is doubtful could not be flagged as one* — ADR-226's bug, on the players the
    whole screen is about."""
    others = [p["id"] for p in store.get_players() if p["id"] not in set(ids)][:15]
    mine = _canned_picks(ids, ids[0], ids[1])
    theirs = _canned_picks(ids[:8] + others[:7], others[0], ids[1])

    answer = _with_canned(_CannedFpl([1, 2], {1: mine, 2: theirs}), lambda: service.head_to_head(
        service.HeadToHeadRequest(manager_id=1, rival_id=2, horizon=1), store=store))

    row = answer["my_edge"][0]
    assert "status" in row["player"], "a differential must be able to carry a doubt"
    assert "chance" in row["player"]
    assert row["multiplier"] in (1, 2, 3)


@pytest.mark.parametrize("request_, expected", [
    (service.LeaguesRequest(manager_id=0), "a manager id is required"),
    (service.LeagueRequest(league_id=0), "a league id is required"),
    (service.LeagueRequest(league_id=1, limit=0), "limit must be 1-50"),
    (service.HeadToHeadRequest(manager_id=1, rival_id=0), "two manager ids are required"),
    # ⚠️ Not a crash — an answer that would be a row of zeros presented as analysis.
    (service.HeadToHeadRequest(manager_id=7, rival_id=7), "cannot be compared with himself"),
])
def test_a_bad_league_request_is_refused(request_, expected):
    with pytest.raises(ValueError, match=expected):
        request_.validate()


def test_the_split_reads_only_the_top_of_a_big_league(store, ids):
    """⚠️⚠️ **The cap is the whole cost control, and it survived its first mutation run.**

    Every other fixture here holds three or four managers, so `limit` never bound and removing it changed
    nothing — ⭐ *the tell is always "does the population contain the case?"*, and it did not. A real league
    is fifty rows and reading all of them is fifty requests to somebody else's API.
    """
    entries = list(range(201, 251))          # a full standings page
    picks = {e: _canned_picks(ids, ids[0], ids[1]) for e in entries}

    class _Counting(_CannedFpl):
        def __init__(self, *a):
            super().__init__(*a)
            self.picks_calls = 0

        def get_entry_picks(self, entry_id, gameweek):
            self.picks_calls += 1
            return super().get_entry_picks(entry_id, gameweek)

    client = _Counting(entries, picks)
    answer = _with_canned(client, lambda: service.league(
        service.LeagueRequest(league_id=1, gameweek=5, with_captains=True, limit=20), store=store))

    assert client.picks_calls == 20, "the cap must bind — this is one upstream request per manager"
    assert len(answer["rows"]) == 50, "and it must cap the READING, never the table"
    assert answer["captains_from"] == 20
