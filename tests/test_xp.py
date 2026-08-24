"""Tests for the Expected Points (xP) analytics — the cross-domain join."""

from src.analytics.xp import player_xp
from src.ui.xp import render_xp_table


def player(team_id=1, ppg=5.0, status="a", ep_next=4.0, web_name="P",
           position="MID", team="ARS", id=1, minutes=900):
    # `minutes` defaults to the 900-minute evidence bar so a no-history player's rate *is* their ppg
    # (ADR-124's full-evidence end). Cold-start tests below pass fewer minutes on purpose.
    return {
        "id": id,
        "team_id": team_id,
        "points_per_game": ppg,
        "status": status,
        "ep_next": ep_next,
        "web_name": web_name,
        "position": position,
        "team": team,
        "minutes": minutes,
    }


def upcoming(team_h=1, team_a=2, home="ARS", away="BUR", h_diff=2, a_diff=5,
             event=1, home_team_strength=None, away_team_strength=None):
    return {
        "event": event,
        "team_h": team_h,
        "team_a": team_a,
        "home": home,
        "away": away,
        "team_h_difficulty": h_diff,
        "team_a_difficulty": a_diff,
        "home_team_strength": home_team_strength,
        "away_team_strength": away_team_strength,
    }


def test_xp_applies_the_fixture_multiplier():
    # ARS (team 1) home, difficulty 2 → ×1.1; ppg 5.0 → xP 5.5.
    result = player_xp([player(ppg=5.0)], [upcoming(h_diff=2)], source="fpl")
    assert result[0]["xp"] == 5.5


def test_xp_is_zero_when_unavailable():
    result = player_xp([player(status="i")], [upcoming(h_diff=2)])
    assert result[0]["xp"] == 0.0


def test_minutes_weight_scales_xp_when_passed():
    # xMins v0 hook (ADR-038): half the expected minutes → half the xP (and per-GW).
    result = player_xp(
        [player(ppg=5.0)], [upcoming(h_diff=2)], source="fpl",
        minutes_weight=lambda p: 0.5,
    )
    assert result[0]["xp"] == 2.8                        # 5.5 × 0.5 = 2.75, rounded for display
    assert result[0]["by_gameweek"][1] == 2.8
    assert result[0]["minutes_weight"] == 0.5


def test_xp_is_byte_identical_without_the_minutes_hook():
    # No hook → xP unchanged and the weight reads 1.0 (the raw `xp` view stays pure).
    result = player_xp([player(ppg=5.0)], [upcoming(h_diff=2)], source="fpl")
    assert result[0]["xp"] == 5.5
    assert result[0]["minutes_weight"] == 1.0


def test_cold_start_floors_a_no_history_player_with_ep_next():
    # ADR-104, now the zero-evidence end of the ADR-124 blend: a player who hasn't kicked a ball has no
    # points-per-game to average, so the rate is FPL's ep_next outright — don't project 0.
    result = player_xp([player(ppg=None, ep_next=4.0, minutes=0)], [upcoming(h_diff=2)])
    assert result[0]["xp"] == 4.4                         # 4.0 (ep_next) × the h_diff=2 multiplier (1.1)
    assert result[0]["rate_source"] == "cold_start"


def test_xp_is_zero_when_no_ppg_and_no_ep_next():
    # ADR-104: the floor only rescues when ep_next is present — no ppg AND no ep_next still → 0.
    result = player_xp([player(ppg=None, ep_next=0, minutes=0)], [upcoming(h_diff=2)])
    assert result[0]["xp"] == 0.0


def test_cold_start_floor_does_not_touch_a_player_with_a_baseline():
    # ADR-104: the ep_next floor is the last tier only — a trusted historical baseline is unchanged.
    result = player_xp([player(ppg=5.0, ep_next=99.0)], [upcoming(h_diff=2)],
                       baseline_by_code={None: 5.0})     # a baseline keyed by the fixture's code (None here)
    assert result[0]["rate_source"] == "hist" and result[0]["xp"] == 5.5   # ep_next 99 ignored


