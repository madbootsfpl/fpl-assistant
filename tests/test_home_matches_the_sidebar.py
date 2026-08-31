"""The Home page's "Explore the sidebar" list must match the actual sidebar.

Found 2026-08-31: it listed **Players · FDR · Team DNA · My Squad · Signals · Trending · Help · Feedback**
while the sidebar reads **My Squad · FDR · Signals · Team DNA · Players · Trending · Help · Feedback**. Four
of the eight were in the wrong place, and the first thing a new user reads was teaching a navigation that
does not exist.

The order is not cosmetic — ADR-166/169 ordered the sidebar by **how often you need it**, so a Home page in a
different sequence is not merely untidy, it contradicts a decision. And it drifted silently, which is the
species this project keeps paying for (ADR-168's unexercised narrated path, ADR-171's renamed tab, the
48-entry-stale ADR index). Hence a test rather than a careful edit.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "src" / "web_streamlit" / "Home.py"
PAGES = ROOT / "src" / "web_streamlit" / "pages"

# Owner-gated and not offered to users, so it is deliberately absent from the Home list (ADR-120).
_NOT_PUBLIC = {"Admin"}


def _sidebar_order():
    """The real sidebar: Streamlit orders `pages/` by the numeric filename prefix."""
    out = []
    for f in sorted(PAGES.glob("*.py")):
        m = re.match(r"(\d+)_(.+)\.py$", f.name)
        if m:
            name = m.group(2).replace("_", " ")
            if name not in _NOT_PUBLIC:
                out.append(name)
    return out


def _home_order():
    """The bullets under "Explore the sidebar", in the order a reader meets them."""
    body = HOME.read_text().split("**Explore the sidebar:**", 1)[1]
    # Stop at the next heading — the "Your squad" bullets below are steps, not pages, and swallowing them
    # made this test fail for the wrong reason the first time it ran.
    body = re.split(r"\n\*\*|\"\"\"", body, maxsplit=1)[0]
    return re.findall(r"^- \S+ \*\*(.+?)\*\*", body, re.M)


def test_home_lists_every_page_in_sidebar_order():
    assert _home_order() == _sidebar_order(), (
        "Home's 'Explore the sidebar' list is out of step with the sidebar.\n"
        f"  sidebar: {_sidebar_order()}\n"
        f"  home:    {_home_order()}\n"
        "The sidebar order is a decision (ADR-166/169 — ordered by how often you need it), so Home must "
        "follow it rather than teach a different nav."
    )


def test_home_does_not_advertise_the_owner_only_page():
    assert "Admin" not in _home_order(), "Admin is owner-gated (ADR-120) and must not be listed for users"
