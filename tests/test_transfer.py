"""Tests for transfer suggestions (ADR-030).

Each FPL constraint is exercised in isolation: position, not-already-owned,
availability, budget (self-funding vs --bank), and ≤3/club (incl. the same-club-swap
edge case). Plus xP-gain ranking, positive-gains-only, the bench flag, and no-upgrade.
Offline, plain dicts.
"""

from src.analytics import (
    SQUAD_15,
    best_legal_xi,
    best_xi_points,
    select_squad,
    suggest_transfer_plan,
    suggest_transfers,
)
from src.ui.transfer import render_transfer_plan, render_transfers


def _p(pid, pos, team, price, status="a"):
    return {"id": pid, "position": pos, "team": team, "price": price,
            "web_name": f"P{pid}", "status": status}


def _xp(**pairs):
    return dict(pairs)


def test_ranks_by_xp_gain_and_reports_the_move():
    owned = [_p(1, "MID", "AAA", 5.0)]
    market = owned + [_p(2, "MID", "BBB", 5.0)]
    xp = {1: 3.0, 2: 9.0}
    out = suggest_transfers(owned, market, xp, xi_aware=False)   # raw-gain path (ADR-046 --raw)
    assert len(out) == 1
    s = out[0]
    assert s["out"]["id"] == 1 and s["in"]["id"] == 2
    assert s["gain"] == 6.0 and s["position"] == "MID"


def test_an_xp_optimal_squad_has_no_positive_transfers():
    # ADR-041 consistency: when the squad is BUILT on the same xP that `transfer` ranks by, there
    # are no free upgrades — a cheaper-or-equal same-position player with higher xP would mean the
    # squad wasn't optimal. (The inconsistency the owner spotted was two different metrics.)
    pool, xp, pid = [], {}, 1
    for pos, n in (("GK", 4), ("DEF", 7), ("MID", 7), ("FWD", 5)):   # spares beyond 2/5/5/3
        for k in range(n):
            player = _p(pid, pos, f"T{pid}", 5.0)                    # distinct team, same price
            player["total_points"] = 0                              # select_squad sums this
            pool.append(player)
            xp[pid] = 10.0 - k                                       # descending xP within position
            pid += 1
    owned = select_squad(pool, budget=100.0, formation=SQUAD_15, scores=xp)["selected"]
    assert suggest_transfers(owned, pool, xp, bank=0.0) == []


def test_incoming_player_is_not_suggested_twice():
    # Both MIDs' best target is P3; the shortlist must not buy P3 twice (ADR-040) — the
    # lower-gain sell (P1) gets its next-best available target (P4) instead.
    owned = [_p(1, "MID", "AAA", 5.0), _p(2, "MID", "BBB", 5.0)]
    market = owned + [_p(3, "MID", "CCC", 5.0), _p(4, "MID", "DDD", 5.0)]
    xp = {1: 3.0, 2: 4.0, 3: 10.0, 4: 8.0}
    out = suggest_transfers(owned, market, xp, xi_aware=False)   # raw-gain rule (ADR-046 --raw)
    incoming = [s["in"]["id"] for s in out]
    assert incoming == [3, 4]                       # P3 once (best gain), then P4 (next-best)
    assert len(set(incoming)) == len(incoming)      # no repeated buy
    # P1→P3 is the top gain (7.0), then P2→P4 (4.0): each sell appears once
    assert [s["out"]["id"] for s in out] == [1, 2]


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
    assert suggest_transfers(owned, market, xp, xi_aware=False) == []       # bank £0 → unaffordable
    out = suggest_transfers(owned, market, xp, bank=2.0, xi_aware=False)     # bank £2 → affordable
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
    out = suggest_transfers(owned, market, {1: 3, 2: 3, 3: 3, 9: 12}, xi_aware=False)
    assert out and out[0]["in"]["id"] == 9           # swap a CCC out for the better CCC in


def test_only_positive_gains_are_returned():
    owned = [_p(1, "MID", "AAA", 5.0)]
    market = owned + [_p(2, "MID", "BBB", 5.0)]      # a *worse* option
    assert suggest_transfers(owned, market, {1: 9.0, 2: 3.0}) == []


def test_bench_out_is_flagged():
    owned = [_p(1, "MID", "AAA", 5.0)]
    market = owned + [_p(2, "MID", "BBB", 5.0)]
    out = suggest_transfers(owned, market, {1: 3.0, 2: 9.0}, bench_ids=[1], xi_aware=False)
    assert out[0]["out_on_bench"] is True


def test_limit_caps_the_number_of_suggestions():
    owned = [_p(i, "MID", f"T{i}", 5.0) for i in range(1, 5)]
    market = owned + [_p(10 + i, "MID", f"U{i}", 5.0) for i in range(1, 5)]
    xp = {i: 1.0 for i in range(1, 5)} | {10 + i: 9.0 for i in range(1, 5)}
    assert len(suggest_transfers(owned, market, xp, limit=2, xi_aware=False)) == 2


# ---- the coordinated plan (ADR-035) -----------------------------------------

