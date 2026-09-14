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
    # ADR-173: a real move always carries `gain` (and `in`), and the plan reads both for the bank-or-use
    # verdict. The fake was under-specified — it modelled less than the real thing ever returns, so it passed
    # only while nobody looked at those keys.
    # ⚠️ ADR-191: the assembler now asks `suggest_transfer_plan` (a plan whose gains add) rather than
    # `suggest_transfers` (a menu of alternatives whose gains do not). Stubbing the old name left the REAL
    # planner running underneath, which is how these fakes failed — loudly, which is the good outcome.
    monkeypatch.setattr(gw, "suggest_transfer_plan",
                        lambda *a, **k: [{"out": {"id": 4}, "in": {"id": 9}, "gain": 2.0, "bank_after": 0.0}])
    monkeypatch.setattr(gw, "suggest_transfers", lambda *a, **k: [])

    plan = gw.gameweek_plan(owned, owned, [], xp, bench_ids=[3])           # declared bench = P3

    assert plan["captain"]["web_name"] == "A"
    # declared XI = {1,2,4}; optimal = {1,2,3} → bring in P3, drop P4
    assert {p["id"] for p in plan["lineup"]["bring_in"]} == {3}
    assert {p["id"] for p in plan["lineup"]["drop"]} == {4}
    assert plan["lineup"]["has_declared_bench"] is True
    assert plan["transfer"] == {"out": {"id": 4}, "in": {"id": 9}, "gain": 2.0, "bank_after": 0.0}
    # ADR-191 — `transfers` is the week's actual advice and `free` the assumption behind it. At one free
    # transfer they say exactly what `transfer` always said, which is the point: the default does not move.
    assert plan["transfers"] == [plan["transfer"]]
    assert plan["free"] == 1
    # only the unavailable/doubtful players are flagged, with the right reason (A, B are fine)
    assert {f["web_name"]: f["reason"] for f in plan["flags"]} == {"C": "doubtful", "D": "injured"}


def test_gameweek_plan_handles_no_captain_no_transfer_and_no_declared_bench(monkeypatch):
    owned = [_p(1, "A", "AAA"), _p(2, "B", "BBB")]
    monkeypatch.setattr(gw, "captain_picks", lambda *a, **k: [])           # nobody eligible
    monkeypatch.setattr(gw, "best_legal_xi", lambda o, s: {1, 2})
    monkeypatch.setattr(gw, "suggest_transfers", lambda *a, **k: [])
    monkeypatch.setattr(gw, "suggest_transfer_plan", lambda *a, **k: [])       # no positive-gain move

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
    monkeypatch.setattr(gw, "suggest_transfer_plan", lambda *a, **k: [])
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
    monkeypatch.setattr(gw, "suggest_transfer_plan", lambda *a, **k: [])
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
    monkeypatch.setattr(gw, "suggest_transfer_plan", lambda *a, **k: [])
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
    monkeypatch.setattr(gw, "suggest_transfer_plan", lambda *a, **k: [])
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
    monkeypatch.setattr(gw, "suggest_transfer_plan", lambda *a, **k: [])
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
    monkeypatch.setattr(gw, "suggest_transfer_plan", lambda *a, **k: [])
    monkeypatch.setattr(gw, "replace_dead", lambda *a, **k: [])
    plan = gw.gameweek_plan([], [], [], {}, bench_ids=[])
    assert plan["timing"]["action"] == "bank"          # nothing worth doing → hold it
    assert plan["horizon_gain"] is None


# ---- ADR-191: the week's answer spends the transfers the manager actually holds -----------------

def _legal15(prices=None):
    """A legal 15 (2 GK · 5 DEF · 5 MID · 3 FWD), ≤3 per club, so `best_xi_points` has a real shape to
    solve. Positions and clubs are what the transfer rules read; the ids double as xP keys below."""
    prices = prices or {}
    rows, pid = [], 1
    for pos, n in (("GK", 2), ("DEF", 5), ("MID", 5), ("FWD", 3)):
        for i in range(n):
            rows.append({"id": pid, "web_name": f"O{pid}", "position": pos,
                         "team": f"T{pid % 6}", "price": prices.get(pid, 5.0), "status": "a"})
            pid += 1
    return rows


