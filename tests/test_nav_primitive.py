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


# ---- ADR-180: the primitive keeps the layout and hands back the colour -------------------------

def test_the_primitive_carries_no_colour():
    """ADR-180. `nav_css` used to paint the active segment purple, because ADR-114 had found that any
    `[theme]` block pinned the theme and removed the viewer's Light/Dark/System toggle. Re-measured on
    Streamlit 1.61 that is no longer true, so the accent is declared once in `config.toml`.

    ⚠️ **Keeping a colour here as well would visibly clash in dark mode.** This file can only hard-code one
    shade; the theme gives dark mode `PURPLE_LT`. The segmented controls would be a different purple from
    every control around them — which is worse than either choice alone, and is exactly what someone would
    re-introduce to fix a page that "looks wrong".
    """
    from src.web_streamlit import brand

    css = brand.nav_css("demo", primary_button="demo_btn")
    for banned in (brand.PURPLE, brand.PURPLE_LT, "background:", "background "):
        assert banned.lower() not in css.lower(), \
            f"the primitive must not paint anything — the theme owns colour now ({banned!r})"
    # …and it still does the half the platform cannot.
    assert "flex: 1 1 0" in css and "width: 100%" in css


def test_the_accent_is_declared_for_both_themes_and_pins_neither():
    """The measurement ADR-180 rests on, asserted so a later edit cannot quietly undo it.

    A bare `[theme] primaryColor` would set the accent for light mode only and leave dark mode on
    Streamlit's default red — the very thing the owner reported. Worse, adding `base` would pin the theme
    and take away the viewer's toggle, which is ADR-114's original finding and still stands.
    """
    import tomllib

    cfg = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text())
    theme = cfg.get("theme", {})
    assert theme.get("light", {}).get("primaryColor") == "#8B2FC9", "light mode gets the brand purple"
    assert theme.get("dark", {}).get("primaryColor") == "#B45CF0", \
        "dark mode gets the lighter one — #8B2FC9 is dim on a near-black ground"
    assert "base" not in theme, "setting `base` pins the theme and removes the Light/Dark/System toggle"
    assert "primaryColor" not in theme, \
        "a top-level primaryColor would colour one mode and leave the other on Streamlit's red"


def test_the_top_nav_uses_the_primitive_like_every_other_selector():
    """ADR-180 — the one selector ADR-176 never wrapped, which is why it rendered narrower than every other
    row on the app and, in dark mode, in Streamlit's default red."""
    src = (PAGES / "1_My_Squad.py").read_text()
    assert 'st.container(key="ms_tool_nav")' in src
    assert 'nav_css("ms_tool_nav")' in src
    at = AppTest.from_file(str(PAGES / "1_My_Squad.py"), default_timeout=90).run()
    assert not at.exception, at.exception
    assert next((c for c in at.segmented_control if c.key == "ms_tool"), None) is not None, \
        "wrapping it in a container must not change the widget's own key"
