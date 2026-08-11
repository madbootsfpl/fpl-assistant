"""Tests for the MADBOOTS brand identity (ADR-103, US-348).

`web_streamlit/brand.py` is the single source of truth for the product's user-facing name/tagline/page-config; a
guard test pins that the old descriptive name ("FPL Assistant") is gone from the code. The internal `fpl-assistant`
package/repo + the `FPL_*` secrets are deliberately unchanged (ADR-103) — those aren't user-facing.
"""

import pathlib

from src.web_streamlit import brand

_SRC = pathlib.Path(__file__).resolve().parent.parent / "src"


def test_brand_constants():
    assert brand.NAME == "MADBOOTS"                       # one word — the wordmark is two-tone (MAD/BOOTS)
    assert brand.TAGLINE == "Fantasy Football, Calculated."


def test_page_config_titles_and_layout():
    assert brand.page_config("Players")["page_title"] == "Players · MADBOOTS"
    assert brand.page_config()["page_title"] == "MADBOOTS"        # Home (no page label)
    cfg = brand.page_config("Ask")
    assert cfg["layout"] == "wide" and cfg["page_icon"]          # the shared icon + wide layout


def test_badge_favicon_and_assets_exist():
    # US-349: page_icon is the badge asset (not an emoji); the badge files ship in the repo.
    icon = brand.page_config()["page_icon"]
    assert icon == brand.badge_path() and pathlib.Path(icon).is_file()
    assert brand.badge_data_uri().startswith("data:image/png;base64,")   # inline (card band), non-empty
    assert len(brand.badge_data_uri()) > 1000


def test_wordmark_is_two_tone_madboots():
    # US-349: the wordmark is one word, MAD purple · BOOTS orange, with an accessible whole-word label.
    w = brand.wordmark_html()
    assert 'aria-label="MADBOOTS"' in w                       # whole-word accessible text
    assert ">MAD<" in w and ">BOOTS<" in w                    # the two coloured halves (no literal space)
    assert brand.PURPLE in w and brand.ORANGE in w            # two-tone


def test_disclaimer_is_not_affiliated():
    # US-350 (ADR-103): a quiet not-affiliated line — the product is named, on official FPL data.
    d = brand.DISCLAIMER
    assert brand.NAME in d and "not affiliated" in d.lower() and "Premier League" in d


def test_no_stray_old_product_name_in_src():
    # US-348 (ADR-103): the visible product name is rebranded everywhere — no "FPL Assistant" left in code/templates.
    hits = [str(f.relative_to(_SRC))
            for f in list(_SRC.rglob("*.py")) + list(_SRC.rglob("*.html"))
            if "FPL Assistant" in f.read_text(encoding="utf-8")]
    assert not hits, f"stray 'FPL Assistant' still in: {hits}"
