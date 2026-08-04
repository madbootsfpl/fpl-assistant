"""Tests for transfer suggestions (ADR-030).

Each FPL constraint is exercised in isolation: position, not-already-owned,
availability, budget (self-funding vs --bank), and ≤3/club (incl. the same-club-swap
edge case). Plus xP-gain ranking, positive-gains-only, the bench flag, and no-upgrade.
Offline, plain dicts.
"""

from src.analytics import suggest_transfer_plan, suggest_transfers


def _p(pid, pos, team, price, status="a"):
    return {"id": pid, "position": pos, "team": team, "price": price,
            "web_name": f"P{pid}", "status": status}


def _xp(**pairs):
    return dict(pairs)


def test_ranks_by_xp_gain_and_reports_the_move():
    owned = [_p(1, "MID", "AAA", 5.0)]
    market = owned + [_p(2, "MID", "BBB", 5.0)]
    xp = {1: 3.0, 2: 9.0}
    out = suggest_transfers(owned, market, xp)
    assert len(out) == 1
    s = out[0]
    assert s["out"]["id"] == 1 and s["in"]["id"] == 2
    assert s["gain"] == 6.0 and s["position"] == "MID"


def test_only_same_position_is_suggested():
    owned = [_p(1, "MID", "AAA", 5.0)]
    market = owned + [_p(2, "FWD", "BBB", 5.0)]      # a FWD can't replace a MID
    out = suggest_transfers(owned, market, {1: 3.0, 2: 20.0})
    assert out == []


def test_already_owned_players_are_not_suggested():
    owned = [_p(1, "MID", "AAA", 5.0), _p(2, "MID", "BBB", 5.0)]
    out = suggest_transfers(owned, owned, {1: 3.0, 2: 9.0})
    assert out == []                                 # id 2 is owned, so no external upgrade


def test_unavailable_candidates_are_excluded():
    owned = [_p(1, "MID", "AAA", 5.0)]
    market = owned + [_p(2, "MID", "BBB", 5.0, status="i")]   # injured target
    out = suggest_transfers(owned, market, {1: 3.0, 2: 20.0})
    assert out == []


def test_budget_self_funding_then_bank_unlocks_a_pricier_target():
    owned = [_p(1, "MID", "AAA", 5.0)]
    market = owned + [_p(2, "MID", "BBB", 6.5)]      # £1.5m over the sale price
    xp = {1: 3.0, 2: 20.0}
    assert suggest_transfers(owned, market, xp) == []            # bank £0 → unaffordable
    out = suggest_transfers(owned, market, xp, bank=2.0)         # bank £2 → affordable
    assert out and out[0]["in"]["id"] == 2


def test_club_limit_blocks_a_fourth_from_one_club():
    # 3 CCC players, none a MID; the only MID owned is from AAA. A CCC MID target would make
    # 4 CCC and there's no CCC MID to sell for a same-club swap → it must be rejected.
    owned = [_p(1, "DEF", "CCC", 5.0), _p(2, "FWD", "CCC", 5.0),
             _p(3, "GK", "CCC", 5.0), _p(4, "MID", "AAA", 5.0)]
    market = owned + [_p(9, "MID", "CCC", 5.0)]
    out = suggest_transfers(owned, market, {1: 1, 2: 1, 3: 1, 4: 1, 9: 20})
    assert out == []


def test_club_limit_allows_a_same_club_swap():
    # selling a CCC player frees a CCC slot, so a CCC target is fine even at the cap
    owned = [_p(1, "MID", "CCC", 5.0), _p(2, "MID", "CCC", 5.0), _p(3, "MID", "CCC", 5.0)]
    market = owned + [_p(9, "MID", "CCC", 5.0)]
    out = suggest_transfers(owned, market, {1: 3, 2: 3, 3: 3, 9: 12})
    assert out and out[0]["in"]["id"] == 9           # swap a CCC out for the better CCC in


