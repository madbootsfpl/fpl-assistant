"""The public landing page (ADR-289).

⭐⭐ **This file is the reason the page is in the repo.** It lived only in `~/madboots-site`, so nothing
could look at it — and a broken explainer-video link sat on the live homepage until the owner happened to
click it. ⚠️ *A page no test can open is a page whose only reviewer is a visitor.*

These assert the things that have actually gone wrong, not everything that could.
"""

from __future__ import annotations

import re
import struct
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "site"
PAGE = (SITE / "index.html").read_text()


def test_every_referenced_file_exists() -> None:
    """⚠️ A missing asset is a broken page, and Cloudflare serves the index for it rather than a 404 —
    ⭐ *so the failure arrives looking like the homepage, which is how it hides* (ADR-282's lesson)."""
    referenced = {
        m for m in re.findall(r'(?:src|href)="([^"]+)"', PAGE)
        if not m.startswith(("http", "#", "mailto:", "data:", "/app/"))
    }

    assert referenced, "the page references no local files at all"
    for name in referenced:
        assert (SITE / name.lstrip("/")).exists(), f"{name} is referenced and not here"


def test_the_explainer_video_is_the_current_one() -> None:
    """⭐ The one that broke. The id appears twice — the iframe and a comment — and ⚠️ *two spellings of
    one value is how a guard silently stops guarding* (ADR-184)."""
    ids = set(re.findall(r'(?:youtu\.be/|youtube\.com/embed/)([A-Za-z0-9_-]{11})', PAGE))

    assert ids == {"Igt5mqheQpE"}, f"the page points at {ids or 'no video'}"


def test_the_hero_artwork_is_not_upscaled() -> None:
    """⚠️⚠️ **`width:100%` on a 377px image rendered it at 460px** — blurry, and 40% of a phone screen.

    ⭐ *An image told to fill its column will fill it whether or not it has the pixels to.*
    """
    rule = re.search(r'\.hero img\{([^}]*)\}', PAGE)
    assert rule, "the hero image rule is gone"

    assert "width:100%" not in rule[1], "the hero image is being upscaled again"
    assert "max-height" in rule[1], "nothing bounds the artwork against the viewport"


def test_the_artwork_is_bounded_by_the_screen_on_a_phone() -> None:
    """⭐ The owner's report: *"images look very big… could they be scaled to page fit depending on device
    size?"* — the cap has to be **relative**, or a taller phone gets a bigger picture of the same boots."""
    mobile = re.search(r'@media\(max-width:760px\)\{.*?\.hero img\{([^}]*)\}', PAGE, re.S)
    assert mobile, "the phone breakpoint no longer sizes the artwork"

    assert "vh" in mobile[1], "the phone cap is a fixed pixel count again"
    assert "vw" in mobile[1] or "%" in mobile[1]


def test_the_page_carries_no_inlined_images() -> None:
    """⚠️⚠️ **273KB of base64 used to live in this file**, downloaded before anything rendered and
    cacheable by nobody. ⭐ *An asset inside the document is an asset the browser cannot skip.*"""
    assert "data:image" not in PAGE
    assert len(PAGE) < 40_000, f"the page has grown to {len(PAGE) // 1024}KB — is something inlined?"


def test_the_artwork_declares_the_size_it_actually_is() -> None:
    """⭐ `width`/`height` reserve the space, so the page does not jump as the image arrives. ⚠️ *Numbers
    that disagree with the file reserve the wrong space*, which is worse than reserving none."""
    tag = re.search(r'<img[^>]*src="boots\.png"[^>]*>', PAGE)
    assert tag, "the hero image is no longer a file reference"

    declared = (int(re.search(r'width="(\d+)"', tag[0])[1]),
                int(re.search(r'height="(\d+)"', tag[0])[1]))
    raw = (SITE / "boots.png").read_bytes()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", raw[16:24]) == declared


def test_both_platform_buttons_go_somewhere_real() -> None:
    # ⚠️ Android points at the install page this repo also generates; iOS is text, not a dead button.
    assert 'href="/app/"' in PAGE, "the Android button is gone"
    # ⭐⭐ **Desktop is the web build now, not Streamlit** (ADR-305, on ADR-301). It is the same app in a
    # browser — same screens, same numbers — where the old link led to a different product that had
    # drifted three features behind. ⚠️ *A button labelled "use on desktop" that opens something else is
    # a button that teaches people the two are unrelated.*
    assert 'href="/app/web/"' in PAGE, "the desktop button is gone"
    assert "madboots.streamlit.app" not in PAGE, (
        "the landing page still sends desktop users to Streamlit"
    )
    assert "iOS — coming soon" in PAGE
    assert not re.search(r'<a[^>]*>[^<]*iOS[^<]*</a>', PAGE), (
        "iOS is a link again — a tap that does nothing reads as broken"
    )


def test_the_release_script_publishes_this_directory() -> None:
    """⭐ Otherwise the repo copy is a decoration and `$SITE` is still the original."""
    script = (SITE.parent / "scripts" / "release_android.sh").read_text()

    assert 'cp site/index.html site/*.png "$SITE/"' in script
