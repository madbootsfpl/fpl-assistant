"""Tests for transfer timing (ADR-132).

The roadmap asked for a multi-gameweek transfer *path search*. A prototype found no path: the best sell was the
same player in all six gameweeks, and the whole market yielded one positive-gain move. So this is the
arithmetic a manager actually faces — use it, bank it, or take the hit — and these pin the sums.
"""

from src.analytics.transfer_timing import (
    bank_or_use,
    free_transfer_run,
    hit_is_worth_it,
    transfer_timing,
)


def _mv(out="A", inn="B", gain=3.0):
    return {"out": {"web_name": out, "id": 1}, "in": {"web_name": inn, "id": 2}, "gain": gain}


# ---- the free-transfer run ---------------------------------------------------------

def test_unused_transfers_roll_over_and_cap_at_five():
    assert free_transfer_run(1, 7) == [1, 2, 3, 4, 5, 5, 5]


def test_spending_one_resets_the_roll():
    assert free_transfer_run(1, 5, made_per_gw=[1]) == [1, 1, 2, 3, 4]


def test_spending_more_than_you_hold_floors_at_zero():
    """Spending beyond your free transfers is exactly what a hit is — the count must not go negative."""
    assert free_transfer_run(1, 3, made_per_gw=[3]) == [1, 1, 2]


# ---- the hit threshold --------------------------------------------------------------

def test_a_hit_needs_to_gain_more_than_it_costs():
    assert hit_is_worth_it(4.1) is True
    assert hit_is_worth_it(4.0) is False        # equal is not worth it
    assert hit_is_worth_it(3.0) is False        # the live case: the best move over six weeks
    assert hit_is_worth_it(None) is False


# ---- bank or use ---------------------------------------------------------------------

def test_no_worthwhile_move_means_bank():
    assert bank_or_use([])["action"] == "bank"
    assert bank_or_use([_mv(gain=0.0)])["action"] == "bank"


def test_holding_two_transfers_removes_the_reason_to_wait():
    assert bank_or_use([_mv(gain=3.0), _mv(gain=6.0)], 1.0, free=2)["action"] == "use"


def test_banking_wins_when_it_saves_more_than_waiting_costs():
    """Banking buys one thing — a second free transfer — so its value is the hit it avoids."""
    d = bank_or_use([_mv(gain=3.0), _mv("C", "D", 6.0)], 1.2)
    assert d["action"] == "bank" and d["value"] == 4.0 and d["cost"] == 1.2


def test_the_saving_is_capped_by_the_second_move_s_own_gain():
    """Avoiding a 4-point hit to make a move worth 1.0 gains you 1.0, not 4.0."""
    d = bank_or_use([_mv(gain=3.0), _mv("C", "D", 1.0)], 0.4)
    assert d["value"] == 1.0


def test_using_wins_when_waiting_costs_more_than_it_saves():
    d = bank_or_use([_mv(gain=3.0), _mv("C", "D", 1.0)], 2.0)
    assert d["action"] == "use"


def test_no_second_move_means_nothing_to_bank_for():
    d = bank_or_use([_mv(gain=3.0)], 1.2)
    assert d["action"] == "use" and d["value"] == 0.0


# ---- the whole picture reads as one plan ---------------------------------------------

def test_banking_never_also_advises_taking_the_hit():
    """A second move that would justify a hit is the *reason* to bank. Saying both reads as two opinions."""
    t = transfer_timing([_mv(gain=3.0), _mv("C", "D", 6.0)], free=1, next_gw_gain=1.2, horizon=6)
    assert "Bank your free transfer" in t["headline"]
    assert "banking makes it free" in t["hit_verdict"]
    assert "more than the" not in t["hit_verdict"]


