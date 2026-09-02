"""Tests for the gameweek plan (ADR-070) — the assembler + its renderer.

`gameweek_plan` only orchestrates already-tested primitives, so here we pin the logic it *adds*:
the lineup bring-in/drop vs the declared bench, the availability flags, and graceful None-handling
(no captain / no transfer). The primitives themselves are stubbed so the test is fast + deterministic
(no ILP, no xP machinery). The renderer is exercised on canned plans across its branches.
"""

from src.analytics import gameweek as gw
from src.analytics.transfer_timing import bank_or_use
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
    # ADR-173: a real `suggest_transfers` move always carries `gain` (and `in`), and the plan now reads both
    # for the bank-or-use verdict. The fake was under-specified — it modelled less than the real thing ever
    # returns, so it passed only while nobody looked at those keys.
    monkeypatch.setattr(gw, "suggest_transfers",
                        lambda *a, **k: [{"out": {"id": 4}, "in": {"id": 9}, "gain": 2.0}])

    plan = gw.gameweek_plan(owned, owned, [], xp, bench_ids=[3])           # declared bench = P3

    assert plan["captain"]["web_name"] == "A"
    # declared XI = {1,2,4}; optimal = {1,2,3} → bring in P3, drop P4
    assert {p["id"] for p in plan["lineup"]["bring_in"]} == {3}
    assert {p["id"] for p in plan["lineup"]["drop"]} == {4}
    assert plan["lineup"]["has_declared_bench"] is True
    assert plan["transfer"] == {"out": {"id": 4}, "in": {"id": 9}, "gain": 2.0}
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


def test_an_unexplained_exodus_reaches_the_gameweek_flags(monkeypatch):
    """ADR-146. The reported gap: Watkins had 96,095 net sales while `status` was `a` and `news` empty, and
    neither AI tips nor Health said a word. Flags previously came only from `status`, so a player FPL calls
    fit was invisible no matter how hard the crowd was selling him.
    """
    owned = [_p(1, "Fine", "AAA"),
             {"id": 2, "web_name": "Watkins", "team": "AVL", "status": "a", "chance": None, "news": "",
              "selected_by": 9.5, "transfers_in_event": 7_583, "transfers_out_event": 103_678}]
    monkeypatch.setattr(gw, "captain_picks", lambda *a, **k: [])
    monkeypatch.setattr(gw, "best_legal_xi", lambda o, s: {1})
    monkeypatch.setattr(gw, "suggest_transfers", lambda *a, **k: [])
    monkeypatch.setattr(gw, "replace_dead", lambda *a, **k: [])

    flags = gw.gameweek_plan(owned, owned, [], {1: 5.0, 2: 4.0})["flags"]
    assert [f["web_name"] for f in flags] == ["Watkins"]
    assert "96,095 sold him" in flags[0]["reason"] and "nothing in the data says why" in flags[0]["reason"]


def test_a_real_status_always_wins_over_the_crowd(monkeypatch):
    """If FPL says he is injured, say *that* — not "the crowd is nervous". The inference is the fallback for
    when the feed is silent, never a replacement for what it does tell us."""
    injured = {"id": 2, "web_name": "Porro", "team": "TOT", "status": "d", "chance": 75,
               "news": "Lack of match fitness", "selected_by": 14.3,
               "transfers_in_event": 2_229, "transfers_out_event": 230_000}
    monkeypatch.setattr(gw, "captain_picks", lambda *a, **k: [])
    monkeypatch.setattr(gw, "best_legal_xi", lambda o, s: set())
    monkeypatch.setattr(gw, "suggest_transfers", lambda *a, **k: [])
    monkeypatch.setattr(gw, "replace_dead", lambda *a, **k: [])

    (flag,) = gw.gameweek_plan([injured], [injured], [], {2: 4.0})["flags"]
    assert flag["reason"] == "doubtful" and "sold him" not in flag["reason"]


def test_a_reported_leaver_is_benched_and_never_captained_while_the_window_is_open(monkeypatch):
    """ADR-154. `decision_xp` still rates a departing player highly — FPL calls him available — so the plan
    flagged him, recommended replacing him, **and put him in the XI anyway**.

    His xP is zeroed **for selection only**: a local copy of the map that goes no further than this call. The
    stored `decision_xp` is untouched and every other surface still shows it.
    """
    leaver = {"id": 2, "web_name": "Watkins", "team": "AVL", "status": "a", "chance": None, "news": "",
              "selected_by": 9.5, "transfers_in_event": 0, "transfers_out_event": 200_000}
    owned = [_p(1, "Keeper", "AAA"), leaver, _p(3, "Other", "BBB")]
    events = {2: [{"kind": "transfer", "source": "Romano", "title": "…deal to sign Ollie Watkins"}]}

    seen = {}

    def fake_captain(pool, *a, **k):
        seen["pool"] = [p["id"] for p in pool]
        return []

    def fake_xi(_owned, scores):
        seen["scores"] = dict(scores)
        return {1}

    monkeypatch.setattr(gw, "captain_picks", fake_captain)
    monkeypatch.setattr(gw, "best_legal_xi", fake_xi)
    monkeypatch.setattr(gw, "suggest_transfers", lambda *a, **k: [])
    monkeypatch.setattr(gw, "replace_dead", lambda *a, **k: [])

    from datetime import date
    gw.gameweek_plan(owned, owned, [], {1: 3.0, 2: 9.0, 3: 4.0}, events_by_id=events, today=date(2026, 8, 27))

    assert seen["scores"][2] == 0.0, "ranked as if he scores nothing — because he will"
    assert seen["scores"][1] == 3.0 and seen["scores"][3] == 4.0, "nobody else is touched"
    assert 2 not in seen["pool"], "and he must never be captained"


