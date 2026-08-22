"""Stat boards show an early-season note instead of a blank table (2026-08-22).

At the GW1 season rollover FPL resets the season-to-date stats, so the over/under · DefCon · clean-sheet · xG
boards are legitimately empty until games accrue. They now show a "fills in as games are played" note (and no
empty dataframe) rather than a confusing blank grid.
"""

from streamlit.testing.v1 import AppTest

_SCRIPT = """
from src.web_streamlit.views.players import render_over_under
sel = {"teams": set(), "positions": set(), "players": set(), "max_price": None, "my_squad": None}
render_over_under([], sel, {})           # no players → the analytics board is empty
"""


def test_empty_stat_board_shows_an_early_season_note_not_a_blank_table():
    at = AppTest.from_string(_SCRIPT, default_timeout=30).run()
    assert not at.exception
    assert any("Early season" in (e.value or "") for e in at.info)   # the helpful note
    assert not at.dataframe                                          # and no empty grid rendered
