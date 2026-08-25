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
    assert "Model note:" not in out                             # US-278: no note without an explanation


def test_render_gameweek_plan_appends_the_model_note_when_explained():
    from src.analytics.explain import Explanation
    ex = {"overall": Explanation(reasons=["Clear captain"], risks=[], confidence=60, band="Medium")}
    out = render_gameweek_plan(_FULL_PLAN, "TS", explanation=ex)
    assert "Model note:" in out                                 # the honest footer closes the explained plan


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


# ---- dead slots in the plan (ADR-136) ------------------------------------------------

def _dead_plan(replacements):
    """A canned plan whose only interesting part is its dead slots."""
    return {"captain": None, "captain_ranked": [], "transfer": None, "flags": [],
            "replacements": replacements,
            "lineup": {"start": [], "bench": [], "bring_in": [], "drop": [], "has_declared_bench": False}}


def test_the_plan_keeps_dead_slots_in_their_own_key(monkeypatch):
    """`replacements` is deliberately NOT folded into `transfer`. Its `gain` answers a different question —
    what the slot throws away, not what the swap adds to the XI — and a differently-meaning number in an
    existing field is how consumers start lying (ADR-136)."""
    owned = [_p(1, "A", "AAA"), _p(2, "Destan", "HUL", status="u", chance=0)]
    monkeypatch.setattr(gw, "captain_picks", lambda *a, **k: [])
    monkeypatch.setattr(gw, "best_legal_xi", lambda o, s: {1})
    monkeypatch.setattr(gw, "suggest_transfers", lambda *a, **k: [])
    monkeypatch.setattr(gw, "replace_dead", lambda *a, **k: [{"out": {"web_name": "Destan"}}])

    plan = gw.gameweek_plan(owned, owned, [], {1: 5.0, 2: 0.0})
    assert plan["transfer"] is None, "the XI-gain answer is unchanged and still says 'nothing to upgrade'"
    assert plan["replacements"][0]["out"]["web_name"] == "Destan", "…and the hole is reported separately"


def test_the_renderer_names_the_dead_slot_and_stops_saying_hold():
    """The reported bug, at the surface: "no positive-gain upgrade — hold your transfer" printed over a squad
    containing a player who had left the league. Both halves are pinned — the new line appears, and the old
    line stops contradicting it."""
    plan = _dead_plan([{"out": {"web_name": "Destan", "team": "HUL", "price": 4.5},
                        "in": {"web_name": "Thomas-Asante", "team": "COV", "price": 5.0},
                        "gain": 7.4, "reason": "gone", "out_on_bench": True}])
    text = render_gameweek_plan(plan, "RoboTS", horizon=5)
    assert "Destan" in text and "gone" in text and "Thomas-Asante" in text
    assert "hold your transfer" not in text, "the exact sentence this was reported as"
    assert text.index("Replace:") < text.index("Transfer:"), "a dead slot outranks a marginal upgrade"


def test_a_healthy_squad_renders_no_dead_slot_line_at_all():
    """It must cost nothing for the managers it doesn't apply to — and 'hold' is honest again when the 15 are
    whole, so that wording comes back."""
    text = render_gameweek_plan(_dead_plan([]), "RoboTS", horizon=5)
    assert "Replace:" not in text
    assert "hold your transfer" in text


def test_a_plan_without_the_key_at_all_still_renders():
    """Older callers (and any canned plan in a test) must not crash on a key added later."""
    plan = _dead_plan([])
    del plan["replacements"]
    assert "Transfer:" in render_gameweek_plan(plan, "RoboTS")