def _market_upgrades():
    """Four buyable upgrades in different positions and clubs, so two moves can be made without the
    club cap or the position rules deciding the answer for us."""
    return [{"id": 100 + k, "web_name": f"M{100 + k}", "position": pos, "team": f"U{k}",
             "price": 5.0, "status": "a"}
            for k, pos in enumerate(("MID", "FWD", "DEF", "MID"))]


def _only_transfers(monkeypatch):
    """Stub the captain and the lineup so an ADR-191 test is about the transfer half and nothing else.
    Both are separately tested; leaving them live here would only mean feeding them full player rows."""
    monkeypatch.setattr(gw, "captain_picks", lambda *a, **k: [])
    monkeypatch.setattr(gw, "best_legal_xi", lambda o, s: set())


def test_two_free_transfers_get_two_moves_and_the_gains_actually_add(monkeypatch):
    """⚠️ **The claim the rendered total makes, pinned against a real XI computation.**

    The week's answer used to call `suggest_transfers(limit=2)` — two *disjoint alternatives*, each priced
    against the **same** squad and the **same** bank. Printing both and summing them would have promised a
    number no manager could get, because the second was never priced on what the first leaves.

    So the test is not "two moves appear". It is: **the sum of the stated gains equals the actual lift of
    making both moves**, computed independently by `best_xi_points`. If the assembler ever goes back to a
    menu, this fails.
    """
    _only_transfers(monkeypatch)
    from src.analytics.optimizer import best_xi_points

    owned = _legal15()
    market = owned + _market_upgrades()
    xp = {p["id"]: 2.0 for p in owned}
    xp.update({100: 9.0, 101: 9.0, 102: 9.0, 103: 9.0})     # four clear upgrades

    plan = gw.gameweek_plan(owned, market, [], xp, bank=0.0, free=2)

    assert len(plan["transfers"]) == 2, "two free transfers should buy two moves"
    assert plan["free"] == 2

    before = best_xi_points(owned, xp)
    after = list(owned)
    for m in plan["transfers"]:
        by_id = {p["id"]: p for p in market}
        after = [p for p in after if p["id"] != m["out"]["id"]] + [by_id[m["in"]["id"]]]
    stated = round(sum(m["gain"] for m in plan["transfers"]), 1)
    assert stated == round(best_xi_points(after, xp) - before, 1), \
        "the stated gains must sum to the real lift of making every move — a menu's would not"


def test_one_free_transfer_is_exactly_what_it_always_was(monkeypatch):
    """The default does not move. `free` is manager-entered and defaults to 1, so the overwhelmingly common
    case has to be byte-identical to the answer this surface has always given — otherwise a fix for the
    two-transfer manager is a regression for everyone else."""
    _only_transfers(monkeypatch)
    owned = _legal15()
    market = owned + _market_upgrades()
    xp = {p["id"]: 2.0 for p in owned}
    xp.update({100: 9.0, 101: 9.0, 102: 9.0, 103: 9.0})

    plan = gw.gameweek_plan(owned, market, [], xp, bank=0.0, free=1)
    assert plan["transfers"] == [plan["transfer"]]
    assert plan["free"] == 1
    text = render_gameweek_plan(plan, "S", horizon=5)
    # ⚠️ Checking for "then #2" alone was not enough: with the guard mutated the *total* line still rendered
    # ("Using all 1 free transfers"), which is noise at best and, on a squad with one move, a restatement
    # dressed as a plan. Assert the whole block is absent, not the part that was easiest to name.
    for leak in ("then #", "Using all", "priced after the one above it"):
        assert leak not in text, f"one transfer held must render no extra-move lines at all — found {leak!r}"


