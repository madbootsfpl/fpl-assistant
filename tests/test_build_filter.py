"""The Render build filter must cover everything the image is built from (ADR-292).

⭐⭐ **The failure mode is silence.** If the Dockerfile starts copying a directory the filter does not
list, Render stops redeploying when that directory changes — and the service keeps serving the old code
while the repo says otherwise. ⚠️ *A deploy filter that has drifted from the build is worse than no
filter, because no filter at least always deploys.*
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "03_Architecture" / "Hosting_The_API.md"


def _documented(heading: str) -> list[str]:
    """The fenced block that follows a bold **heading** in the runbook."""
    body = DOC.read_text()
    start = body.index(f"**{heading}**")
    block = re.search(r"```\n(.*?)```", body[start:], re.S)
    assert block, f"no fenced list under **{heading}**"
    return [line.strip() for line in block[1].splitlines() if line.strip()]


def _copied_by_dockerfile() -> set[str]:
    """Every source path the image copies in — ⭐ read from the build, not from memory."""
    sources = set()
    for line in (ROOT / "Dockerfile").read_text().splitlines():
        if line.startswith("COPY "):
            parts = line.split()[1:]
            sources.update(parts[:-1])  # the last token is the destination
    return sources


def test_the_filter_covers_everything_the_image_copies() -> None:
    included = _documented("Included Paths")

    for source in _copied_by_dockerfile():
        covered = any(
            source == pattern
            or (pattern.endswith("/**") and source.rstrip("/").startswith(pattern[:-3]))
            for pattern in included
        )
        assert covered, (
            f"the Dockerfile copies {source!r} and the build filter does not list it — "
            f"Render will stop redeploying when it changes"
        )


def test_the_files_that_decide_the_build_are_included() -> None:
    """⚠️ Neither is copied *into* the image, and both change what is.

    ⭐ *A filter that watches the payload and not the recipe misses the commit that changes the recipe.*
    """
    included = _documented("Included Paths")

    assert "Dockerfile" in included
    assert ".dockerignore" in included


def test_the_streamlit_app_is_ignored_because_the_image_excludes_it() -> None:
    """⭐ Not an optimisation — `.dockerignore` drops it, so it *cannot* affect the API."""
    assert "src/web_streamlit/" in (ROOT / ".dockerignore").read_text()
    assert "src/web_streamlit/**" in _documented("Ignored Paths")


def test_the_filter_does_not_include_things_the_image_never_sees() -> None:
    """⚠️ Every extra path is a redeploy for nothing — which is the whole point of the filter.

    ⭐ *A filter that lists the repo is a filter that has been quietly given up on.*
    """
    included = _documented("Included Paths")

    for never in ("mobile/", "docs/", "tests/", "site/", "scripts/"):
        assert not any(p.startswith(never) for p in included), (
            f"{never} is in the build filter and is not in the image"
        )