def test_the_live_case_reads_plainly():
    """One move worth 3.0 over six gameweeks, and a hit costs 4."""
    t = transfer_timing([_mv("Gibbs-White", "Cunha", 3.0)], free=1, next_gw_gain=1.2, horizon=6)
    assert "Use your free transfer" in t["headline"] and "Gibbs-White" in t["headline"]
    assert t["take_hit"] is False
    assert "no hit to consider" in t["hit_verdict"]      # no second move, so hits aren't mentioned twice


def test_nothing_worth_doing_says_hold():
    t = transfer_timing([], free=1, horizon=6)
    assert "hold" in t["headline"] and "Nothing is worth transferring in" in t["hit_verdict"]


def test_a_second_move_worth_the_hit_is_recommended_when_banking_is_not():
    t = transfer_timing([_mv(gain=3.0), _mv("C", "D", 6.0)], free=1, next_gw_gain=9.0, horizon=6)
    assert t["decision"]["action"] == "use" and t["take_hit"] is True
    assert "worth the hit" in t["headline"]


# ---- A dead slot takes the free transfer (ADR-156) ------------------------------------------------
# The page used to say two things at once: a ⛔ banner naming Watkins as unable to score, and — directly
# beneath it — "use your free transfer on Gibbs-White → Cunha". Both were computed correctly; neither knew
# about the other.

def _dead(out="Watkins", inn="Welbeck", gain=15.5, reason="per Romano"):
    return {"out": {"web_name": out, "id": 9}, "in": {"web_name": inn, "id": 8},
            "gain": gain, "reason": reason}


def test_a_dead_slot_takes_the_free_transfer_ahead_of_a_bigger_looking_upgrade():
    t = transfer_timing([_mv("Gibbs-White", "Cunha", 3.3)], free=1, next_gw_gain=1.2, horizon=6,
                        dead=[_dead()])
    assert "Watkins → Welbeck" in t["headline"]
    assert "per Romano" in t["headline"]                 # the reader can check the claim
    assert t["decision"]["action"] == "use"
    assert "Gibbs-White" not in t["headline"], "the upgrade drops to being the hit question"


def test_a_dead_slot_is_never_banked_against():
    """Banking buys a second free transfer next week. A hole in the squad costs the same every week it stays."""
    # next_gw_gain 0.0 + a second move worth 6.0 is the textbook "bank it" case…
    banked = transfer_timing([_mv(gain=1.0), _mv("C", "D", 6.0)], free=1, next_gw_gain=0.0, horizon=6)
    assert banked["decision"]["action"] == "bank"
    # …and it stops being one the moment part of the squad cannot play.
    t = transfer_timing([_mv(gain=1.0), _mv("C", "D", 6.0)], free=1, next_gw_gain=0.0, horizon=6,
                        dead=[_dead()])
    assert t["decision"]["action"] == "use"
    assert "Bank" not in t["headline"]


def test_the_best_ordinary_move_becomes_the_hit_question_behind_a_dead_slot():
    t = transfer_timing([_mv("Gibbs-White", "Cunha", 6.5)], free=1, horizon=6, dead=[_dead()])
    assert t["take_hit"] is True                         # 6.5 > the 4-point hit
    assert "Gibbs-White → Cunha" in t["hit_verdict"]

    quiet = transfer_timing([], free=1, horizon=6, dead=[_dead()])
    assert "only move worth making" in quiet["hit_verdict"]
    assert "Nothing is worth transferring in" not in quiet["hit_verdict"]


def test_the_two_gains_are_never_compared_as_numbers():
    """ADR-136 keeps them apart: `replace_dead`'s gain is 'points recovered from zero', an upgrade's is
    'XI improvement'. The dead slot wins on kind, so a *smaller* number still goes first."""
    t = transfer_timing([_mv("Gibbs-White", "Cunha", 9.9)], free=1, horizon=6,
                        dead=[_dead(gain=1.1)])
    assert "Watkins → Welbeck" in t["headline"]


# ---- ADR-186: bank to afford, not only to stack ------------------------------------------------

