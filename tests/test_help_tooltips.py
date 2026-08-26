"""Coverage test for the ⓘ help tooltips (ADR-065).

Every **input control** (selectbox/multiselect/slider/number_input/text_input/checkbox/radio) on a web page
must carry a non-empty `help=` — that's the "all feature options have a tooltip" the tester asked for.
`st.tabs` labels and `st.chat_input` take no `help=` (captions cover them) and aren't checked; buttons are
actions, not options, so they're not strictly gated here.

US-208 covers the shared components + the browse pages; US-209 extends the list to the squad pages.
"""

import pathlib

from streamlit.testing.v1 import AppTest

_PAGES = pathlib.Path(__file__).resolve().parent.parent / "src" / "web_streamlit" / "pages"
_INPUTS = ("selectbox", "multiselect", "slider", "number_input", "text_input", "checkbox", "radio")

# Pages whose input controls must all carry help (US-208 browse + US-209 squad/decision pages).
# The consolidated pages default to their first view (Players→Pool, Squads→Build); those views' input
# controls all carry help. Manage-view widgets get their help when their view is selected (kept from
# Sprint 074; not re-checked here — the default-view check is the standing gate).
_COVERED = ["2_Players.py", "3_Team_DNA_and_FDR.py", "1_Squad_Lab.py", "8_Trending.py"]


def _inputs(at):
    widgets = []
    for attr in _INPUTS:
        widgets.extend(getattr(at, attr))
    return widgets


def _missing_help(page):
    at = AppTest.from_file(str(_PAGES / page), default_timeout=30).run()
    assert not at.exception, f"{page} raised: {at.exception}"
    return [(page, w.label) for w in _inputs(at) if not (w.help or "").strip()]


def test_browse_pages_input_controls_have_help():
    missing = [m for page in _COVERED for m in _missing_help(page)]
    assert not missing, f"input controls missing a help tooltip: {missing}"
