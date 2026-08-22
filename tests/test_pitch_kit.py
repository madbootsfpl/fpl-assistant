"""The pitch draws the live club KIT, not a stale mugshot (ADR-084 revision, 2026-08-22).

A just-transferred player kept appearing on the pitch in his *prior* club's kit, because the pitch used the FPL
**mugshot** (`p{code}.png`) and FPL's photo CDN lags a transfer by weeks (the club **kit graphic** updates
instantly, like FPL's own pitch). Fix: the pitch image is `shirt_url_by_id` (the live club shirt, transfer-proof);
the **hover card keeps the mugshot** (a detail card — it self-heals when FPL refreshes the photo).
"""

from src.web_streamlit import pitch
from src.web_streamlit.badges import shirt_url_by_id

_TEAMS = [{"short_name": "LIV", "code": 14}, {"short_name": "ARS", "code": 3}]
# a real FPL shirt/photo URL shape (LIV outfield kit · Isak's mugshot code)
_LIV_KIT = "https://fantasy.premierleague.com/dist/img/shirts/standard/shirt_14-66.png"
_MUGSHOT = "https://resources.premierleague.com/premierleague/photos/players/110x140/p219168.png"


def _player(**over):
    """Isak, now at Liverpool — enough fields for `_kit_html` (crowd/set-piece flags + the card body)."""
    p = {"id": 100, "web_name": "Isak", "position": "FWD", "team": "LIV", "price": 10.5, "total_points": 204,
         "points_per_game": 5.9, "minutes": 2600, "goals_scored": 21, "assists": 6, "xg": 19.5, "xa": 3.1,
         "xgi": 22.6, "ict_index": 240.1, "selected_by": 31.0, "status": "a"}
    p.update(over)
    return p


# --- shirt_url_by_id -----------------------------------------------------------------

def test_shirt_url_by_id_maps_to_the_live_club_kit():
    out = shirt_url_by_id([_player(id=1, team="LIV", position="FWD"),
                           _player(id=2, team="ARS", position="GK")], _TEAMS)
    assert out[1].endswith("shirt_14-66.png")        # LIV outfield kit (club code 14)
    assert out[2].endswith("shirt_3_1-66.png")       # ARS keeper kit (the _1 GK variant, code 3)


def test_shirt_url_by_id_blank_when_the_team_code_is_missing():
    out = shirt_url_by_id([_player(id=9, team="ZZZ")], _TEAMS)   # unknown club → no code
    assert out[9] == ""                                          # → a 👕 placeholder on the pitch, no crash


# --- the pitch kit card --------------------------------------------------------------

def test_pitch_shows_the_club_kit_not_the_stale_mugshot():
    html = pitch._kit_html(_player(), captain_id=None, xp_by_id={100: 5.0},
                           photos={100: _MUGSHOT}, next_opp={}, kits={100: _LIV_KIT})
    assert f'<div class="pic"><img src="{_LIV_KIT}"' in html   # the on-pitch image is the live club kit
    assert "p219168.png" in html                               # …but the hover card keeps the mugshot (self-heals)


def test_pitch_kit_falls_back_to_the_photo_when_no_kits_map():
    # older callers/tests that don't pass `kits` keep the previous behaviour (kit = the photo)
    html = pitch._kit_html(_player(), captain_id=None, xp_by_id={100: 5.0},
                           photos={100: _MUGSHOT}, next_opp={})
    assert f'<div class="pic"><img src="{_MUGSHOT}"' in html