def _cliff_market():
    """A squad with one clear weak slot, and two replacements: one affordable now, one better and dearer."""
    # ⚠ `status`/`chance` included: `gameweek_plan` filters on availability before it reaches the transfer
    # search, so a row without them cannot get that far. The recurring failure here is a fixture that models
    # less than the payload — this one has to satisfy the whole assembly, not just `affordability_cliff`.
    def row(pid, name, pos, team, price):
        return {"id": pid, "web_name": name, "position": pos, "team": team, "price": price,
                "status": "a", "chance": None, "total_points": 0, "code": pid,
                # `gameweek_plan` also picks a captain, which prices players through `decision_xp` — so the
                # row has to satisfy that too. Modelling less than the payload is how a fixture stops being
                # able to reach the code it is aimed at.
                "points_per_game": 0.0, "minutes": 0, "form": 0.0, "ep_next": 0.0, "team_id": 1,
                "selected_by": 5.0, "penalties_order": None, "corners_order": None,
                "freekicks_order": None, "cost_change_event": 0, "transfers_in_event": 0}

    owned = [row(i, f"P{i}", "MID", f"T{i}", 6.0) for i in range(1, 15)]
    owned.append(row(99, "Weak", "FWD", "T9", 6.0))
    cheap = row(200, "Cheap", "FWD", "TA", 6.0)
    dear = row(201, "Dear", "FWD", "TB", 7.5)
    xp = {p["id"]: 10.0 for p in owned} | {99: 1.0, 200: 8.4, 201: 14.8}
    return owned, owned + [cheap, dear], xp


def _fake_suggest(owned, market, xp, *, bank=0.0, limit=1, **kw):
    """A stand-in for `suggest_transfers`: the best affordable swap for the weakest owned player."""
    out = min(owned, key=lambda p: xp.get(p["id"], 0.0))
    budget = out["price"] + bank
    cands = [p for p in market if p["id"] not in {o["id"] for o in owned}
             and p["position"] == out["position"] and p["price"] <= budget + 1e-9]
    if not cands:
        return []
    best = max(cands, key=lambda p: xp.get(p["id"], 0.0))
    gain = xp.get(best["id"], 0.0) - xp.get(out["id"], 0.0)
    return [{"out": out, "in": best, "gain": round(gain, 2)}][:limit]


def test_a_better_move_just_out_of_budget_is_reported():
    """ADR-186, owner: *"you are not suggesting to hold on making transfers for a couple of weeks to buy a
    more expensive player than you can afford."*

    Measured on his squad at £0.0m bank: **Watkins → Havertz +7.4** today, **Watkins → Isak +13.8** with
    **£1.5m** more. The cliff is steep and was invisible — every move is priced against today's bank and the
    best one is reported as *the* answer.
    """
    from src.analytics.transfer_timing import affordability_cliff

    owned, market, xp = _cliff_market()
    cliff = affordability_cliff(owned, market, xp, bank=0.0, suggest=_fake_suggest)
    assert cliff, "a +6.4 uplift for £1.5m must be reported"
    assert cliff["move"]["in"]["web_name"] == "Dear"
    assert cliff["best_now"]["in"]["web_name"] == "Cheap", "the affordable move is still named"
    assert cliff["uplift"] == round(14.8 - 8.4, 1)


def test_it_reports_the_cheapest_budget_that_unlocks_the_move():
    """*"£1.5m more"* is actionable; *"£2m more"* when £1.5m suffices is wrong in the direction that costs
    the manager money. The sweep stops at the first budget that clears the bar."""
    from src.analytics.transfer_timing import affordability_cliff

    owned, market, xp = _cliff_market()
    cliff = affordability_cliff(owned, market, xp, bank=0.0, suggest=_fake_suggest, step=0.5)
    assert cliff["extra"] == 1.5, f"Dear costs 7.5 against a 6.0 sale — exactly £1.5m: {cliff['extra']}"


