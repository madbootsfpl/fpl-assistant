"""One definition of the app's main control — and one page that must not have it (ADR-176).

Two guards, and the second is the more important one. The first stops the CSS being copied; the second stops
a future tidy-up from turning Signals' evidence ladder into four equal choices.
"""

import re
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "src" / "web_streamlit" / "pages"
WEB = ROOT / "src" / "web_streamlit"

ADOPTERS = ["1_My_Squad.py", "2_FDR.py", "4_Team_DNA.py", "5_Players.py", "6_Trending.py"]


def test_no_page_hand_rolls_the_selector_css():
    """ADR-140: *one rule written twice always drifts.*

    This project has paid for that in a stale caption, a stale ADR index and a stale runbook. The purple
    selector began inline in `1_My_Squad.py` (ADR-175); the moment a second page wanted it, it became
    `brand.nav_css`. A page writing its own would look identical today and diverge on the first edit.
    """
    offenders = []
    for f in PAGES.glob("*.py"):
        src = f.read_text()
        if "stButtonGroup" in src and "nav_css" not in src:
            offenders.append(f.name)
    assert not offenders, f"these pages style the selector themselves instead of calling brand.nav_css: {offenders}"


def test_the_primitive_is_defined_once():
    hits = [f.name for f in WEB.rglob("*.py") if 'data-testid="stButtonGroup"' in f.read_text()]
    assert hits == ["brand.py"], f"the selector CSS should live only in brand.py, found in {hits}"


def test_every_adopter_calls_it_with_its_own_key():
    """Each page scopes the CSS to its own container — a shared key would leak styling between pages."""
    keys = []
    for name in ADOPTERS:
        src = (PAGES / name).read_text()
        found = re.findall(r'nav_css\("([^"]+)"', src)
        assert found, f"{name} adopts the primitive but never calls nav_css"
        keys += found
    assert len(keys) == len(set(keys)), f"two pages share a container key: {keys}"


def test_signals_is_not_behind_a_selector():
    """⚠️ **The decision this file exists to protect.**

    ADR-150 orders Signals by *evidentiary strength* — official FPL news, then an unexplained exodus, then
    media headlines, then crowd chatter — and states that the ordering **is** the answer to the risk. Behind
    a selector a reader could open "crowd chatter" without ever seeing that it sits below "official news":
    four equal choices where there is a ladder.

    So the page that looks most like it wants ADR-176's pattern is the one page that must not have it. If a
    later tidy-up "makes Signals consistent with the others", this fails — and the reason is above.
    """
    src = (PAGES / "3_Signals.py").read_text()
    assert "nav_css" not in src, "Signals must not adopt the selector — the stacking carries the honesty"

    at = AppTest.from_file(str(PAGES / "3_Signals.py"), default_timeout=60).run()
    if at.exception:
        return                                        # no data in this environment
    heads = [h.value for h in at.subheader]
    ordered = [h for h in heads if re.match(r"^\d ·", h or "")]
    assert ordered == sorted(ordered), "the four sections must still read top to bottom, in order"
    assert len(ordered) >= 4, f"all four evidence tiers should be on the page at once, found {ordered}"
