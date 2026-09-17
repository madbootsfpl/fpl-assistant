"""A near-tie breaks toward the longer view, and the band is sized for its window (ADR-209).

Owner: *"I would suspect that is a better option than Fée to Hall."* He was right, and the app had the number
that said so — it prints *"Longer view: −1.5 XI xP"* beside a move it chose over one worth **+3.1**, because
the two **tied on the number it ranks by** (+1.2 each next GW).

📊 Measured across 96 realistic squads: the gap between the best and second-best next-GW move has a **median
of 0.20** against a per-player weekly sd of 3.51. ⭐⭐ **ON A ONE-GAMEWEEK WINDOW THE RANKING WAS NEVER
RANKING — IT WAS PICKING**, and the old band (2.0, whatever the window) caught **100%** of those pairs, so the
correlation rule had silently been deciding every one-gameweek recommendation.
"""

import pytest

from src.analytics.transfer import TIE_NOISE, suggest_transfers, tie_noise


def _p(pid, pos="MID", price=6.0, team="ARS", name=None):
    return {"id": pid, "web_name": name or f"P{pid}", "position": pos, "team": team,
            "price": price, "status": "a", "chance": None, "total_points": 20,
            "points_per_game": 4.0, "minutes": 360, "selected_by": 5.0, "code": pid,
            "transfers_in_event": 0, "transfers_out_event": 0, "team_id": pid}


def _squad():
    out = [_p(1, "GK", 4.5, "BUR"), _p(2, "GK", 4.0, "BRE")]
    out += [_p(10 + i, "DEF", 4.5, t) for i, t in enumerate(("WOL", "LUT", "SHU", "NOR", "IPS"))]
    out += [_p(20 + i, "MID", 5.5, t) for i, t in enumerate(("EVE", "FUL", "CRY", "BHA", "NEW"))]
    out += [_p(30 + i, "FWD", 6.0, t) for i, t in enumerate(("LEE", "CHE", "MCI"))]
    return out


# --- the band ------------------------------------------------------------------------

def test_the_band_is_sized_for_the_window_it_is_given():
    """⚠️ **`TIE_NOISE` was a five-gameweek band applied to every window.** My Squad narrows the horizon
    toward the deadline, so it was being handed a one-gameweek map with a band five times too wide — able to
    overturn a real difference rather than break a tie.

    ⭐ *This is the mistake the codebase already warns about three functions away* (ADR-186: a threshold sized
    against one window applied to another). A lesson recorded about one number does not check the others.
    """
    assert tie_noise(5) == TIE_NOISE, "unchanged at the window it was sized for — no caller moves"
    assert tie_noise(1) == pytest.approx(TIE_NOISE / 5 ** 0.5, rel=1e-6)
    assert tie_noise(1) < tie_noise(3) < tie_noise(5), "a wider window tolerates a wider gap"
    assert tie_noise(0) == tie_noise(1) and tie_noise(None) == tie_noise(1), "never divide by nothing"


def test_the_band_scales_with_the_square_root_not_the_window():
    """⭐ The error in an N-gameweek total grows as **√N** if weekly errors are roughly independent, so a band
    that stays the same *fraction of the noise* scales the same way. Linear scaling would give 0.40 at one
    gameweek — under half the right size, and it would stop the tie-break speaking where it matters most."""
    assert tie_noise(1) == pytest.approx(0.894, abs=0.01)
    assert tie_noise(1) != pytest.approx(TIE_NOISE / 5, abs=0.01), "not the naive linear scaling"


# --- the tie-break -------------------------------------------------------------------

def _two_candidates():
    """Two incoming midfielders a whisker apart next GW, a chasm apart over five."""
    squad = _squad()
    near = _p(90, "MID", 6.0, "LIV", "NearTerm")     # better this week, worse later
    far = _p(91, "MID", 6.0, "TOT", "LongTerm")      # a whisker worse now, far better later
    x1 = {p["id"]: 2.0 for p in squad}
    x1.update({90: 5.0, 91: 4.8})
    x5 = {p["id"]: 10.0 for p in squad}
    x5.update({90: 10.5, 91: 20.0})
    return squad, [*squad, near, far], x1, x5


