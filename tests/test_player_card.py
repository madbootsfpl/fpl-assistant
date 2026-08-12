"""Tests for the rich player card renderer (ADR-084, US-342).

Pure HTML builder — no Streamlit — so the markup is inspectable directly (the pitch/captain-card pattern). Covers
the position-adaptive stat sets, escaping, fixtures/flags, the compact variant, and empty-safety.
"""

from src.web_streamlit import player_card

_FWD = {"web_name": "Haaland", "position": "FWD", "team": "MCI", "price": 15.5, "total_points": 239,
        "points_per_game": 6.8, "minutes": 2953, "goals_scored": 27, "assists": 8, "xg": 25.5, "xa": 2.67,
        "xgi": 28.17, "xgc": 38.6, "defcon_per90": 3.17, "cbi": 48, "ict_index": 302.3, "selected_by": 74.4,
        "penalties_order": 1, "status": "a"}
_DEF = {"web_name": "Gabriel", "position": "DEF", "team": "ARS", "price": 8.0, "total_points": 209,
        "points_per_game": 6.5, "minutes": 2750, "goals_scored": 3, "assists": 5, "xgc": 22.01,
        "defcon_per90": 9.07, "cbi": 239, "tackles": 38, "recoveries": 64, "selected_by": 26.5, "status": "a"}
_GK = {"web_name": "Raya", "position": "GK", "team": "ARS", "price": 6.0, "total_points": 162,
       "points_per_game": 4.4, "minutes": 3330, "xgc": 27.56, "cbi": 37, "recoveries": 304,
       "selected_by": 31.0, "status": "a"}


def _labels(player, **kw):
    return [lbl for lbl, _v in player_card._stat_rows(player, **kw)]


# --- position-adaptive stat rows ----------------------------------------------------

def test_forward_leads_on_attacking_stats():
    labels = _labels(_FWD)
    assert "Goals" in labels and "xG Involvement" in labels and "Expected Goals" in labels
    assert "Expected GC" not in labels                       # a striker's card isn't about goals conceded


def test_defender_leads_on_defensive_stats():
    labels = _labels(_DEF)
    assert "Expected GC" in labels and "DefCon / 90" in labels and "Clr + Blk + Int" in labels
    assert "Tackles" in labels


def test_keeper_has_no_attacking_stats():
    labels = _labels(_GK)
    assert "Expected GC" in labels and "Recoveries" in labels
    assert "Goals" not in labels and "Expected Goals" not in labels


def test_stat_rows_skip_missing_values():
    labels = _labels({"web_name": "New", "position": "MID", "price": 5.0, "total_points": 0})
    assert "FPL Points" in labels and "Goals" not in labels   # goals absent → row skipped (not a blank)


# --- the HTML ------------------------------------------------------------------------

def test_card_html_carries_identity_and_stats():
    h = player_card.player_card_html(_FWD, team_name="Man City")
    assert "Haaland" in h and "Man City" in h and "£15.5m" in h and "FWD" in h
    assert "239" in h and "Player Card" in h                 # a stat + the brand band


def test_card_band_says_last_season_not_a_hardcoded_year():
    # US-345: preseason the stats are last season's carryover — label it honestly, not "Season 24/25"
    h = player_card.player_card_html(_FWD, team_name="Man City")
    assert "Last season" in h and "24/25" not in h


def test_card_html_escapes_everything():
    evil = {**_FWD, "web_name": "<script>x</script>", "position": "FWD"}
    h = player_card.player_card_html(evil, team_name='"><img>')
    assert "<script>" not in h and "&lt;script&gt;" in h
    assert '"><img>' not in h.replace("&gt;", "")            # the team name is escaped too


def test_fixtures_and_projected_xp_chip():
    fx = [{"opp": "BOU", "home": True, "fdr": 3}, {"opp": "CRY", "home": False, "fdr": 3},
          {"opp": "COV", "home": True, "fdr": 2}]
    h = player_card.player_card_html(_FWD, team_name="Man City", fixtures=fx, projected_xp=6.4)
    assert "BOU (H)" in h and "CRY (A)" in h and "COV (H)" in h
    assert "#22a559" in h                                     # the FDR-2 (green) pill colour
    assert "◆ Proj. 6.4 xP" in h
    assert "👑" in h and "⚽ pens" in h                        # ownership tier + set-piece flag chips


def test_per_gameweek_row_shows_xp_over_fixture():
    # US-367 (ADR-109): when fixtures carry an `xp`, the card renders a per-GW row (xP over the fixture, up to 3
    # gameweeks) — the tester's card-under-the-shirt layout. No Total column (owner steer — cleaner; the shirt chip
    # already shows the horizon total).
    fx = [{"opp": "HUL", "home": False, "fdr": 2, "xp": 5.1},
          {"opp": "IPS", "home": True, "fdr": 3, "xp": 6.2},
          {"opp": "EVE", "home": False, "fdr": 3, "xp": 4.5}]
    # card_body = the body WITHOUT the <style> block (which itself names .plc-gwrow), so the class is meaningful.
    h = player_card.card_body(_FWD, team_name="Man City", fixtures=fx, projected_xp=15.8)
    assert "plc-gwrow" in h                                    # the per-GW row (not the plain pills)
    assert "5.1" in h and "6.2" in h and "4.5" in h            # per-GW xP on top
    assert "HUL (A)" in h and "IPS (H)" in h and "EVE (A)" in h   # the fixture under each
    assert "plc-gwcol total" not in h and "Total" not in h    # no Total column (dropped)
    assert "◆ Proj." not in h                                  # the single Proj chip is suppressed by the row


def test_fixtures_without_xp_fall_back_to_pills():
    # US-367: backward-compatible — fixtures with no `xp` (e.g. the Players "Card" view) keep today's pills + chip.
    fx = [{"opp": "BOU", "home": True, "fdr": 3}]
    h = player_card.card_body(_FWD, fixtures=fx, projected_xp=6.4)
    assert "plc-gwrow" not in h and "plc-fix" in h and "◆ Proj. 6.4 xP" in h


def test_compact_drops_the_band_and_trims_stats():
    full = player_card.player_card_html(_FWD, team_name="Man City")
    compact = player_card.player_card_html(_FWD, team_name="Man City", compact=True)
    assert "Player Card" in full and "Player Card" not in compact      # no brand band when compact
    assert "compact" in compact and "Haaland" in compact
    assert len(_labels(_FWD, compact=True)) <= 4 < len(_labels(_FWD))  # trimmed stats so the popover fits (US-346)


def test_empty_safe():
    assert player_card.player_card_html(None) == ""
    assert player_card.player_card_html({}) == ""                      # no player fields → nothing
