"""Signals answers about your fifteen, or about the market (ADR-245).

⭐⭐ **Trending stopped being a separate screen.** It was the same question — *what is the crowd doing?* —
asked in a different shape, and a second screen would have meant a second ordering, a second idea of what
counts as evidence, and two places to keep honest.

⚠️⚠️ **The market has to be bounded, and the bound has to be visible.** Ownership on the live board has a
**median of 0.2%**, so an unbounded sweep returned **194 news items**, nearly all about players almost
nobody holds — ⭐ *a list that long is not more information, it is a screen a person stops reading.*
"""

import pytest

from src import service
from src.service.answers import _market_subjects
from src.storage import Storage


@pytest.fixture(scope="module")
def store():
    s = Storage()
    yield s
    s.close()


@pytest.fixture(scope="module")
def squad(store):
    need = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}
    picked, per_club = [], {}
    for p in store.get_players():
        if need.get(p["position"], 0) and per_club.get(p["team"], 0) < 3 and len(picked) < 15:
            picked.append(p["id"])
            need[p["position"]] -= 1
            per_club[p["team"]] = per_club.get(p["team"], 0) + 1
    return picked


# ── the scope itself ─────────────────────────────────────────────────────────────────────────────

def test_squad_scope_only_talks_about_your_players(store, squad):
    answer = service.signals(service.SignalsRequest(player_ids=squad, horizon=1), store=store)
    assert answer["scope"] == "squad"
    for signal in answer["signals"]:
        assert signal["player"]["id"] in set(squad)
    # ⭐ No floor in squad scope: your fifteen are your fifteen however few managers agree.
    assert answer["ownership_floor"] is None


def test_global_scope_needs_no_squad(store):
    """⭐ The one squad-shaped request where the squad is optional — a market sweep has none to give."""
    answer = service.signals(service.SignalsRequest(scope="global", horizon=1), store=store)
    assert answer["scope"] == "global"
    assert answer["signals"], "the market produced nothing at all"


def test_global_sees_players_the_squad_scope_cannot(store, squad):
    mine = service.signals(service.SignalsRequest(player_ids=squad, horizon=1), store=store)
    market = service.signals(service.SignalsRequest(scope="global", horizon=1), store=store)
    assert len(market["signals"]) > len(mine["signals"])
    assert market["checked"] > mine["checked"]


# ── the bound ────────────────────────────────────────────────────────────────────────────────────

def test_the_floor_is_read_from_the_board_and_reported(store):
    """⚠️⚠️ **A market view that silently drops four fifths of the board lies by omission.**

    ⭐ *A filter the reader cannot see is one he will eventually be surprised by* (ADR-215) — so the cut
    travels in the answer, and the app prints it.
    """
    answer = service.signals(service.SignalsRequest(scope="global", horizon=1), store=store)
    floor = answer["ownership_floor"]
    assert floor is not None and floor > 0

    # ⚠️ Checked against the **board**, not against the answer: `player_summary` does not carry ownership,
    # so asserting on the signal alone would have been a test of nothing. (The first draft of this did
    # exactly that, and hedged it with `or True` — ⭐ *a hedge in an assertion is a confession.*)
    by_id = {p["id"]: p for p in store.get_players()}
    for signal in answer["signals"]:
        share = by_id[signal["player"]["id"]]["selected_by"] or 0
        assert share >= floor, (
            f"{signal['player']['web_name']} is owned by {share}%, under the {floor}% cut the answer claims"
        )


def test_the_floor_moves_with_the_distribution(store):
    """⭐⭐ **Not a typed threshold.** Halve the board's ownership and the cut halves with it — which is the
    whole difference between a percentile and a number somebody wrote down in September."""
    players = [dict(p) for p in store.get_players()]
    _, live = _market_subjects(players)

    halved = [{**p, "selected_by": (p.get("selected_by") or 0) / 2} for p in players]
    _, lower = _market_subjects(halved)
    assert lower < live, f"cut stayed at {live} when every share halved"


def test_the_bound_keeps_the_list_readable(store):
    """⚠️ Measured, not asserted from taste: an unbounded sweep is 194 news items on this board."""
    everyone = [p for p in store.get_players()]
    subjects, _ = _market_subjects(everyone)
    assert len(subjects) < len(everyone) / 2, (
        f"the cut kept {len(subjects)} of {len(everyone)} — that is not a bound"
    )
    answer = service.signals(service.SignalsRequest(scope="global", horizon=1), store=store)
    assert len(answer["signals"]) < 80, (
        f"{len(answer['signals'])} signals is past the point a person reads a list"
    )


# ── trending, folded in ──────────────────────────────────────────────────────────────────────────

def test_the_crowd_is_the_weakest_evidence_and_sorts_last(store):
    """⭐ *"Lots of people did this" is the reason a template forms, and it is not on its own a reason to
    join one.* So it ranks below an injury FPL confirmed, and says which it is."""
    answer = service.signals(service.SignalsRequest(scope="global", horizon=1), store=store)
    kinds = [s["kind"] for s in answer["signals"]]
    if "trending" not in kinds:
        pytest.skip("no trending signals on the board this week")
    assert kinds.index("trending") > kinds.index("official")
    assert kinds[-1] == "trending", "a weaker claim sorted above the crowd"


def test_the_crowd_never_reports_a_player_you_already_hold(store):
    """⚠️ *"12,000 managers bought him"* about someone in your own squad is not news — you are one of them.

    ⭐ The signal is about the market; for your own player the interesting version is the exodus, which is
    a separate kind and still fires.
    """
    market = service.signals(service.SignalsRequest(scope="global", horizon=1), store=store)
    trending_ids = [s["player"]["id"] for s in market["signals"] if s["kind"] == "trending"]
    if not trending_ids:
        pytest.skip("no trending signals on the board this week")

    # Own them, and they stop being news.
    again = service.signals(
        service.SignalsRequest(scope="global", player_ids=trending_ids, horizon=1), store=store)
    assert not [s for s in again["signals"] if s["kind"] == "trending"
                and s["player"]["id"] in set(trending_ids)]


def test_a_signal_says_whether_it_is_about_one_of_yours(store, squad):
    """⭐⭐ **"Yours" changes what a signal means**, not just who it is about: an exodus from a player you
    hold is a decision, the same exodus from one you do not is a fact about the market.

    ⚠️ Flagged by the service so the client is not matching ids itself and getting it wrong.
    """
    answer = service.signals(
        service.SignalsRequest(scope="global", player_ids=squad, horizon=1), store=store)
    for signal in answer["signals"]:
        assert signal["owned"] == (signal["player"]["id"] in set(squad))


def test_scope_must_be_one_of_two_things():
    with pytest.raises(ValueError, match="scope"):
        service.SignalsRequest(scope="everything").validate()