def test_no_cliff_is_reported_when_there_is_nothing_worth_waiting_for():
    """Silence is the common case and the whole reason this is safe to add. Three ways it must stay quiet:
    the money is already there, nothing better exists, and the uplift is too small to mention."""
    from src.analytics.transfer_timing import affordability_cliff

    owned, market, xp = _cliff_market()
    assert affordability_cliff(owned, market, xp, bank=5.0, suggest=_fake_suggest) is None, \
        "with the money already in the bank there is nothing to wait for"
    assert affordability_cliff(owned, owned, xp, bank=0.0, suggest=_fake_suggest) is None, \
        "no market means no better move"

    xp_flat = {**xp, 201: 8.9}                      # the dearer option is only +0.5 better
    assert affordability_cliff(owned, market, xp_flat, bank=0.0, suggest=_fake_suggest) is None, \
        "a trivial uplift must not be dressed up as a reason to wait"


def test_the_cliff_never_replaces_the_move_you_can_make_today():
    """The immediate advice stays the headline. This is a *reason you might wait*, not a recommendation to
    do nothing — and a manager who cannot raise the money must still be told what to do now."""
    from src.analytics.gameweek import gameweek_plan
    from src.ui.gameweek import render_gameweek_plan

    plan = {"captain": None, "lineup": {"start": [], "bench": [], "bring_in": [], "drop": [],
                                        "has_declared_bench": False},
            # ⚠ `team` included: the renderer prints "(TEAM)" beside each name, so a fixture without it
            # cannot reach the code under test — it KeyErrors first. The recurring failure in this repo is a
            # fixture that models less than the payload.
            "transfer": {"out": {"web_name": "Weak", "team": "T9"},
                         "in": {"web_name": "Cheap", "team": "TA"}, "gain": 7.4},
            "flags": [], "timing": {"action": "use"}, "horizon_gain": None,
            "cliff": {"extra": 1.5, "gain": 13.8, "uplift": 6.4,
                      "move": {"out": {"web_name": "Weak", "team": "T9"},
                               "in": {"web_name": "Dear", "team": "TB"}},
                      "best_now": None, "gain_now": 7.4}}
    out = render_gameweek_plan(plan, "S", horizon=5)
    assert "Weak" in out and "Cheap" in out, "the move you can make today is still named first"
    assert "Worth saving for: £1.5m more" in out, out
    assert "+13.8" in out and "+6.4" in out
    assert gameweek_plan is not None


def test_the_gameweek_plan_actually_computes_a_cliff(monkeypatch):
    """⚠️ **The wiring, not the component.** Every test above either calls `affordability_cliff` directly or
    hands `render_gameweek_plan` a pre-built dict — so a mutation setting `cliff = None` inside
    `gameweek_plan` passed all of them. ADR-185's lesson, one sprint later: **testing a component is not
    testing that anything uses it.**

    ⚠️⚠️ **And the first version of *this* test skipped instead of failing.** It asserted `"cliff" in plan`
    then returned early when the value was None — which is exactly what the mutation produces. **A test that
    skips is not a test that passes** (ADR-178), and the skip is invisible in a green run.

    So it asserts the **call**: `gameweek_plan` must ask `affordability_cliff`, with this squad, this market
    and this bank. That holds whether or not today's data happens to contain a cliff.
    """
    from src.analytics import gameweek as gw_mod

    seen = {}
    real = gw_mod.affordability_cliff

    def spy(owned, market, xp_by_id, **kw):
        seen.update(n_owned=len(owned), n_market=len(market), bank=kw.get("bank"),
                    suggest=kw.get("suggest"))
        return real(owned, market, xp_by_id, **kw)

    monkeypatch.setattr(gw_mod, "affordability_cliff", spy)
    # The transfer search is stubbed so this exercises the **assembly**, not `decision_xp`'s internals —
    # which need a fuller player row than this fixture, and are covered by their own tests.
    monkeypatch.setattr(gw_mod, "suggest_transfers", _fake_suggest)

    owned, market, xp = _cliff_market()
    plan = gw_mod.gameweek_plan(owned, market, [], xp, bank=1.25)

    assert seen, "gameweek_plan must ask what a bigger budget would afford (ADR-186)"
    assert seen["n_owned"] == len(owned) and seen["n_market"] == len(market)
    assert seen["bank"] == 1.25, "the squad's real bank must reach it, not a default"
    assert seen["suggest"] is not None, "the transfer search is injected, not re-implemented"
    assert "cliff" in plan, "and the result is carried on the plan"


