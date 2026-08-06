"""Tests for the gameweek plan (ADR-070) — the assembler + its renderer.

`gameweek_plan` only orchestrates already-tested primitives, so here we pin the logic it *adds*:
the lineup bring-in/drop vs the declared bench, the availability flags, and graceful None-handling
(no captain / no transfer). The primitives themselves are stubbed so the test is fast + deterministic
(no ILP, no xP machinery). The renderer is exercised on canned plans across its branches.
"""

from src.analytics import gameweek as gw
from src.ui.gameweek import render_gameweek_plan


def _p(pid, name, team, status="a", chance=None):
    return {"id": pid, "web_name": name, "team": team, "status": status, "chance": chance}


def test_gameweek_plan_assembles_captain_lineup_transfer_and_flags(monkeypatch):
    owned = [_p(1, "A", "AAA"), _p(2, "B", "BBB"),
             _p(3, "C", "CCC", status="d", chance=75),   # doubtful (a warning, kept)
             _p(4, "D", "DDD", status="i", chance=0)]     # injured → unavailable
    xp = {1: 5.0, 2: 4.0, 3: 3.0, 4: 2.0}

    monkeypatch.setattr(gw, "captain_picks", lambda *a, **k: [{"web_name": "A", "xp": 5.0}])
    monkeypatch.setattr(gw, "best_legal_xi", lambda o, s: {1, 2, 3})       # optimal XI = 1,2,3
    monkeypatch.setattr(gw, "suggest_transfers", lambda *a, **k: [{"out": {"id": 4}}])

    plan = gw.gameweek_plan(owned, owned, [], xp, bench_ids=[3])           # declared bench = P3

    assert plan["captain"]["web_name"] == "A"
    # declared XI = {1,2,4}; optimal = {1,2,3} → bring in P3, drop P4
    assert {p["id"] for p in plan["lineup"]["bring_in"]} == {3}
    assert {p["id"] for p in plan["lineup"]["drop"]} == {4}
    assert plan["lineup"]["has_declared_bench"] is True
    assert plan["transfer"] == {"out": {"id": 4}}
    # only the unavailable/doubtful players are flagged, with the right reason (A, B are fine)
    assert {f["web_name"]: f["reason"] for f in plan["flags"]} == {"C": "doubtful", "D": "injured"}


def test_gameweek_plan_handles_no_captain_no_transfer_and_no_declared_bench(monkeypatch):
    owned = [_p(1, "A", "AAA"), _p(2, "B", "BBB")]
    monkeypatch.setattr(gw, "captain_picks", lambda *a, **k: [])           # nobody eligible
    monkeypatch.setattr(gw, "best_legal_xi", lambda o, s: {1, 2})
    monkeypatch.setattr(gw, "suggest_transfers", lambda *a, **k: [])       # no positive-gain move

    plan = gw.gameweek_plan(owned, owned, [], {1: 1.0, 2: 1.0})           # no bench_ids

    assert plan["captain"] is None and plan["transfer"] is None
    assert plan["lineup"]["has_declared_bench"] is False
    assert plan["lineup"]["bring_in"] == [] and plan["lineup"]["drop"] == []
    assert plan["flags"] == []


# ---- renderer -------------------------------------------------------------------------------------

_FULL_PLAN = {
    "captain": {"web_name": "Haaland", "team": "MCI", "xp": 6.2, "venue": "H",
                "opponent": "BUR", "penalty_taker": True, "doubtful": False},
    "lineup": {"start": [], "bench": [], "has_declared_bench": True,
               "bring_in": [{"web_name": "Saka"}], "drop": [{"web_name": "Foden"}]},
    "transfer": {"out": {"web_name": "Watkins", "team": "AVL"},
                 "in": {"web_name": "Isak", "team": "NEW"}, "gain": 1.3},
    "flags": [{"web_name": "Foden", "team": "MCI", "reason": "doubtful", "chance": 75}],
}


def test_render_gameweek_plan_shows_all_four_sections():
    out = render_gameweek_plan(_FULL_PLAN, "TS")
    assert "This week — squad 'TS'" in out
    assert "Haaland (MCI)" in out and "home vs BUR" in out and "penalty taker" in out
    assert "start Saka — bench Foden" in out
    assert "Watkins (AVL) → Isak (NEW)" in out and "+1.3 XI xP" in out
    assert "Foden (doubtful, 75%)" in out


def test_render_gameweek_plan_degraded_branches():
    plan = {"captain": None,
            "lineup": {"start": [], "bench": [], "has_declared_bench": False,
                       "bring_in": [], "drop": []},
            "transfer": None, "flags": []}
    out = render_gameweek_plan(plan, "TS")
    assert "no eligible captain" in out
    assert "no saved bench" in out
    assert "no positive-gain upgrade" in out
    assert "all your players are available" in out