def test_plan_threads_the_shared_bank():
    # P11 (£5.0) can't replace P2 (£4.5) at bank £0 — but selling P1 (£5.0) for P10 (£4.5)
    # frees £0.5, which unlocks it on the next move.
    owned = [_p(1, "GK", "AAA", 5.0), _p(2, "MID", "BBB", 4.5)]
    market = owned + [_p(10, "GK", "CCC", 4.5), _p(11, "MID", "DDD", 5.0)]
    xp = {1: 1, 2: 1, 10: 20, 11: 25}
    plan = suggest_transfer_plan(owned, market, xp, count=2, xi_aware=False)
    assert [m["in"]["id"] for m in plan] == [10, 11]     # 11 only reachable after 10's sale
    assert plan[-1]["bank_after"] == 0.0


def test_plan_never_buys_the_same_player_twice():
    owned = [_p(1, "MID", "AAA", 5.0), _p(2, "MID", "BBB", 5.0)]
    market = owned + [_p(10, "MID", "CCC", 5.0), _p(11, "MID", "DDD", 5.0)]
    xp = {1: 1, 2: 1, 10: 30, 11: 20}                    # P10 is the best for both owned
    plan = suggest_transfer_plan(owned, market, xp, count=2, xi_aware=False)
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
    plan = suggest_transfer_plan(owned, market, xp, count=2, xi_aware=False)
    assert [m["in"]["id"] for m in plan] == [10]          # P11 would be a 4th from CCC


def test_plan_stops_when_no_positive_move_remains():
    owned = [_p(1, "MID", "AAA", 5.0)]
    market = owned + [_p(10, "MID", "BBB", 5.0)]
    assert suggest_transfer_plan(owned, market, {1: 9, 10: 3}, count=3) == []


def test_plan_table_shows_the_incoming_players_per_gameweek():
    plan = [{
        "out": {"web_name": "Kelleher", "team": "BRE", "price": 5.0, "xp": 19.6},
        "in": {"id": 99, "web_name": "Benitez", "team": "CRY", "price": 4.5, "xp": 35.0},
        "gain": 15.4, "out_on_bench": False, "bank_after": 0.5,
    }]
    out = render_transfer_plan(
        plan, "TS", by_gameweek_by_id={99: {1: 7.0, 2: 6.3}}, gameweeks=[1, 2],
    )
    assert "GW1" in out and "GW2" in out
    assert "7.0" in out and "6.3" in out          # the INCOMING player's per-GW xP
    assert "Benitez" in out and "+15.4" in out


def test_render_labels_the_metric_xi_aware_vs_raw():
    # the shown gain is self-labelled: ΔXI + "XI improvement" by default, ΔxP + "raw xP gain" under --raw
    sugg = [{
        "out": {"web_name": "A", "team": "AAA", "price": 5.0, "xp": 3.0}, "out_on_bench": False,
        "in": {"id": 2, "web_name": "B", "team": "BBB", "price": 5.0, "xp": 9.0}, "gain": 6.0,
        "position": "MID",
    }]
    xi = render_transfers(sugg, "TS")
    assert "XI improvement" in xi and "ΔXI" in xi
    raw = render_transfers(sugg, "TS", xi_aware=False)
    assert "raw xP gain" in raw and "ΔxP" in raw


# ---- XI-aware ranking (ADR-046) ---------------------------------------------

def _full_squad():
    """A legal 15 (2/5/5/3) on distinct teams, plus an xP map. The best XI is a 4-4-2
    worth 62: GK + 4 DEF@5 + 4 MID@6 + 2 FWD@6; the 5th DEF, 5th MID, 3rd FWD and 2nd GK
    (all @1) sit on the bench.
    """
    squad, xp, pid = [], {}, 1
    plan = (("GK", [6, 1]), ("DEF", [5, 5, 5, 5, 1]),
            ("MID", [6, 6, 6, 6, 1]), ("FWD", [6, 6, 1]))
    for pos, points in plan:
        for pts in points:
            player = _p(pid, pos, f"T{pid}", 5.0)   # distinct team → no club-cap noise
            player["total_points"] = 0              # select_squad (via best_legal_xi) sums this
            squad.append(player)
            xp[pid] = float(pts)
            pid += 1
    return squad, xp


def test_best_xi_points_matches_the_ilp():
    # the fast formation-enumeration best-XI equals best_legal_xi's total (ADR-046 §2)
    squad, xp = _full_squad()
    fast = best_xi_points(squad, xp)
    ilp = sum(xp[i] for i in best_legal_xi(squad, xp))
    assert fast == 62.0 and round(fast, 1) == round(ilp, 1)


def test_xi_gain_ranks_an_xi_upgrade_over_a_bench_only_swap():
    # Two same-price targets: a FWD@10 (lifts the fielded XI) and a DEF@2 (only beats the
    # benched 5th DEF@1 — the best XI still fields four DEF@5, so XI-gain is 0).
    squad, xp = _full_squad()
    xi_up = _p(100, "FWD", "U1", 5.0)      # replaces a fielded FWD@6 → +4 to the XI
    bench_up = _p(101, "DEF", "U2", 5.0)   # only better than the benched DEF@1 → XI unchanged
    xp[100], xp[101] = 10.0, 2.0
    market = squad + [xi_up, bench_up]

    out = suggest_transfers(squad, market, xp)          # XI-aware default
    assert out[0]["in"]["id"] == 100 and out[0]["gain"] > 0
    assert 101 not in [s["in"]["id"] for s in out]      # bench-only swap (XI-gain 0) drops out

    raw = suggest_transfers(squad, market, xp, xi_aware=False)   # --raw still surfaces it
    assert 101 in [s["in"]["id"] for s in raw]
