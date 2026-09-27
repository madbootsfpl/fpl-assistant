"""The landing page's colours still match `brand.py` (ADR-312).

⚠️⚠️⚠️ **The surface with a generator did not drift; the surface without one did.** `brand.dart` is written
by a script and compared by a test, so the phone's palette has never disagreed with `brand.py`. Nothing did
that for `site/index.html` — and its `--ink` was **#0c0a12** against the brand's **#17131F**, while five of
its colours (`bg`, `panel`, `text`, `muted`, `green`, `yellow`) existed nowhere central at all.

⭐⭐ *A generator alone would not be enough, because nothing makes anyone run it.* This regenerates and
compares, so a palette change that has not reached the landing page fails the suite that gates a commit —
the same argument, and the same mechanism, as `test_brand_dart.py`.
"""

from __future__ import annotations

import importlib.util
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]


def generator():
    """`scripts/` is not a package, so load the real script from disk."""
    spec = importlib.util.spec_from_file_location(
        "gen_site", ROOT / "scripts" / "generate_site_palette.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_page_carries_exactly_what_the_generator_writes() -> None:
    gen = generator()
    page = gen.PAGE.read_text()

    assert gen.render(page) == page, (
        "site/index.html's brand colours are out of step with brand.py. Run\n"
        "    venv/bin/python scripts/generate_site_palette.py"
    )


def test_every_brand_colour_on_the_page_comes_from_brand_py() -> None:
    """⚠️ The block being *current* is not the same as it being *complete* — ⭐ *a variable that never
    entered the generated block cannot drift out of it*, which is exactly how five colours came to live
    only on this page."""
    gen = generator()
    from src.web_streamlit import brand

    for name, value in gen.VARIABLES.items():
        assert hasattr(brand, _const_for(name)), f"--{name} has no constant in brand.py"
        assert getattr(brand, _const_for(name)) == value


def _const_for(css_name: str) -> str:
    return {
        "purple-lt": "PURPLE_LT", "bg": "DARK_BG", "panel": "DARK_PANEL",
        "text": "DARK_TEXT", "muted": "DARK_MUTED",
    }.get(css_name, css_name.upper())


def test_the_ink_that_drifted_is_the_brands_ink() -> None:
    """⭐ The specific regression, named — *a guard for a class of bug still wants the instance in it*."""
    from src.web_streamlit import brand

    page = (ROOT / "site" / "index.html").read_text()
    ink = re.search(r"--ink:(#[0-9a-fA-F]{6})", page)

    assert ink and ink.group(1).lower() == brand.INK.lower(), (
        f"the page's ink is {ink and ink.group(1)}, brand.py's is {brand.INK}"
    )


def test_the_structural_css_is_left_alone() -> None:
    """⚠️⚠️ **The generator owns the brand block and nothing else.** `--bg2`, `--line` and the font stacks
    are hand-written CSS — ⭐ *a generator that owns the whole file makes every edit a merge conflict with a
    script*, and the next person would simply stop running it."""
    page = (ROOT / "site" / "index.html").read_text()

    block = re.search(r"/\* brand: generated.*?/\* end brand \*/", page, re.S)
    assert block, "the generated block's markers are gone — a reader cannot see where it ends"
    for hand_written in ("--bg2:", "--line:", "--sans:"):
        assert hand_written not in block.group(0), f"{hand_written} was swallowed by the generated block"
        assert hand_written in page


def test_the_share_card_is_generated_from_the_brand() -> None:
    """⚠️⚠️ **The card a link shows was hand-made and drifted**: its wordmark was **upright** while every
    other typeset instance is italic, and with no generator nothing would ever have said so.

    ⭐ Not compared pixel-by-pixel — it is rendered by Chrome, and *a guard that fails on a browser update
    is a guard people delete.* This asserts the thing that actually drifted: that the setting comes from
    `brand.py` rather than from whatever was typed that day.
    """
    from PIL import Image

    script = (ROOT / "scripts" / "generate_og_image.py").read_text()
    for token in ("brand.WORDMARK_ITALIC", "brand.WORDMARK_WEIGHT", "brand.WORDMARK_TRACKING_EM",
                  "brand.MAD_ON_DARK", "brand.ORANGE", "brand.TAGLINE"):
        assert token in script, f"the share card does not take {token} from brand.py"

    card = Image.open(ROOT / "site" / "og-image.png")
    assert card.size == (1200, 630), f"the share card is {card.size}; the meta tags promise 1200x630"


def test_the_drawn_logo_keeps_its_own_lettering_on_the_card() -> None:
    """⭐ ADR-312 §4 in the one asset that shows both at once: the illustration letters the name **MAD
    BOOTS** and the typeset wordmark beside it reads **MADBOOTS**. ⚠️ *The exemption is only coherent if the
    art is actually still there* — a card that dropped it would satisfy the one-word rule by deleting the
    thing the rule was written around."""
    script = (ROOT / "scripts" / "generate_og_image.py").read_text()

    assert 'ART = ROOT / "site" / "favicon.png"' in script
    assert "LOGO_ART_EXEMPT" in script, "the exemption is not cited where it is exercised"
