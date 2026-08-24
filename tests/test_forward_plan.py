"""Tests for the forward planner (ADR-131).

The design was decided by a prototype, not a spec: six gameweeks of a real squad sat inside ±3% on projected
points while hard-fixture counts swung 2→7. So the planner leads with **exposure**, and — the part these
mostly pin — it says plainly when nothing stands out rather than naming a worst-of-six out of noise.
"""

from src.analytics.forward_plan import forward_plan, week_rows

IDS = {"AAA": 1, "BBB": 2, "CCC": 3, "DDD": 4}


def _fx(event, home, away, hd=3, ad=3, i=0):
    return {"event": event, "team_h": IDS[home], "team_a": IDS[away], "home": home, "away": away,
            "team_h_difficulty": hd, "team_a_difficulty": ad,
            "kickoff_time": f"2026-09-{event:02d}T12:0{i}:00Z"}


def _p(pid, team, name=None):
    return {"id": pid, "team": team, "web_name": name or f"p{pid}", "position": "MID"}


# ---- exposure ----------------------------------------------------------------------

def test_a_blank_gameweek_is_counted_and_named():
    owned = [_p(1, "AAA", "Blanker"), _p(2, "BBB")]
    up = [_fx(2, "AAA", "BBB"), _fx(3, "BBB", "CCC")]          # AAA has no GW3 fixture
    weeks = week_rows(owned, up, horizon=2)
    assert weeks[1]["blank"] == ["Blanker"] and weeks[0]["blank"] == []


def test_a_double_gameweek_is_counted_and_named():
    owned = [_p(1, "AAA", "Doubler")]
    up = [_fx(3, "AAA", "CCC", i=1), _fx(3, "DDD", "AAA", i=2)]
    assert week_rows(owned, up, horizon=1)[0]["double"] == ["Doubler"]


def test_a_double_is_judged_hard_by_its_worse_half():
    """A double is only as easy as its harder match — the same rule the ticker shades by."""
    owned = [_p(1, "AAA")]
    up = [_fx(3, "AAA", "CCC", hd=2, i=1), _fx(3, "DDD", "AAA", ad=5, i=2)]
    assert week_rows(owned, up, horizon=1)[0]["hard"] == ["p1"]


def test_only_difficulty_four_and_above_counts_as_hard():
    owned = [_p(1, "AAA")]
    assert week_rows(owned, [_fx(2, "AAA", "BBB", hd=3)], horizon=1)[0]["hard"] == []
    assert week_rows(owned, [_fx(2, "AAA", "BBB", hd=4)], horizon=1)[0]["hard"] == ["p1"]


# ---- the headline is honest ---------------------------------------------------------

def _even_fixtures(events, diff=3):
    return [_fx(e, "AAA", "BBB", hd=diff, ad=diff) for e in events]


def test_an_even_run_says_so_rather_than_naming_a_worst_week():
    """The whole point. A planner that always names a problem week teaches its reader to distrust it."""
    owned = [_p(i, "AAA") for i in range(1, 6)]
    plan = forward_plan(owned, _even_fixtures(range(2, 8)), horizon=6)
    assert "No standout week" in plan["headline"]
    assert all(w["flag"] is None for w in plan["weeks"])


def test_a_blank_outranks_everything_in_the_headline():
    """A blanked player scores nothing at all — it changes a week in kind, not by degree."""
    owned = [_p(1, "AAA", "Blanker"), _p(2, "BBB")]
    up = _even_fixtures([2, 4], diff=5) + [_fx(3, "BBB", "CCC")]
    plan = forward_plan(owned, up, horizon=3)
    assert "blank" in plan["headline"] and "GW3" in plan["headline"]


def test_a_double_is_named_when_there_is_no_blank():
    owned = [_p(1, "AAA", "Doubler")]
    up = [_fx(2, "AAA", "BBB"), _fx(3, "AAA", "CCC", i=1), _fx(3, "DDD", "AAA", i=2)]
    plan = forward_plan(owned, up, horizon=2)
    assert "double" in plan["headline"] and "GW3" in plan["headline"]


def test_a_tough_week_is_only_flagged_when_it_clears_the_median():
    """A fifteen-man squad's exposure wobbles by a player or two every week; that isn't a problem week."""
    owned = [_p(i, "AAA") for i in range(1, 6)] + [_p(9, "CCC")]
    # AAA is hard in GW4 only; every other week is ordinary.
    up = [_fx(2, "AAA", "BBB"), _fx(3, "AAA", "BBB"), _fx(4, "AAA", "BBB", hd=5),
          _fx(5, "AAA", "BBB"), _fx(2, "CCC", "DDD"), _fx(3, "CCC", "DDD"),
          _fx(4, "CCC", "DDD"), _fx(5, "CCC", "DDD")]
    plan = forward_plan(owned, up, horizon=4)
    flagged = [w["event"] for w in plan["weeks"] if w["flag"] == "hard"]
    assert flagged == [4] and "GW4" in plan["headline"]


# ---- the xP line --------------------------------------------------------------------

def test_a_barely_moving_projection_is_reported_as_flat():
    """So a reader doesn't take a 3% wobble for a forecast."""
    owned = [_p(1, "AAA")]
    up = _even_fixtures([2, 3, 4])
    bg = {1: {2: 5.0, 3: 5.1, 4: 4.9}}
    assert forward_plan(owned, up, bg, horizon=3)["xp"]["flat"] is True


def test_a_genuinely_varying_projection_is_not_flat():
    owned = [_p(1, "AAA")]
    bg = {1: {2: 2.0, 3: 9.0, 4: 5.0}}
    assert forward_plan(owned, _even_fixtures([2, 3, 4]), bg, horizon=3)["xp"]["flat"] is False


def test_no_fixtures_is_empty_safe():
    plan = forward_plan([_p(1, "AAA")], [], horizon=6)
    assert plan["weeks"] == [] and plan["xp"] is None
