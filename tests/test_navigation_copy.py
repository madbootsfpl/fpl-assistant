"""The app's copy must describe the navigation the app actually has.

Started as a Home-page check and grew, because the same defect kept turning up somewhere new: Home, then the
Help guide, then four places in `squads.py`, a Radar caption, and three module docstrings. Copy that
describes the nav lives all over the app, so a guard on one file was only ever going to catch one file.

The original finding: Home listed **Players · FDR · Team DNA · My Squad · Signals · Trending · Help · Feedback**
while the sidebar reads **My Squad · FDR · Signals · Team DNA · Players · Trending · Help · Feedback**. Four
of the eight were in the wrong place, and the first thing a new user reads was teaching a navigation that
does not exist.

The order is not cosmetic — ADR-166/169 ordered the sidebar by **how often you need it**, so a Home page in a
different sequence is not merely untidy, it contradicts a decision. And it drifted silently, which is the
species this project keeps paying for (ADR-168's unexercised narrated path, ADR-171's renamed tab, the
48-entry-stale ADR index). Hence a test rather than a careful edit.
"""

import ast
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


def _my_squad_subtabs():
    """The real sub-tab names, read off the segmented control in the page source."""
    src = (PAGES / "1_My_Squad.py").read_text()
    m = re.search(r'"Tool",\s*\[(.*?)\]', src, re.S)
    assert m, "could not find the My Squad tool switch"
    return re.findall(r'"(.+?)"', m.group(1))


def test_home_only_points_at_sub_tabs_that_exist():
    """Home says things like "My Squad ▸ Lab" — every one must be a real tab.

    ADR-166 folded Squad Lab and Leagues in from the sidebar and ADR-171 folded AI Tips and Captain into the
    page itself, so the set of valid names has moved twice in a week. Home was still telling people to
    "manage transfers · captaincy · chips · analysis in My Squad" — a list of tabs, two of which no longer
    existed and one of which had been renamed.
    """
    named = set(re.findall(r"My Squad ▸ (\w+)", HOME.read_text()))
    real = set(_my_squad_subtabs())
    assert named <= real, (
        f"Home points at My Squad sub-tabs that do not exist: {sorted(named - real)}.\n"
        f"  real tabs: {sorted(real)}"
    )


# ---- Nothing in the app may point at navigation that is gone (2026-08-31) -------------------------
#
# Started as two Help-only checks and became a sweep, because the same sentence kept turning up somewhere
# new: Home, then Help, then three places in `squads.py` — including a panel that renders **on My Squad**
# while telling you to find the Lab "(sidebar)". Copy that describes the nav lives all over the app, so a
# guard on two files was only ever going to catch two files.

HELP = PAGES / "7_Help.py"
WEB = ROOT / "src" / "web_streamlit"

# Retired navigation, with what replaced it. Substring match on purpose — these are exact phrasings that
# shipped, not patterns, so a false positive means someone re-wrote a real mistake.
RETIRED = {
    "Squad Lab** tab": "the Lab is My Squad ▸ Lab (ADR-166), not a sidebar tab",
    "Build page": "there is no Build page — ADR-105 renamed it, ADR-166 folded it in",
    "My Squad → Health": "Health was renamed DNA (ADR-166/US-436)",
    "Team DNA & FDR": "split into two pages (ADR-169)",
    "the **Ask** tab": "Ask was retired (ADR-168)",
    "· Chips · ": "Chips is a section of My Squad, not a sub-tab (ADR-166/171)",
}


def _sources():
    """Every module that can put words on screen (the pages, and the view/helper modules they call)."""
    return sorted(WEB.rglob("*.py"))


def _visible_strings(path):
    """String literals that are **not** docstrings — i.e. the copy a user can actually read.

    The distinction matters and the first version of this test got it wrong. `2_FDR.py`'s docstring opens
    *"Split from the combined Team DNA & FDR page (ADR-169)"* — a correct, valuable statement about history,
    and flagging it would have pushed someone to delete the reasoning to make a test pass. Comments fall out
    for free (the parser drops them), and a docstring is a `Constant` that is the first statement of a
    module, class or function — so both kinds of prose-about-the-past are excluded, while every caption,
    help text, `st.markdown` and f-string fragment is still read.
    """
    tree = ast.parse(path.read_text())
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            first = next(iter(node.body), None)
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                    and isinstance(first.value.value, str):
                docstrings.add(id(first.value))
    return [n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docstrings]


def test_nothing_points_at_navigation_that_no_longer_exists():
    """The onboarding guide is the worst place for a stale tab name — but not the only one.

    Found 2026-08-31: Help said *"switch My Squad · AI Tips · Captain · Transfer · Chips · Health"* (four of
    six wrong) and gave a numbered step to **Ask**, retired two days earlier. `squads.py` told people to
    build in the **Squad Lab** tab *"(sidebar)"* — from a panel that renders on My Squad, three inches under
    the Lab tab itself — and to build "on the Build page", gone since ADR-105.
    """
    hits = []
    for f in _sources():
        copy = " ".join(_visible_strings(f))
        hits += [f"{f.relative_to(ROOT)}: {phrase!r} — {why}"
                 for phrase, why in RETIRED.items() if phrase in copy]
    assert not hits, "app copy points at navigation that no longer exists:\n  " + "\n  ".join(hits)


def test_every_my_squad_pointer_names_a_real_sub_tab():
    """`My Squad ▸ X` is the house form for pointing at a sub-tab — so every X must exist.

    The valid set moved twice in one week: ADR-166 folded Lab and Leagues in, ADR-171 folded AI Tips and
    Captain away. It is the reference most likely to rot next.
    """
    real = set(_my_squad_subtabs())
    bad = []
    for f in _sources():
        named = set(re.findall(r"My Squad ▸ (\w+)", " ".join(_visible_strings(f))))
        bad += [f"{f.relative_to(ROOT)}: {sorted(named - real)}" for _ in [0] if named - real]
    assert not bad, f"pointers at My Squad sub-tabs that do not exist (real: {sorted(real)}):\n  " + "\n  ".join(bad)
