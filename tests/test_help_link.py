"""The app's Help link points at a page that exists (ADR-254).

⭐⭐ **Help goes out of the app; feedback stays in.** They look like one item and are two jobs. Help is
*content* — long, searchable, better on a big screen, and updatable without an App Store release.
Reporting happens the instant you notice something, and ⚠️ *every step between noticing and reporting
loses reports*, so that one keeps its two taps and the screen and build number it already sends for free.

⚠️⚠️ **A link into another app's routing is a promise nothing else keeps.** Streamlit derives its URLs
from filenames: `pages/7_Help.py` is served at `/Help`. Rename or renumber that file and the phone's link
404s — silently, in a browser, for a tester who concludes the app is broken. ⭐ *A cross-repo link needs a
test on the side that can see both.*
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "src" / "web_streamlit" / "pages"
MAIN = ROOT / "mobile" / "lib" / "main.dart"


def _linked_url() -> str:
    match = re.search(r"const url = '(https://[^']+)'", MAIN.read_text())
    assert match, "main.dart no longer carries a help URL — update this guard with it"
    return match.group(1)


def test_the_help_link_names_a_page_that_exists():
    url = _linked_url()
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    # ⭐ Streamlit strips the numeric prefix and the extension: `7_Help.py` → `Help`.
    served = {re.sub(r"^\d+_", "", p.stem) for p in PAGES.glob("*.py")}
    assert slug in served, (
        f"the app links to /{slug}, and the web serves {sorted(served)}. "
        f"Renaming a page silently 404s the phone's Help row."
    )


def test_it_points_at_the_deployed_app_not_a_local_server():
    """⚠️ `localhost` here would work on this machine and nowhere else — the exact class of bug that kept
    the whole app on one Mac (ADR-239)."""
    url = _linked_url()
    assert url.startswith("https://"), f"help link is not https: {url}"
    assert "localhost" not in url and "127.0.0.1" not in url


def test_the_page_it_links_to_really_is_the_help_page():
    """⭐ Not just *a* page. ⚠️ A link to the right URL on a page that has become something else is worse
    than a broken link, because nothing reports it."""
    page = next(PAGES.glob("*_Help.py"))
    text = page.read_text()
    assert "st.title" in text
    # ⭐ Both halves the row promises: the written walkthrough **and** the videos.
    assert "Watch" in text and "Read" in text, (
        "the Help page no longer offers both reading and watching, but the app's row still says it does"
    )


def test_the_row_in_the_app_says_where_it_goes():
    """⚠️⚠️ **A row that leaves the app has to say so.** Tapping a list item and landing in Safari is a
    surprise unless it was announced — ⭐ *the surprise is the cost, not the browser.*"""
    more = (ROOT / "mobile" / "lib" / "more_view.dart").read_text()
    # ⚠️ **Comments may sit between the name and the description**, and the first version of this
    # pattern did not allow for them — so it reported *"the Help row is gone or renamed"* about a row
    # that was present and correct. ⭐ *A guard that fails for its own reasons teaches people to edit the
    # guard*, which is how a real one stops being trusted.
    block = re.search(
        r"name: 'Help[^']*',(?:\s*//[^\n]*\n)*\s*why:\s*((?:\s*'[^']*'\s*)+)", more)
    assert block, "the Help row is gone or renamed — update this guard with it"
    assert "madboots" in block.group(1), "the Help row does not say it opens the web app"