def test_the_second_move_is_priced_after_the_first_not_beside_it(monkeypatch):
    """⚠️ **The difference between a plan and a menu, as an assertion — and the fixture is the whole test.**

    A first attempt here used two equal upgrades in different positions and asserted the second gain was no
    larger than the first. **It passed while the code was mutated back to a menu**, because a menu sorts by
    gain descending and so satisfies that too, and because with equal upgrades in free positions the two
    answers genuinely coincide. ⭐ *A fixture that only exercises the lucky case will confirm a broken
    mechanism* — the mutation test caught it, the assertion never would have.

    So this fixture makes the two mechanisms **disagree**, using the thing a menu cannot model: **the bank
    threads**. Both upgrades cost £6.0m against £5.0m players with £1.0m in the bank, so each is affordable on
    its own — a menu, pricing both against the *original* bank, offers both. A plan spends the money on the
    first and finds the second unaffordable. One answer is reachable and the other is fiction.
    """
    _only_transfers(monkeypatch)
    owned = _legal15()
    ups = [{"id": 200 + k, "web_name": f"M{200 + k}", "position": "MID", "team": f"V{k}",
            "price": 6.0, "status": "a"} for k in range(2)]
    market = owned + ups
    xp = {p["id"]: 2.0 for p in owned}
    xp.update({200: 9.0, 201: 9.0})

    plan = gw.gameweek_plan(owned, market, [], xp, bank=1.0, free=2)

    # A menu would hand back both £6.0m buys, because it prices each against the untouched £1.0m bank.
    assert len(plan["transfers"]) == 1, (
        "the money was spent on the first move, so there is no second — a menu would offer one anyway: "
        f"{[(m['out']['web_name'], m['in']['web_name']) for m in plan['transfers']]}")
    # …and the one move it does advise is genuinely affordable.
    assert plan["transfers"][0]["bank_after"] >= 0.0


def test_the_plan_says_how_many_transfers_it_assumed(monkeypatch):
    """The count is entered by the manager and defaults to 1, so the advice rests on something that can be
    wrong. ⭐ A stated assumption gets corrected; a silent one gets believed — which is how the week's answer
    spent weeks advising a position its reader was not in."""
    _only_transfers(monkeypatch)
    owned = _legal15()
    market = owned + _market_upgrades()
    xp = {p["id"]: 2.0 for p in owned}
    xp.update({100: 9.0, 101: 9.0, 102: 9.0, 103: 9.0})

    text = render_gameweek_plan(gw.gameweek_plan(owned, market, [], xp, bank=0.0, free=2), "S", horizon=5)
    assert "Using all 2 free transfers" in text
    assert "each move priced after the one above it" in text, \
        "the total is only honest if it says the moves were priced in sequence"


def test_the_cliff_must_beat_the_second_transfer_to_be_shown(monkeypatch):
    """⚠️ **Two correct answers to competing questions, made to compete (ADR-186 + ADR-191).**

    *"Save £1.0m for a better player"* and *"use the second transfer you already hold"* were both computed and
    **neither was compared to the other** — the reader got whichever happened to render. On the owner's squad
    the app suggested saving for +3.3 while a transfer he already held was worth several times that.

    Shown when it wins, suppressed when it loses. Nothing else about the plan changes.
    """
    _only_transfers(monkeypatch)
    owned = _legal15()
    market = owned + _market_upgrades()
    xp = {p["id"]: 2.0 for p in owned}
    xp.update({100: 9.0, 101: 9.0, 102: 9.0, 103: 9.0})

    def cliff_worth(uplift):
        return lambda *a, **k: {"extra": 1.0, "uplift": uplift, "gain": 20.0,
                                "move": {"out": {"web_name": "X"}, "in": {"web_name": "Y"}}}

    second = gw.gameweek_plan(owned, market, [], xp, bank=0.0, free=2)["transfers"][1]["gain"]

    monkeypatch.setattr(gw, "affordability_cliff", cliff_worth(second + 1.0))
    assert gw.gameweek_plan(owned, market, [], xp, bank=0.0, free=2)["cliff"] is not None, \
        "a cliff worth more than the second transfer still deserves saying"

    monkeypatch.setattr(gw, "affordability_cliff", cliff_worth(second - 0.1))
    assert gw.gameweek_plan(owned, market, [], xp, bank=0.0, free=2)["cliff"] is None, \
        "don't tell someone to save up for less than the move they can already make"

    # …and with one transfer held there is no second move to compete, so the cliff stands as it always did.
    assert gw.gameweek_plan(owned, market, [], xp, bank=0.0, free=1)["cliff"] is not None