def test_the_cliff_is_priced_over_the_wider_window_not_the_page_horizon(monkeypatch):
    """⚠️ **The bug the owner found the day ADR-186 shipped: the line never appeared.**

    `affordability_cliff` was priced against `xp_by_id`, which on My Squad is **a single gameweek** since
    ADR-179 fixed that page's horizon at 1. A one-week gain can essentially never clear a 2.0 xP threshold —
    on his squad the best move was **+1.7 over one week** and **+7.4 over five**, so the cliff existed at the
    window it was measured in and was invisible at the window it rendered on.

    > **I tuned the thresholds against a five-gameweek measurement and shipped onto a one-gameweek page.**

    **The window is the fix, not the threshold.** *"Is it worth waiting a fortnight for a better player?"* is
    a question about several gameweeks; a one-week gain is the wrong yardstick for it. The plan already
    computes `horizon_xp` over a wider span for ADR-173's *Longer view* line, so the two now answer the same
    question over the same number of weeks.
    """
    from src.analytics import gameweek as gw_mod

    seen = {}
    real = gw_mod.affordability_cliff

    def spy(owned, market, xp_by_id, **kw):
        seen["xp"] = xp_by_id
        return real(owned, market, xp_by_id, **kw)

    monkeypatch.setattr(gw_mod, "affordability_cliff", spy)
    monkeypatch.setattr(gw_mod, "suggest_transfers", _fake_suggest)

    owned, market, xp = _cliff_market()
    wide = {pid: v * 5 for pid, v in xp.items()}            # the same players over a longer window
    gw_mod.gameweek_plan(owned, market, [], xp, bank=0.0, horizon_xp=wide)

    assert seen["xp"] is wide, ("the cliff must be priced over the WIDE window — measured on the page's "
                               "one-gameweek horizon it can never clear the threshold")

    # …and with no wider window supplied it falls back rather than failing.
    seen.clear()
    gw_mod.gameweek_plan(owned, market, [], xp, bank=0.0)
    assert seen["xp"] is xp, "no wide window → use what there is, never None"


def test_the_cliffs_span_is_named_because_it_differs_from_the_line_above_it():
    """The headline transfer is priced over the page's horizon; the cliff over the wider one. Unlabelled,
    two numbers on adjacent lines would look like the same yardstick — which is how a reader concludes the
    app contradicts itself."""
    from src.ui.gameweek import render_gameweek_plan

    plan = {"captain": None,
            "lineup": {"start": [], "bench": [], "bring_in": [], "drop": [], "has_declared_bench": False},
            "transfer": {"out": {"web_name": "Weak", "team": "T9"},
                         "in": {"web_name": "Cheap", "team": "TA"}, "gain": 1.7},
            "flags": [], "timing": {"action": "use"}, "horizon_gain": None, "horizon_gw": 5,
            "cliff": {"extra": 1.5, "gain": 13.8, "uplift": 6.4,
                      "move": {"out": {"web_name": "Weak", "team": "T9"},
                               "in": {"web_name": "Dear", "team": "TB"}},
                      "best_now": None, "gain_now": 7.4}}
    out = render_gameweek_plan(plan, "S", horizon=1)
    assert "+13.8 XI xP over 5 GWs" in out, out
    assert "next GW" in out, "and the headline still says its own, shorter window"