def test_outside_a_transfer_window_he_is_treated_completely_normally(monkeypatch):
    """The owner's caveat: *"we could get a reported to be leaving outside the window and we should not react
    in that case."* In October he plays on until January, so nothing changes at all."""
    leaver = {"id": 2, "web_name": "Watkins", "team": "AVL", "status": "a", "chance": None, "news": "",
              "selected_by": 9.5, "transfers_in_event": 0, "transfers_out_event": 200_000}
    owned = [_p(1, "Keeper", "AAA"), leaver]
    events = {2: [{"kind": "transfer", "source": "Romano", "title": "…deal to sign Ollie Watkins"}]}

    seen = {}

    def fake_captain(pool, *a, **k):
        seen["pool"] = [p["id"] for p in pool]
        return []

    def fake_xi(_owned, scores):
        seen["scores"] = dict(scores)
        return {1}

    monkeypatch.setattr(gw, "captain_picks", fake_captain)
    monkeypatch.setattr(gw, "best_legal_xi", fake_xi)
    monkeypatch.setattr(gw, "suggest_transfers", lambda *a, **k: [])
    monkeypatch.setattr(gw, "replace_dead", lambda *a, **k: [])

    from datetime import date
    gw.gameweek_plan(owned, owned, [], {1: 3.0, 2: 9.0}, events_by_id=events, today=date(2026, 10, 15))

    assert seen["scores"][2] == 9.0, "his xP stands — he is not going anywhere until January"
    assert 2 in seen["pool"], "and he is a perfectly good captain"


# ---- ADR-173: the plan offers the alternative and the longer view ----------

def _tr(gain=2.0, out_id=1, in_id=2):
    return {"position": "MID", "out": {"id": out_id, "web_name": "Out", "team": "ARS", "price": 5.0, "xp": 3.0},
            "in": {"id": in_id, "web_name": "In", "team": "CHE", "price": 5.0, "xp": 3.0 + gain},
            "gain": gain, "out_on_bench": False}


def _plan(transfer=None, timing=None, horizon_gain=None):
    return {"captain": None, "captain_ranked": [], "flags": [], "replacements": [],
            "lineup": {"start": [], "drop": [], "has_declared_bench": False},
            "transfer": transfer, "timing": timing, "horizon_gain": horizon_gain, "horizon_gw": 5}


def test_the_plan_says_when_banking_beats_spending():
    """The owner's point: *"there is value in letting your transfers build up."*

    The arithmetic for this has existed since ADR-132 and was wired into the Transfer tab only — so the
    surface most people read presented one option as the only one. It never lied; it just never mentioned
    the alternative.
    """
    timing = bank_or_use([{"gain": 0.3}, {"gain": 3.0}], 0.3)
    assert timing["action"] == "bank"
    out = render_gameweek_plan(_plan(_tr(0.3), timing), "TST", horizon=1)
    assert "Or bank it:" in out and "saves 3.0" in out


def test_a_worthwhile_move_is_not_second_guessed():
    # When spending is right, no "or bank it" line — an alternative offered every week is noise, not advice.
    out = render_gameweek_plan(_plan(_tr(4.0), bank_or_use([{"gain": 4.0}], 4.0)), "TST", horizon=1)
    assert "Or bank it" not in out


def test_the_longer_view_names_the_disagreement():
    """A one-week gain reads as a season verdict when it stands alone — the mistake the owner caught.

    He rejected a transfer that was right for next week and wrong for his season, and the line said only
    "+1.5 XI xP next GW". The window was never hidden; the *other* window was simply absent.
    """
    worse = render_gameweek_plan(_plan(_tr(2.0), None, horizon_gain=0.4), "TST", horizon=1)
    assert "worth less over the next 5 GWs" in worse

    better = render_gameweek_plan(_plan(_tr(2.0), None, horizon_gain=9.0), "TST", horizon=1)
    assert "still ahead over the next 5 GWs" in better


def test_no_transfer_means_no_timing_lines():
    out = render_gameweek_plan(_plan(None, bank_or_use([], None), horizon_gain=3.0), "TST", horizon=1)
    assert "Longer view" not in out and "Or bank it" not in out


def test_the_plan_always_carries_a_timing_verdict(monkeypatch):
    """`timing` is always present, so a caller cannot silently drop the alternative."""
    import src.analytics.gameweek as gw
    monkeypatch.setattr(gw, "captain_picks", lambda *a, **k: [])
    monkeypatch.setattr(gw, "best_legal_xi", lambda o, s: set())
    monkeypatch.setattr(gw, "suggest_transfers", lambda *a, **k: [])
    monkeypatch.setattr(gw, "replace_dead", lambda *a, **k: [])
    plan = gw.gameweek_plan([], [], [], {}, bench_ids=[])
    assert plan["timing"]["action"] == "bank"          # nothing worth doing → hold it
    assert plan["horizon_gain"] is None