def test_xp_uses_the_next_fixture_only():
    # Team 1 has two upcoming fixtures; the first (diff 2) is used, not diff 5.
    fixtures = [upcoming(h_diff=2, event=1), upcoming(h_diff=5, event=2)]
    result = player_xp([player(ppg=5.0)], fixtures)
    assert result[0]["xp"] == 5.5


def test_xp_zero_when_team_has_no_fixture_in_horizon():
    # Player's team (99) plays no fixture in the window (a blank) → 0.
    result = player_xp([player(team_id=99, ppg=5.0)], [upcoming()])
    assert result[0]["xp"] == 0.0
    assert result[0]["games"] == 0


def test_xp_sums_over_the_horizon():
    # Team 1 plays GW1 (diff 3 → ×1.0) and GW2 (diff 3 → ×1.0); horizon 2 → 5.0×2 = 10.0.
    fixtures = [upcoming(h_diff=3, event=1), upcoming(h_diff=3, event=2)]
    result = player_xp([player(ppg=5.0)], fixtures, horizon=2)
    assert result[0]["xp"] == 10.0
    assert result[0]["games"] == 2


def test_xp_double_gameweek_counts_both_fixtures():
    # Team 1 (ARS) plays TWICE in GW1 — a double gameweek — so both count at horizon 1.
    fixtures = [
        upcoming(team_h=1, team_a=2, home="ARS", away="BUR", h_diff=3, event=1),
        upcoming(team_h=1, team_a=3, home="ARS", away="COV", h_diff=3, event=1),
    ]
    result = player_xp([player(ppg=5.0)], fixtures, horizon=1)
    assert result[0]["games"] == 2        # both GW1 fixtures counted
    assert result[0]["xp"] == 10.0        # 5.0 × (1.0 + 1.0)


def test_xp_sorted_highest_first():
    players = [player(ppg=3.0, web_name="Low"), player(ppg=6.0, web_name="High")]
    result = player_xp(players, [upcoming(h_diff=3)])   # neutral ×1.0
    assert result[0]["web_name"] == "High"


def test_xp_custom_source_uses_strength():
    # ARS home; custom difficulty = BUR's away strength (2) → ×1.1, not FPL's 4.
    fixtures = [upcoming(h_diff=4, a_diff=4, away_team_strength=2, home_team_strength=5)]
    result = player_xp([player(ppg=5.0)], fixtures, source="custom")
    assert result[0]["xp"] == 5.5


def _row(web_name="B.Fernandes", team="MUN", position="MID", xp=7.4, games=1,
         ep_next=4.0, difficulty=2):
    return {
        "web_name": web_name, "team": team, "position": position,
        "xp": xp, "games": games, "ep_next": ep_next, "difficulty": difficulty,
    }


def test_render_xp_table_empty():
    assert "run `refresh`" in render_xp_table([])


def test_render_xp_table_shows_xp_and_fpl_ep_at_horizon_1():
    out = render_xp_table([_row()], source="custom", horizon=1)

    assert "B.Fernandes" in out
    assert "7.4" in out          # our xP
    assert "4.0" in out          # FPL's ep_next (shown at horizon 1)
    assert "custom" in out       # source noted in the footer


def test_render_xp_table_handles_missing_ep():
    out = render_xp_table([_row(ep_next=None)], horizon=1)
    assert "—" in out            # None ep_next renders as a dash


def test_render_xp_table_hides_fpl_over_a_multi_gw_horizon():
    # ep_next is present, but at horizon > 1 it must be hidden (not comparable).
    out = render_xp_table([_row(games=5, ep_next=4.0)], horizon=5)

    assert "4.0" not in out            # FPL's next-GW number is not shown
    assert "not comparable" in out     # footer explains why
    assert "next 5 gameweeks" in out