def test_a_near_tie_breaks_toward_the_longer_view():
    squad, market, x1, x5 = _two_candidates()
    got = suggest_transfers(squad, market, x1, bank=2.0, limit=1, window=1, horizon_xp=x5)
    assert got[0]["in"]["web_name"] == "LongTerm", (
        f"0.2 apart next GW is inside the 0.89 band; 9.5 apart over five is not: {got[0]['in']}")


def test_it_never_overrides_a_real_difference():
    """⭐ *A tie-break that can overturn a gap worth having is not a tie-break.* Widen the next-GW gap past
    the band and the longer view must lose, however large it is."""
    squad, market, x1, x5 = _two_candidates()
    x1[91] = 3.0                                     # now 2.0 behind — well outside the 0.89 band
    got = suggest_transfers(squad, market, x1, bank=2.0, limit=1, window=1, horizon_xp=x5)
    assert got[0]["in"]["web_name"] == "NearTerm"


def test_without_a_wider_map_nothing_changes():
    """⭐ 0.0 for everyone is a tie, so an absent map disables this cleanly and the sort falls straight
    through to the correlation rule that was there before."""
    squad, market, x1, _ = _two_candidates()
    got = suggest_transfers(squad, market, x1, bank=2.0, limit=1, window=1)
    assert got[0]["in"]["web_name"] == "NearTerm", "no wider map → the next-GW leader wins"


def test_the_longer_view_is_asked_before_the_correlation_rule():
    """⭐⭐ **A tie-break on expected points strictly dominates one on spread, so it must be asked first.**

    ADR-189 established that correlated defence *never moves expected points* — it widens that component's
    spread by √2, ~1.2 points at worst. The longer view moves expected points, by 4.6 in the case that
    prompted this. Here the correlation rule alone would take the uncorrelated defender; the longer view must
    win instead.
    """
    # ⚠️ **The squad must hold TWO from that club, not one.** A first version held one WOL defender, so the
    # tie-break could simply sell him and buy the other WOL — leaving zero correlation either way, and the
    # guard asserted a name rather than a mechanism. ⭐ *A fixture that lets the code sidestep the property
    # under test confirms nothing.*
    squad = [p for p in _squad() if p["id"] != 11]
    squad.append(_p(11, "DEF", 4.5, "WOL"))            # a second WOL defender
    corr = _p(92, "DEF", 5.0, "WOL", "Correlated")     # a third WOL asset — correlation dislikes him
    clean = _p(93, "DEF", 5.0, "AVL", "Uncorrelated")
    x1 = {p["id"]: 2.0 for p in squad}
    x1.update({92: 5.0, 93: 4.9})
    x5 = {p["id"]: 10.0 for p in squad}
    x5.update({92: 25.0, 93: 10.0})
    plain = suggest_transfers(squad, [*squad, corr, clean], x1, bank=2.0, limit=1, window=1)
    withwide = suggest_transfers(squad, [*squad, corr, clean], x1, bank=2.0, limit=1,
                                 window=1, horizon_xp=x5)
    assert plain[0]["in"]["web_name"] == "Uncorrelated", "correlation decides when nothing else can"
    assert withwide[0]["in"]["web_name"] == "Correlated", "…and the longer view outranks it"


# --- the wiring ----------------------------------------------------------------------

def test_the_plan_threads_the_window_and_the_wider_map(monkeypatch):
    """⭐ *An optional arg on a shared helper is a silent opt-out* (ADR-181). Every guard above passed while
    `gameweek_plan` passed neither, so the surface the owner reads kept a five-gameweek band on a one-week
    map and never let the longer view speak."""
    from src.analytics import gameweek as gw
    from src.analytics import transfer as tr

    seen = {}
    real = tr.suggest_transfers

    def spy(*a, **kw):
        seen.update({"window": kw.get("window"), "has_wide": kw.get("horizon_xp") is not None})
        return real(*a, **kw)

    monkeypatch.setattr(tr, "suggest_transfers", spy)
    monkeypatch.setattr(gw, "captain_picks", lambda *a, **k: [])
    squad = _squad()
    x1 = {p["id"]: 2.0 for p in squad}
    gw.gameweek_plan(squad, squad, [], x1, horizon=1, horizon_xp={p["id"]: 9.0 for p in squad})
    assert seen.get("window") == 1, f"the plan must tell the tie-break its window: {seen}"
    assert seen.get("has_wide") is True, f"…and hand it the wider map: {seen}"
