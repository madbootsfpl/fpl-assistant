"""Each suggested transfer carries its own reasons (ADR-327).

🔴 **The bug, as a tester met it:** four transfer cards whose headlines differed — *M.Sangaré → Belloumi*,
*Egan → Vuskovic*, *Kinsky → Tzolakis*, *Konsa → Schuster* — and whose bodies were **identical**, down to
*"Selling M.Sangaré (2.4 xP)"* on the card that sells Konsa, and *"+3.3 to your starting XI"* on the card
whose own headline says +1.8.

⭐⭐ `explain_transfer` was never wrong. It was called once, for the plan's primary move, and the client
painted that one answer onto every card — *nothing was wrong except how many times the answer was used*,
which is why no test of the explainer itself could have caught it.
"""

from src.analytics.explain import explain_gameweek


def _move(out_id, out_name, out_xp, in_id, in_name, in_xp, gain):
    return {"out": {"id": out_id, "web_name": out_name, "xp": out_xp, "price": 5.0},
            "in": {"id": in_id, "web_name": in_name, "xp": in_xp, "price": 4.5}, "gain": gain}


def _plan():
    moves = [_move(1, "M.Sangaré", 2.4, 11, "Belloumi", 6.5, 3.3),
             _move(2, "Egan", 2.0, 12, "Vuskovic", 6.0, 3.5),
             _move(3, "Kinsky", 3.0, 13, "Tzolakis", 4.8, 1.7),
             _move(4, "Konsa", 3.1, 14, "Schuster", 5.0, 1.8)]
    return {"transfer": moves[0], "transfers": moves, "captain": None, "lineup": {}, "flags": []}


def _players():
    return {i: {"id": i, "web_name": n, "form": 1.0, "status": "a", "selected_by_percent": 5.0}
            for i, n in ((11, "Belloumi"), (12, "Vuskovic"), (13, "Tzolakis"), (14, "Schuster"))}


def test_one_explanation_per_move_keyed_by_the_buy():
    found = explain_gameweek(_plan(), _players(), {}, horizon=1)
    per_move = found["transfers"]
    assert sorted(per_move) == ["11", "12", "13", "14"], "a move went unexplained"


def test_no_two_moves_share_a_body():
    """⚠️ **The assertion the screenshot demands.** Four cards, four different sets of reasons — and the
    old behaviour produced four *identical* ones, so comparing them is the whole test."""
    found = explain_gameweek(_plan(), _players(), {}, horizon=1)
    bodies = [tuple(ex.reasons) + tuple(ex.risks) for ex in found["transfers"].values()]
    assert len(set(bodies)) == len(bodies), (
        "two moves carry the same reasons — the plan's primary explanation is being reused"
    )


def test_each_move_names_the_player_it_actually_sells():
    """🔴 The visible tell: *"Selling M.Sangaré"* appeared on the card selling Konsa."""
    found = explain_gameweek(_plan(), _players(), {}, horizon=1)
    for buy_id, sold in (("11", "M.Sangaré"), ("12", "Egan"), ("13", "Kinsky"), ("14", "Konsa")):
        risks = " ".join(found["transfers"][buy_id].risks)
        assert f"Selling {sold}" in risks, f"the move buying {buy_id} does not say it sells {sold}"


def test_each_move_states_its_own_gain():
    """⚠️ Every headline carried its own `+x.x xP` while every body claimed the first move's."""
    found = explain_gameweek(_plan(), _players(), {}, horizon=1)
    for buy_id, gain in (("11", "+3.3"), ("12", "+3.5"), ("13", "+1.7"), ("14", "+1.8")):
        assert any(gain in r for r in found["transfers"][buy_id].reasons), \
            f"the move buying {buy_id} does not state {gain}"


def test_the_primary_explanation_is_still_there():
    """⭐ `transfer` stays: the web app and the ask layer read it, and this fix adds a shape rather than
    replacing one."""
    found = explain_gameweek(_plan(), _players(), {}, horizon=1)
    assert found["transfer"] is not None
    assert found["transfer"].reasons == found["transfers"]["11"].reasons
