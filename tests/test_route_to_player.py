"""*"What would it take to field X?"* — target-driven planning (ADR-207, ADR-191 §3).

The app asks a **squad-driven** question: *for each player I own, what is the best replacement?* The owner
kept asking a **target-driven** one, twice, unprompted:

> *"Is Haaland a better option than Bruno and figure the moves needed to select him."*  (2026-09-14)
> *"I would use my transfers to see if I can get another forward in that is scoring."*  (2026-09-17)

⭐ **The inversion is the feature.** `suggest_transfers` iterates the **outgoing** players, so a named
incoming player can only be reached by luck. Here the incoming player is fixed and the **route** is searched.
"""

from src.analytics.transfer import route_to_player


def _p(pid, pos="FWD", price=7.0, team="ARS", name=None):
    return {"id": pid, "web_name": name or f"P{pid}", "position": pos, "team": team,
            "price": price, "status": "a", "chance": None}


def _squad():
    """A legal 15 — 2 GK, 5 DEF, 5 MID, 3 FWD — with three forwards at different prices."""
    out = [_p(1, "GK", 4.5, "BUR"), _p(2, "GK", 4.0, "BRE")]
    out += [_p(10 + i, "DEF", 4.5, t) for i, t in enumerate(("WOL", "LUT", "SHU", "NOR", "IPS"))]
    out += [_p(20 + i, "MID", 5.5, t) for i, t in enumerate(("EVE", "FUL", "CRY", "BHA", "NEW"))]
    out += [_p(30, "FWD", 6.0, "LEE", "Cheap"), _p(31, "FWD", 8.0, "CHE", "Mid"),
            _p(32, "FWD", 11.0, "MCI", "Premium")]
    return out


def _xp(**over):
    base = {p["id"]: 3.0 for p in _squad()}
    base.update({30: 2.0, 31: 6.0, 32: 9.0})
    base.update(over)
    return base


# --- the inversion -------------------------------------------------------------------

def test_it_finds_every_route_to_a_named_player_not_just_one():
    """`suggest_transfers` returns one best move per outgoing player and stops. This must enumerate the
    whole choice, because *which* sale is the decision the reader is making."""
    target = _p(99, "FWD", 9.0, "LIV", "Target")
    res = route_to_player(target, _squad(), {**_xp(), 99: 12.0}, bank=1.5)
    sold = {r["out"]["web_name"] for r in res["routes"]}
    assert sold == {"Mid", "Premium"}, sold          # Cheap (6.0 + 1.5) cannot afford 9.0
    assert res["routes"][0]["out"]["web_name"] == "Mid", "the best route must lead, not the cheapest sale"


def test_the_best_route_is_the_one_that_helps_the_XI_not_the_one_that_frees_most_money():
    """⭐ The failure ADR-191 §2 measured from the other direction: on a real squad the best pair routed
    *the same incoming player through a different sale*. Selling your best player always affords the target;
    that is not the same as it being the right route."""
    target = _p(99, "FWD", 11.0, "LIV", "Target")
    res = route_to_player(target, _squad(), {**_xp(), 99: 12.0}, bank=5.0)
    assert [r["out"]["web_name"] for r in res["routes"]][0] == "Cheap", (
        "selling the 2.0-xP forward must beat selling the 9.0-xP one, though both afford him")


def test_a_blocked_route_is_reported_with_what_it_is_short_by():
    """⭐ *A blocked route is information, not an absence.* "Sell him and you are £0.6m short" is exactly
    ADR-186's *worth saving for*; printing only what cleared tells the reader about one option and hides the
    near-misses."""
    target = _p(99, "FWD", 9.0, "LIV", "Target")
    res = route_to_player(target, _squad(), {**_xp(), 99: 12.0}, bank=1.5)
    blocked = {b["out"]["web_name"]: b["short_by"] for b in res["blocked"]}
    assert blocked == {"Cheap": 1.5}
    assert res["shortfall"] == 1.5


def test_negative_routes_are_returned_least_bad_first_not_suppressed():
    """⭐ **A target-driven question is one the reader has already half-answered.** The job is to *price* the
    wish, not to grant or refuse it — so a route that costs points is still a route, and the reader decides.
    Suppressing them would answer a question nobody asked ("is this wise?") instead of the one they did."""
    target = _p(99, "FWD", 5.0, "LIV", "Weak")
    res = route_to_player(target, _squad(), {**_xp(), 99: 0.5}, bank=0.0)
    assert res["routes"], "a route that loses points is still a route"
    gains = [r["gain"] for r in res["routes"]]
    assert all(g <= 0 for g in gains) and gains == sorted(gains, reverse=True), gains


