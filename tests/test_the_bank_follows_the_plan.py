"""The bank moves when you plan a transfer (ADR-337).

🔴 **Reported from a real phone**: *"when I make proposed transfers in the app, these figures don't rise
or fall. I can make a transfer and have no idea if I have enough funds to do same."* Five changes, and
*"£1.0m In the bank"* sat still through every one of them.

⚠️⚠️ **The code said why, and had the reasoning backwards.** Its comment read *"a draft that invented its
own bank would let a manager plan a move he cannot pay for"* — and holding FPL's bank is precisely what
did that. ⭐ *The figure that is supposed to stop you cannot stop you if it never moves.*

⭐⭐ These drive the **endpoint**, against the real store. A first draft of this file asserted arithmetic
written inside the test and never called `my_team` at all — ⚠️ *a test that recomputes the answer tests
the recomputation.*
"""

import pytest

from src.service.answers import squad as mod
from src.service.requests import MyTeamRequest
from src.storage import Storage

BANK = 1.0


@pytest.fixture
def board():
    store = Storage()
    rows = [dict(r) for r in store.get_players()]
    yield store, rows, {r["id"]: r["price"] for r in rows}
    store.close()


@pytest.fixture
def fpl_squad(board, monkeypatch):
    """A fixed fifteen that FPL 'holds', so the only thing that varies is the draft."""
    _, rows, _ = board
    ids = [r["id"] for r in rows][:15]
    priced = {r["id"]: r["price"] for r in rows}
    # ⚠️ `cost` is the real sum, not a round number. The invariant below compares bank+cost before and
    # after, and a made-up FPL cost would be comparing two different definitions of the same word.
    cost = round(sum(priced[i] for i in ids), 1)
    monkeypatch.setattr(mod, "fetch_manager_team", lambda mid, rs: ({
        "name": "T", "player_ids": ids, "bench_ids": ids[11:], "bank": BANK,
        "value": 100.0, "cost": cost, "captain_id": ids[0], "vice_captain_id": ids[1],
        "active_chip": None}, ""))
    return ids


def swap(ids, priced, *, dearest_in=True):
    """Swap one **bench** player for someone not owned.

    ⚠️ The bench, deliberately: replacing an XI player and appending the arrival to the bench leaves it
    five deep, and the optimiser raises on a bench of five. ⭐ *A fixture that builds an illegal squad is
    testing the validator, not the thing you meant.*
    """
    out = ids[-1]
    pool = [i for i in priced if i not in ids]
    arrival = max(pool, key=lambda i: priced[i]) if dearest_in else min(pool, key=lambda i: priced[i])
    draft = [i for i in ids if i != out] + [arrival]
    bench = [i for i in ids[11:] if i != out] + [arrival]
    return draft, bench, out, arrival


def test_without_a_draft_the_bank_is_fpls_own(board, fpl_squad):
    store, _, _ = board
    answer = mod.my_team(MyTeamRequest(manager_id=1), store=store)

    assert answer["squad"]["bank"] == BANK
    assert answer["squad"]["bank_is_estimated"] is False, "nothing is estimated about the real squad"


def test_a_plan_you_cannot_afford_reports_a_negative_bank(board, fpl_squad):
    """🔴 The reported bug. Without this the app shows a squad you have no way to buy."""
    store, _, priced = board
    draft, bench, out, dear = swap(fpl_squad, priced)

    answer = mod.my_team(MyTeamRequest(manager_id=1, draft_player_ids=draft,
                                       draft_bench_ids=bench), store=store)

    spend = round(priced[dear] - priced[out], 1)
    assert spend > BANK, "the fixture did not build an unaffordable plan"
    assert answer["squad"]["bank"] == pytest.approx(round(BANK - spend, 1), abs=0.05)
    assert answer["squad"]["bank"] < 0


def test_the_bank_is_flagged_as_an_estimate_while_planning(board, fpl_squad):
    """⚠️ FPL pays back only **half** of a player's rise since you bought him, and the public API
    publishes no selling price — `entry/{id}/event/{gw}/picks/` carries the squad's aggregate `bank` and
    `value` and nothing per player. ⭐ So this errs **optimistic**, and the screen has to say so: an
    estimate that flatters the reader about money is the one kind that must admit it.
    """
    store, _, priced = board
    draft, bench, *_ = swap(fpl_squad, priced)

    answer = mod.my_team(MyTeamRequest(manager_id=1, draft_player_ids=draft,
                                       draft_bench_ids=bench), store=store)

    assert answer["squad"]["bank_is_estimated"] is True


def test_an_affordable_plan_leaves_money_in_the_bank(board, fpl_squad):
    """⭐ The other direction: selling dear and buying cheap must *raise* it. A rule that only ever
    subtracts would look right on every screenshot in the bug report and still be wrong."""
    store, _, priced = board
    draft, bench, out, arrival = swap(fpl_squad, priced, dearest_in=False)
    assert priced[arrival] < priced[out], "the fixture did not build a cheaper plan"

    answer = mod.my_team(MyTeamRequest(manager_id=1, draft_player_ids=draft,
                                       draft_bench_ids=bench), store=store)

    assert answer["squad"]["bank"] > BANK


def test_the_total_is_invariant_so_value_does_not_move(board, fpl_squad):
    """⭐⭐ **The half of the report that was not a bug.** FPL's `value` includes the bank, so a transfer
    only moves money between the two. ⚠️ *The tester was right that the bank was frozen and right that
    value looked frozen; only one of them was wrong.*"""
    store, _, priced = board
    draft, bench, *_ = swap(fpl_squad, priced)

    plain = mod.my_team(MyTeamRequest(manager_id=1), store=store)
    planned = mod.my_team(MyTeamRequest(manager_id=1, draft_player_ids=draft,
                                        draft_bench_ids=bench), store=store)

    assert planned["squad"]["value"] == plain["squad"]["value"]
    # And the invariant that makes it correct rather than merely unchanged:
    assert (round(plain["squad"]["bank"] + plain["squad"]["cost"], 1)
            == pytest.approx(round(planned["squad"]["bank"] + planned["squad"]["cost"], 1), abs=0.05))


def test_the_cost_follows_the_drafted_fifteen(board, fpl_squad):
    """⚠️ `cost` is *"what the fifteen price at today"* — so it has to be **this** fifteen."""
    store, _, priced = board
    draft, bench, *_ = swap(fpl_squad, priced)

    answer = mod.my_team(MyTeamRequest(manager_id=1, draft_player_ids=draft,
                                       draft_bench_ids=bench), store=store)

    assert answer["squad"]["cost"] == pytest.approx(
        round(sum(priced[i] for i in draft), 1), abs=0.05)
