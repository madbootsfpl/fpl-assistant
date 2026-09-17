"""*"Bench or replace him"* assumed a bench worth using (ADR-208).

The owner, after ADR-206 stopped the app trying to sell his doubtful star:

> *"We are picking up that João Pedro is a Doubt, we are not suggesting a transfer for him — that's as
> designed, so good. BUT where we have a gap is that the other 2 fwds are zero to low scoring, we should be
> getting a backup recommendation in there."*

FPL **auto-substitutes** a starter who plays 0 minutes with the first legal bench player in his position. So
the advice *"bench him"* is only good advice if that player is worth fielding. On RoboTS it was **Walle Egeli
at 0.2 xP** — benching a doubtful 4.3 to field a 0.2 is not a mitigation, it is the loss.

⭐ **An instruction is only as good as the option it assumes you have**, so the option is now stated and the
reader decides (ADR-194's posture), rather than the app recommending a door it has not looked behind.
"""

from src.analytics.explain import _flag_action
from src.analytics.gameweek import auto_sub_cover


def _p(pid, pos, name, status="a", team="ARS"):
    return {"id": pid, "position": pos, "web_name": name, "status": status, "chance": None,
            "team": team, "price": 5.0, "selected_by": 1.0, "transfers_in_event": 0,
            "transfers_out_event": 0}


def test_cover_is_the_best_bench_player_in_the_same_position():
    flagged = _p(1, "FWD", "Star", status="d")
    bench = [_p(2, "FWD", "Weak"), _p(3, "FWD", "Weaker"), _p(4, "MID", "Irrelevant")]
    got = auto_sub_cover(flagged, bench, {2: 0.2, 3: 0.0, 4: 9.9})
    assert got == {"name": "Weak", "xp": 0.2}


def test_a_different_position_is_not_cover_however_good_he_is():
    """⚠️ FPL's auto-sub must keep the formation legal — an XI needs a goalkeeper and at least one forward.
    A 9.9-xP midfielder on the bench is not cover for a forward."""
    assert auto_sub_cover(_p(1, "FWD", "Star"), [_p(4, "MID", "Great")], {4: 9.9}) is None


def test_an_unavailable_substitute_is_not_cover():
    """⚠️ **Found by the first smoke run on the owner's real squad**, which reported *"benching E.Le Fée
    fields Foden (0.0 xP)"* about a **suspended** player. FPL's auto-sub skips a bench player who also records
    0 minutes. ⭐ *A fallback that shares the failure it is covering for is not a fallback.*"""
    bench = [_p(2, "MID", "Suspended", status="s"), _p(3, "MID", "Injured", status="i")]
    assert auto_sub_cover(_p(1, "MID", "Flagged", status="d"), bench, {2: 4.0, 3: 5.0}) is None
    ok = auto_sub_cover(_p(1, "MID", "Flagged", status="d"),
                        bench + [_p(4, "MID", "Fit")], {2: 4.0, 3: 5.0, 4: 1.0})
    assert ok == {"name": "Fit", "xp": 1.0}, "the fit one is cover even though he scores less"


def test_a_row_without_a_position_says_nothing_rather_than_matching_everything():
    """⚠️ The shared gameweek fixture carried **no `position` at all** until this ADR, because
    `best_legal_xi` is stubbed there and nothing else read it. Matching None to None would have made every
    bench player 'cover'. ⭐ *Silence beats a confident wrong answer* — and a thin row must not crash a plan.

    ⚠️ **The bench must contain a positionless row too, or this cannot fail.** A first version benched only
    a row *with* a position, so `None == "FWD"` was false and the guard was never the reason for the answer —
    the mutant that removes it survived. ⭐ *A guard is only tested by the case it exists to catch.*
    """
    thin = {"id": 1, "web_name": "Mystery", "status": "d", "chance": None}
    also_thin = {"id": 3, "web_name": "AlsoMystery", "status": "a", "chance": None}
    assert auto_sub_cover(thin, [_p(2, "FWD", "Someone"), also_thin], {2: 3.0, 3: 5.0}) is None


# --- the sentence the reader actually gets -------------------------------------------

def test_the_three_cases_are_worded_apart():
    """⭐ **"No cover" is a different problem from "weak cover" and must not be flattened into it** — one is
    solved by a transfer, the other by a judgement call."""
    assert _flag_action({"starting": True, "cover": {"name": "Weak", "xp": 0.2}}) == (
        "bench or replace him — benching him fields Weak (0.2 xP)")
    assert _flag_action({"starting": True, "cover": None}) == (
        "replace him — you have no cover on your bench")
    assert _flag_action({"starting": False, "cover": None}) == "already on your bench"


def test_a_flagged_player_already_benched_is_not_told_to_bench_him():
    """He is already there. ⭐ *Advice that describes the state you are in is noise wearing the shape of
    help* — and it was the old wording for every flagged bench player."""
    assert "bench or replace" not in _flag_action({"starting": False, "cover": None})


def test_the_plan_attaches_cover_only_to_flagged_starters(monkeypatch):
    """⭐ *Testing a component is not testing that anything uses it.* Every guard above passed while
    `auto_sub_cover` was never called from `gameweek_plan`."""
    from src.analytics import gameweek as gw

    # ⚠️ A **fit** midfielder is benched too, so "Benched" HAS cover available — otherwise the assertion
    # that flagged bench players get none would hold for the wrong reason, and the guard that restricts cover
    # to starters could be deleted without a test noticing.
    owned = [_p(1, "FWD", "Star", status="d"), _p(2, "FWD", "Weak"),
             _p(3, "MID", "Benched", status="i"), _p(4, "MID", "Fit"), _p(5, "MID", "SpareMid")]
    xp = {1: 4.3, 2: 0.2, 3: 0.0, 4: 3.0, 5: 2.0}
    monkeypatch.setattr(gw, "captain_picks", lambda *a, **k: [{"web_name": "Star", "xp": 4.3}])
    monkeypatch.setattr(gw, "best_legal_xi", lambda o, s: {1, 4})      # Star + Fit start
    monkeypatch.setattr(gw, "suggest_transfer_plan", lambda *a, **k: [])
    monkeypatch.setattr(gw, "suggest_transfers", lambda *a, **k: [])
    plan = gw.gameweek_plan(owned, owned, [], xp)
    flags = {f["web_name"]: f for f in plan["flags"]}
    assert flags["Star"]["starting"] is True
    assert flags["Star"]["cover"] == {"name": "Weak", "xp": 0.2}
    assert flags["Benched"]["starting"] is False and flags["Benched"]["cover"] is None


def test_the_lever_the_reader_sees_carries_the_cover(monkeypatch):
    """⭐ **Testing a component is not testing that anything uses it — again.**

    Every `_flag_action` guard above passed with the lever still saying the old unqualified *"bench or
    replace him"*, because they all call `_flag_action` directly and the reader never does. This goes through
    `confidence_levers`, which is what actually renders.
    """
    from src.analytics.explain import confidence_levers

    out = confidence_levers(57, [
        {"web_name": "Star", "starting": True, "cover": {"name": "Weak", "xp": 0.2}},
        {"web_name": "Other", "starting": True, "cover": None},
    ])
    text = " | ".join(lv["what"] for lv in out["levers"])
    assert "benching him fields Weak (0.2 xP)" in text, text
    assert "you have no cover on your bench" in text, text