def test_owning_him_already_is_said_plainly():
    res = route_to_player(_p(31, "FWD", 8.0, "CHE", "Mid"), _squad(), _xp())
    assert res["owned"] is True and res["routes"] == []


def test_the_club_limit_is_checked_after_the_swap_not_before():
    """⚠️ Selling a clubmate of the target **frees a slot**, so the 3-per-club rule is not a property of the
    squad as it stands. Checking it before the swap would refuse a legal transfer."""
    squad = _squad()
    for pid in (10, 11, 12):                       # three defenders from one club
        squad[[p["id"] for p in squad].index(pid)]["team"] = "LIV"
    target = _p(99, "DEF", 5.0, "LIV", "FourthRed")
    res = route_to_player(target, squad, {**{p["id"]: 3.0 for p in squad}, 99: 4.0}, bank=1.0)
    sold = {r["out"]["web_name"] for r in res["routes"]}
    assert {"P10", "P11", "P12"} <= sold, "selling a clubmate must open the slot"
    assert "P13" not in sold, "selling a non-clubmate would make it four from one club"


def test_only_the_same_position_can_be_sold():
    """FPL transfers are one-for-one and same-position, so a midfielder cannot fund a forward."""
    target = _p(99, "FWD", 5.0, "LIV", "Target")
    res = route_to_player(target, _squad(), {**_xp(), 99: 8.0}, bank=10.0)
    assert all(r["out"]["position"] == "FWD" for r in res["routes"])
    assert all(b["out"]["position"] == "FWD" for b in res["blocked"])


def test_a_player_reported_to_be_leaving_is_valued_at_zero_when_ranking_routes():
    """ADR-153/156 — selling a leaver should look attractive, and it only does if the ranking stops crediting
    him with points he will never score."""
    target = _p(99, "FWD", 9.0, "LIV", "Target")
    xp = {**_xp(), 99: 12.0}
    plain = route_to_player(target, _squad(), xp, bank=1.5)
    leaving = route_to_player(target, _squad(), xp, bank=1.5, reported_out={32: 5})
    best_plain = plain["routes"][0]["out"]["web_name"]
    best_leaving = leaving["routes"][0]["out"]["web_name"]
    assert best_plain == "Mid" and best_leaving == "Premium", (
        f"the leaver should become the route to take: {best_plain} -> {best_leaving}")


# --- the wiring ----------------------------------------------------------------------

def test_the_cli_route_command_answers_for_a_saved_squad(capsys, monkeypatch, tmp_path):
    """⭐ **Testing a component is not testing that anything uses it.** Every guard above passed while
    `route_to_player` had no caller at all — a perfectly-tested function nobody can reach is a private note.
    """
    from src import config
    from src.cli import main
    from src.squads import SquadStore
    from src.storage import Storage

    monkeypatch.setattr(config, "SQUADS_PATH", str(tmp_path / "squads.json"))
    db = Storage()
    try:
        players = db.get_players()
        if not players:
            import pytest
            pytest.skip("no cached players — run `refresh`")
        fwds = sorted((p for p in players if p["position"] == "FWD" and p["status"] == "a"),
                      key=lambda p: -(p["price"] or 0))
        target, owned_fwds = fwds[0], fwds[1:4]
        squad = owned_fwds + [p for p in players if p["position"] != "FWD"][:12]
    finally:
        db.close()

    SquadStore(str(tmp_path / "squads.json")).save(
        "T", [p["id"] for p in squad], [p["web_name"] for p in squad])
    monkeypatch.setattr("src.cli.SquadStore", lambda *a, **k: SquadStore(str(tmp_path / "squads.json")))

    main(["route", target["web_name"], "--squad", "T", "--next", "1"])
    out = capsys.readouterr().out
    assert "What would it take to field" in out and target["web_name"] in out
    assert ("sell" in out or "short by" in out or "No legal route" in out), out


def test_an_unknown_player_name_is_refused_rather_than_guessed(capsys, monkeypatch, tmp_path):
    from src import config
    from src.cli import main
    from src.squads import SquadStore

    monkeypatch.setattr(config, "SQUADS_PATH", str(tmp_path / "squads.json"))
    store = SquadStore(str(tmp_path / "squads.json"))
    store.save("T", [1, 2, 3], ["a", "b", "c"])
    monkeypatch.setattr("src.cli.SquadStore", lambda *a, **k: store)
    main(["route", "Definitely Nobody", "--squad", "T"])
    assert "No player matching" in capsys.readouterr().out
