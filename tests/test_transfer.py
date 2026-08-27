"""Tests for transfer suggestions (ADR-030).

Each FPL constraint is exercised in isolation: position, not-already-owned,
availability, budget (self-funding vs --bank), and ≤3/club (incl. the same-club-swap
edge case). Plus xP-gain ranking, positive-gains-only, the bench flag, and no-upgrade.
Offline, plain dicts.
"""

from datetime import date as _date

from src.analytics import (
    SQUAD_15,
    best_legal_xi,
    best_xi_points,
    replace_dead,
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


# ---- replace_dead (ADR-136) ----------------------------------------------------------

def _dp(pid, name, pos, team, price, status="a", news=""):
    return {"id": pid, "web_name": name, "position": pos, "team": team, "price": price,
            "status": status, "news": news, "chance": None}


_DEAD_FIXTURES = [{"event": gw, "home": "HUL", "away": "COV",
                   "kickoff_time": f"2026-09-{gw:02d}T14:00:00Z"} for gw in (2, 3, 4, 5, 6)]
_TODAY = _date(2026, 8, 25)


# Clubs spread so the squad is legal under ≤3/club — otherwise every replacement is correctly refused and
# the test would "pass" for the wrong reason.
_CLUBS = ("ARS", "AVL", "BHA", "CRY", "EVE", "IPS")


def _dead_squad():
    """A legal squad whose only problem is a departed forward sitting on the bench."""
    return ([_dp(1, "GK1", "GK", "ARS", 4.5), _dp(2, "GK2", "GK", "AVL", 4.0)]
            + [_dp(10 + i, f"D{i}", "DEF", _CLUBS[i], 5.0) for i in range(5)]
            + [_dp(20 + i, f"M{i}", "MID", _CLUBS[i], 6.0) for i in range(5)]
            + [_dp(30, "F0", "FWD", "BHA", 7.0), _dp(31, "F1", "FWD", "CRY", 6.5),
               _dp(32, "Destan", "FWD", "HUL", 4.5, status="u", news="Has joined Konyaspor permanently")])


def test_a_dead_player_on_the_bench_is_invisible_to_the_xi_ranking_but_not_to_replace_dead():
    """The bug as reported, as a test. `suggest_transfers` is right about what it measures — replacing a
    benched dead player lifts the best legal XI by exactly zero, so `if gain > 0` drops it and the advice
    reads "hold". The slot is still a permanent zero with no auto-sub cover."""
    owned = _dead_squad()
    market = owned + [_dp(99, "Sub", "FWD", "NEW", 4.5)]
    xp = {p["id"]: 5.0 for p in market}
    xp[32] = 0.0                                            # the dead man scores nothing, by construction
    xp[99] = 4.0    # worse than any starter, so there is genuinely no XI upgrade — but far better than zero

    assert suggest_transfers(owned, market, xp, bench_ids=[32], bank=0.0) == [], "the reported 'hold'"

    (move,) = replace_dead(owned, market, xp, _DEAD_FIXTURES, today=_TODAY, bench_ids=[32])
    assert move["out"]["web_name"] == "Destan" and move["in"]["web_name"] == "Sub"
    assert move["gain"] == 4.0, "the gain is what the slot throws away, not what the XI gains"
    assert move["reason"] == "gone" and move["out_on_bench"] is True


def test_it_names_the_best_replacement_not_the_cheapest_body():
    """"Any playing £4.5m body is pure upside" describes the floor, not the target. If the best affordable
    replacement is worth 16.9 xP, that is the one worth naming."""
    owned = _dead_squad()
    market = owned + [_dp(98, "Cheap", "FWD", "NEW", 4.0), _dp(99, "Better", "FWD", "TOT", 4.5)]
    xp = {p["id"]: 5.0 for p in market} | {32: 0.0, 98: 3.0, 99: 9.0}
    (move,) = replace_dead(owned, market, xp, _DEAD_FIXTURES, today=_TODAY, bench_ids=[32])
    assert move["in"]["web_name"] == "Better"


def test_the_replacement_must_be_a_legal_affordable_available_move():
    """Same rules as any transfer — this is advice you can act on, not a wish."""
    owned = _dead_squad()
    market = owned + [
        _dp(97, "TooDear", "FWD", "NEW", 9.9),                                    # unaffordable
        _dp(96, "AlsoHurt", "FWD", "NEW", 4.5, status="i", news="Unknown return date"),   # unavailable
        _dp(95, "WrongPos", "MID", "NEW", 4.5),                                   # wrong position
        _dp(94, "Fine", "FWD", "IPS", 4.5),
    ]
    xp = {p["id"]: 1.0 for p in market} | {32: 0.0, 97: 50.0, 96: 40.0, 95: 30.0, 94: 4.0}
    (move,) = replace_dead(owned, market, xp, _DEAD_FIXTURES, today=_TODAY, bench_ids=[32], bank=0.0)
    assert move["in"]["web_name"] == "Fine"


def test_two_dead_slots_get_different_replacements():
    """Offering the same player twice would be advice you cannot follow."""
    owned = [p for p in _dead_squad() if p["id"] != 31]
    owned.append(_dp(33, "Uche", "FWD", "HUL", 4.5, status="u", news="has returned to Getafe CF"))
    market = owned + [_dp(99, "A", "FWD", "NEW", 4.5), _dp(98, "B", "FWD", "TOT", 4.5)]
    xp = {p["id"]: 1.0 for p in market} | {32: 0.0, 33: 0.0, 99: 9.0, 98: 8.0}
    moves = replace_dead(owned, market, xp, _DEAD_FIXTURES, today=_TODAY, bench_ids=[32])
    assert len(moves) == 2
    assert {m["in"]["web_name"] for m in moves} == {"A", "B"}, "no incoming player suggested twice"
    assert [m["in"]["web_name"] for m in moves] == ["A", "B"], "biggest recovery first"


def test_a_healthy_squad_produces_nothing_at_all():
    """It must cost nothing — no line, no space — for the managers it doesn't apply to."""
    owned = [p for p in _dead_squad() if p["id"] != 32] + [_dp(32, "Fit", "FWD", "HUL", 4.5)]
    xp = {p["id"]: 5.0 for p in owned}
    assert replace_dead(owned, owned, xp, _DEAD_FIXTURES, today=_TODAY) == []


def test_the_banner_states_its_reasoning_and_disappears_when_the_squad_is_whole():
    """A dead slot needs a *reason*, not a number: "has joined Inter" is what makes a manager act. And the
    banner must cost nothing — no line at all — for the squads it doesn't apply to (ADR-136)."""
    from src.ui.transfer import render_dead_slots

    assert render_dead_slots([]) == ""
    text = render_dead_slots([{"out": {"web_name": "Destan", "team": "HUL", "price": 4.5},
                               "in": {"web_name": "Thomas-Asante", "team": "COV", "price": 5.0},
                               "gain": 7.4, "reason": "gone", "out_on_bench": True}], horizon=5)
    assert "Destan" in text and "gone" in text and "on your bench" in text
    assert "7.4" in text and "auto-sub cover" in text, "it must say WHY a zero-XI-gain move is worth making"


def test_the_no_upgrade_line_stops_contradicting_the_banner_above_it():
    """"The squad may already be strong" printed directly beneath a dead-slot warning is the reported bug
    wearing different words."""
    whole = render_transfers([], "S", bank=0.5, horizon=5)
    with_dead = render_transfers([], "S", bank=0.5, horizon=5, has_dead=True)
    assert "may already be strong" in whole
    assert "may already be strong" not in with_dead and "dead slot" in with_dead


def test_a_reported_leaver_is_measured_against_zero_not_his_paper_xp():
    """ADR-153. For a player the press and the crowd both say is leaving, his projected xP is **fiction**:
    FPL still calls him available, so `decision_xp` credits him a full horizon of points he will not be here
    to score.

    Comparing a replacement against that produced *"recovers **−8.6** xP"* on the live squad — a negative
    recovery, which is not a sentence about anything. The baseline is 0, exactly as it already is for a player
    FPL has marked `u`. No analytics change: `decision_xp` is untouched, and only this slot's arithmetic uses
    the number that will actually happen.
    """
    owned = _dead_squad()
    leaver = owned[-1]
    leaver.update(status="a", news="")                     # FPL has not caught up
    market = owned + [_dp(99, "Replacement", "FWD", "NEW", 4.5)]
    xp = {p["id"]: 1.0 for p in market} | {leaver["id"]: 9.0, 99: 6.0}

    (move,) = replace_dead(owned, market, xp, _DEAD_FIXTURES, today=_TODAY,
                           reported_out={leaver["id"]: {"kind": "transfer", "source": "Romano", "title": "t"}})
    assert move["gain"] == 6.0, "the replacement is worth what he scores, not the difference from a fiction"
    assert move["gain"] > 0, "a recovery must never read as negative"
    assert move["out"]["xp"] == 0.0 and move["reported"] is True


# ---- Reported departures in the ranking (ADR-156) --------------------------------------------------
# The owner: "Transfer doesn't pick up Watkins, he is not recommended to transfer." The ranking compared a
# replacement against the 4.3 xP FPL still credits a player with an agreed move to Al-Hilal — points he will
# never score — so the most urgent transfer in the squad ranked below a marginal upgrade.

_LEAVING = {"kind": "transfer", "source": "Romano", "title": "Al Hilal, here we go!"}


def test_a_reported_leaver_is_valued_at_zero_in_the_ranking():
    owned = [_p(1, "MID", "AAA", 5.0)]
    market = owned + [_p(2, "MID", "BBB", 5.0)]
    xp = {1: 6.0, 2: 7.0}
    # Without the fact he is worth 6.0, so the swap gains a nominal 1.0…
    assert suggest_transfers(owned, market, xp, xi_aware=False)[0]["gain"] == 1.0
    # …with it, the honest question is "7.0 versus nothing".
    out = suggest_transfers(owned, market, xp, xi_aware=False, reported_out={1: _LEAVING})
    assert out[0]["gain"] == 7.0
    assert out[0]["out"]["xp"] == 0.0           # shown as zero, because this surface recommends
    assert out[0]["out"]["leaving"] == _LEAVING


def test_a_departing_player_is_never_a_suggested_signing():
    owned = [_p(1, "MID", "AAA", 5.0)]
    market = owned + [_p(2, "MID", "BBB", 5.0)]
    xp = {1: 3.0, 2: 9.0}
    assert suggest_transfers(owned, market, xp, xi_aware=False, reported_out={2: _LEAVING}) == []


def test_the_stored_xp_map_is_never_mutated_by_the_ranking():
    """The zeroing is a local copy — `decision_xp` is the app's single recipe and this must not touch it."""
    owned = [_p(1, "MID", "AAA", 5.0)]
    market = owned + [_p(2, "MID", "BBB", 5.0)]
    xp = {1: 6.0, 2: 7.0}
    suggest_transfers(owned, market, xp, xi_aware=False, reported_out={1: _LEAVING})
    assert xp == {1: 6.0, 2: 7.0}


def test_the_fact_threads_through_every_step_of_a_plan():
    owned = [_p(1, "MID", "AAA", 5.0), _p(3, "DEF", "AAA", 5.0)]
    market = owned + [_p(2, "MID", "BBB", 5.0), _p(4, "DEF", "CCC", 5.0)]
    xp = {1: 6.0, 2: 7.0, 3: 1.0, 4: 2.0}
    plan = suggest_transfer_plan(owned, market, xp, count=2, xi_aware=False, reported_out={1: _LEAVING})
    first = next(m for m in plan if m["out"]["id"] == 1)
    assert first["gain"] == 7.0                 # …and not the 1.0 his stored xP would have made it
