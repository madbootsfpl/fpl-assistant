"""Help lives on madboots.com now, and the app's link reaches it (ADR-254, ADR-319).

⭐⭐ **Help goes out of the app; feedback stays in.** They look like one item and are two jobs. Help is
*content* — long, searchable, better on a big screen, and updatable without an App Store release.
Reporting happens the instant you notice something, and ⚠️ *every step between noticing and reporting
loses reports*, so that one keeps its two taps and the screen and build number it already sends for free.

⚠️⚠️ **What changed in ADR-319, and why this file changed with it.** The destination used to be
`madboots.streamlit.app/Help`, and the old version of this guard checked that a matching
`src/web_streamlit/pages/*.py` existed — because Streamlit derives URLs from filenames and a rename would
404 the phone silently. The destination is now a static page **in this repo**, so that whole class of risk
is gone and a different one takes its place: ⭐ *the page is generated, and nothing makes anyone run the
generator* — the same argument as `test_site_palette.py`, with the same mechanism.

⚠️ **The videos are deliberately not in the generated page.** They are rows in `maddie_videos` that the
owner edits from the Supabase dashboard, fetched at read time. Baking them in would turn "add a clip" into
"run a deploy", which is the opposite of what was asked for — so a test here pins that they stay out.
"""

from __future__ import annotations

import importlib.util
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
MAIN = ROOT / "mobile" / "lib" / "main.dart"
RELEASE = ROOT / "scripts" / "release_web.sh"


def generator():
    """`scripts/` is not a package, so load the real script from disk."""
    spec = importlib.util.spec_from_file_location(
        "gen_help", ROOT / "scripts" / "generate_help_page.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _linked_url() -> str:
    match = re.search(r"const url = '(https://[^']+)'", MAIN.read_text())
    assert match, "main.dart no longer carries a help URL — update this guard with it"
    return match.group(1)


# --- the page is current -------------------------------------------------------------------------

def test_the_page_carries_exactly_what_the_generator_writes() -> None:
    gen = generator()
    assert gen.render() == gen.OUT.read_text(), (
        "site/help.html is out of step with its sources. Run\n"
        "    venv/bin/python scripts/generate_help_page.py"
    )


def test_every_rule_ask_answers_from_is_on_the_page() -> None:
    """⭐ The page says *"the same ones Ask answers from, so they cannot drift apart"* — ⚠️ a claim that
    is only true while something checks it."""
    from src.fpl_rules import RULES

    page = (SITE / "help.html").read_text()
    for rule in RULES:
        title = rule["topic"].replace("_", " ").title()
        assert f"<summary>{title}</summary>" in page, (
            f"'{rule['topic']}' is a rule Ask can answer and the help page does not list it"
        )
    # ⭐ And the page's own count is not a number somebody typed.
    assert f">{len(RULES)} topics" in page or f"{len(RULES)} topics" in page


# --- the link reaches it -------------------------------------------------------------------------

def test_the_help_link_names_a_page_the_site_publishes() -> None:
    url = _linked_url()
    assert url.startswith("https://madboots.com/"), f"help no longer points at the site: {url}"
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    # ⭐ Cloudflare Pages serves `help.html` at `/help`; the file is what makes the URL real.
    assert (SITE / f"{slug}.html").exists(), (
        f"the app links to /{slug} and site/{slug}.html does not exist"
    )


def test_it_points_at_the_deployed_site_not_a_local_server() -> None:
    """⚠️ `localhost` here would work on this machine and nowhere else — the exact class of bug that kept
    the whole app on one Mac (ADR-239)."""
    url = _linked_url()
    assert url.startswith("https://")
    assert "localhost" not in url and "127.0.0.1" not in url


def test_the_release_publishes_the_page_and_everything_it_loads() -> None:
    """⚠️⚠️ **A page that is not copied is a 404 with a passing test suite.** `release_web.sh` once
    republished a landing page nine lines stale because only one script was named in a guard — ⭐ *the
    deploy step is part of the feature, so it is part of the test.*"""
    script = RELEASE.read_text()
    for asset in ("help.html", "help.css", "help.js"):
        assert asset in script, f"release_web.sh does not publish {asset}"
    assert "help-config.js" in script, (
        "release_web.sh does not write the video hub's address, so the videos never load in production"
    )


def test_the_app_no_longer_sends_anyone_to_streamlit() -> None:
    """⭐ The point of the move: *one help destination*, on the domain the product is named after."""
    for name in ("main.dart", "more_view.dart", "settings_view.dart"):
        text = (ROOT / "mobile" / "lib" / name).read_text()
        assert "streamlit" not in text.lower(), f"{name} still sends a reader to Streamlit"


def test_the_row_in_the_app_says_where_it_goes() -> None:
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
    assert "madboots" in block.group(1), "the Help row does not say it opens the web page"


# --- the videos stay data-driven -----------------------------------------------------------------

def test_the_page_it_links_to_really_is_the_help_page() -> None:
    """⭐ Not just *a* page. ⚠️ A link to the right URL on a page that has become something else is worse
    than a broken link, because nothing reports it."""
    page = (SITE / "help.html").read_text()
    assert 'id="start"' in page, "the walkthrough is gone but the app's row still promises it"
    assert 'id="videos"' in page, "the videos are gone but the app's row still promises them"


def test_the_clips_are_rows_not_markup() -> None:
    """⚠️⚠️ **The owner adds a video by editing a row, never by cutting a release.** ⭐ *A hard-coded clip
    would work on the day it was written and quietly become the reason nobody adds another.*"""
    page = (SITE / "help.html").read_text()
    assert "youtube" not in page.lower(), (
        "a video is baked into the generated page — it belongs in the maddie_videos table"
    )
    loader = (SITE / "help.js").read_text()
    assert "maddie_videos" in loader and "published=eq.true" in loader, (
        "help.js no longer reads the table the owner curates"
    )
    assert "order=sort_order" in loader, (
        "help.js does not honour sort_order, so the owner cannot reorder the clips"
    )


def test_the_committed_config_carries_no_credential() -> None:
    """⚠️⚠️ The key is publishable — `maddie_videos` is `SELECT`-only for `anon` (ADR-216) — but ⭐
    *"safe to publish" and "safe to commit" are different questions, and only one of them has an audit
    trail.* It arrives from the environment at deploy."""
    config = (SITE / "help-config.js").read_text()
    assert re.search(r"url:\s*''", config) and re.search(r"key:\s*''", config), (
        "site/help-config.js has a real store address in it — that belongs in release_web.sh's environment"
    )


def test_the_page_says_so_when_the_videos_cannot_load() -> None:
    """⭐ The Streamlit hub never raised, *so the hub always rendered*. Same promise here: ⚠️ a reader who
    sees an error concludes the product is broken, not that one table was unreachable."""
    loader = (SITE / "help.js").read_text()
    assert ".catch(" in loader, "help.js can leave the reader staring at 'Loading…' forever"
    assert "not configured" in loader, "help.js does not say anything when the store is absent"