def test_only_positive_gains_are_returned():
    owned = [_p(1, "MID", "AAA", 5.0)]
    market = owned + [_p(2, "MID", "BBB", 5.0)]      # a *worse* option
    assert suggest_transfers(owned, market, {1: 9.0, 2: 3.0}) == []


def test_bench_out_is_flagged():
    owned = [_p(1, "MID", "AAA", 5.0)]
    market = owned + [_p(2, "MID", "BBB", 5.0)]
    out = suggest_transfers(owned, market, {1: 3.0, 2: 9.0}, bench_ids=[1])
    assert out[0]["out_on_bench"] is True


def test_limit_caps_the_number_of_suggestions():
    owned = [_p(i, "MID", f"T{i}", 5.0) for i in range(1, 5)]
    market = owned + [_p(10 + i, "MID", f"U{i}", 5.0) for i in range(1, 5)]
    xp = {i: 1.0 for i in range(1, 5)} | {10 + i: 9.0 for i in range(1, 5)}
    assert len(suggest_transfers(owned, market, xp, limit=2)) == 2


# ---- the coordinated plan (ADR-035) -----------------------------------------

def test_plan_threads_the_shared_bank():
    # P11 (£5.0) can't replace P2 (£4.5) at bank £0 — but selling P1 (£5.0) for P10 (£4.5)
    # frees £0.5, which unlocks it on the next move.
    owned = [_p(1, "GK", "AAA", 5.0), _p(2, "MID", "BBB", 4.5)]
    market = owned + [_p(10, "GK", "CCC", 4.5), _p(11, "MID", "DDD", 5.0)]
    xp = {1: 1, 2: 1, 10: 20, 11: 25}
    plan = suggest_transfer_plan(owned, market, xp, count=2)
    assert [m["in"]["id"] for m in plan] == [10, 11]     # 11 only reachable after 10's sale
    assert plan[-1]["bank_after"] == 0.0


def test_plan_never_buys_the_same_player_twice():
    owned = [_p(1, "MID", "AAA", 5.0), _p(2, "MID", "BBB", 5.0)]
    market = owned + [_p(10, "MID", "CCC", 5.0), _p(11, "MID", "DDD", 5.0)]
    xp = {1: 1, 2: 1, 10: 30, 11: 20}                    # P10 is the best for both owned
    plan = suggest_transfer_plan(owned, market, xp, count=2)
    ins = [m["in"]["id"] for m in plan]
    assert ins == [10, 11] and len(set(ins)) == 2         # P10 bought once, then P11


def test_plan_bank_never_goes_negative():
    owned = [_p(1, "MID", "AAA", 5.0)]
    market = owned + [_p(10, "MID", "CCC", 5.0)]
    plan = suggest_transfer_plan(owned, market, {1: 1, 10: 20}, bank=0.0, count=3)
    assert all(m["bank_after"] >= 0 for m in plan)


def test_plan_respects_the_club_limit_across_moves():
    # 2 CCC already (a DEF + GK, so P10/P11 MIDs can't be a same-club swap). Buying P10 makes
    # CCC=3; buying P11 too would be a 4th → blocked, so the plan stops at one move.
    owned = [_p(1, "DEF", "CCC", 5.0), _p(2, "GK", "CCC", 5.0),
             _p(3, "MID", "AAA", 5.0), _p(4, "MID", "BBB", 5.0)]
    market = owned + [_p(10, "MID", "CCC", 5.0), _p(11, "MID", "CCC", 5.0)]
    xp = {1: 1, 2: 1, 3: 1, 4: 1, 10: 30, 11: 28}
    plan = suggest_transfer_plan(owned, market, xp, count=2)
    assert [m["in"]["id"] for m in plan] == [10]          # P11 would be a 4th from CCC


def test_plan_stops_when_no_positive_move_remains():
    owned = [_p(1, "MID", "AAA", 5.0)]
    market = owned + [_p(10, "MID", "BBB", 5.0)]
    assert suggest_transfer_plan(owned, market, {1: 9, 10: 3}, count=3) == []
